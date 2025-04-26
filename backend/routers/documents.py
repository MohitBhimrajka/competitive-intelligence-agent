from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List
from pydantic import BaseModel
from datetime import datetime
import os
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
import tempfile

router = APIRouter()

class Document(BaseModel):
    id: int
    competitor_id: int
    title: str
    file_path: str
    document_type: str
    created_at: datetime
    processed: bool

class DocumentCreate(BaseModel):
    competitor_id: int
    title: str
    document_type: str

# Mock database
documents_db = []
current_id = 1
vector_store = None

@router.post("/upload", response_model=Document)
async def upload_document(
    competitor_id: int,
    title: str,
    document_type: str,
    file: UploadFile = File(...)
):
    global current_id
    
    # Save the uploaded file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = temp_file.name

    # Create document record
    new_document = Document(
        id=current_id,
        competitor_id=competitor_id,
        title=title,
        file_path=temp_path,
        document_type=document_type,
        created_at=datetime.utcnow(),
        processed=False
    )
    
    documents_db.append(new_document)
    current_id += 1
    
    return new_document

@router.post("/process/{document_id}")
async def process_document(document_id: int):
    document = next((d for d in documents_db if d.id == document_id), None)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # Load and process the PDF
        loader = PyPDFLoader(document.file_path)
        pages = loader.load()
        
        # Split the text into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = text_splitter.split_documents(pages)
        
        # Create embeddings and store in vector database
        embeddings = OpenAIEmbeddings()
        global vector_store
        if vector_store is None:
            vector_store = FAISS.from_documents(chunks, embeddings)
        else:
            vector_store.add_documents(chunks)
        
        # Update document status
        document.processed = True
        return {"message": "Document processed successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[Document])
async def get_documents():
    return documents_db

@router.get("/{document_id}", response_model=Document)
async def get_document(document_id: int):
    document = next((d for d in documents_db if d.id == document_id), None)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

@router.delete("/{document_id}")
async def delete_document(document_id: int):
    document = next((d for d in documents_db if d.id == document_id), None)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Remove the file
    if os.path.exists(document.file_path):
        os.remove(document.file_path)
    
    # Remove from database
    documents_db.remove(document)
    return {"message": "Document deleted successfully"} 