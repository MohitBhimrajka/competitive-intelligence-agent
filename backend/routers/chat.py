from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
import logging

from services.rag_service import rag_service # Import the instantiated service
from services.database import db

router = APIRouter()
logger = logging.getLogger(__name__)

class ChatQuery(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str

@router.post("/{company_id}", response_model=ChatResponse)
async def handle_chat_query(company_id: str, chat_query: ChatQuery):
    """Handles user queries using the RAG system."""
    if not chat_query.query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    
    # Check if company exists
    company = await db.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    try:
        answer = await rag_service.ask_question(chat_query.query, company_id)
        return ChatResponse(answer=answer)
    except Exception as e:
        logger.error(f"Error handling chat query for company {company_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process chat query: {str(e)}") 