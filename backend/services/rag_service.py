import os
import logging
import faiss
from langchain_ollama import OllamaLLM
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from typing import List, Optional
from dotenv import load_dotenv

from backend.services.database import db # Fixed import path

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
FAISS_INDEX_PATH = "./faiss_indexes" # Directory to save indexes
EMBEDDING_MODEL_NAME = "models/embedding-001" # Google's embedding model
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
LLM_MODEL_NAME = "gemma3:12b" # Local Ollama model

class RAGService:
    def __init__(self):
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=EMBEDDING_MODEL_NAME,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        self.llm = OllamaLLM(model=LLM_MODEL_NAME, temperature=0.3)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
        )
        if not os.path.exists(FAISS_INDEX_PATH):
            os.makedirs(FAISS_INDEX_PATH)
        logger.info("RAG Service initialized.")

    def _get_index_path(self, company_id: str) -> str:
        """Generates the path for a company's FAISS index."""
        return os.path.join(FAISS_INDEX_PATH, f"idx_{company_id}")

    async def update_rag_index(self, company_id: str):
        """Fetches all data for a company and updates/creates its RAG index."""
        logger.info(f"Updating RAG index for company_id: {company_id}")
        documents = []

        # 1. Fetch Company Data
        company = await db.get_company(company_id)
        if not company:
            logger.error(f"Company not found for RAG indexing: {company_id}")
            return
        documents.append(Document(page_content=f"Company: {company['name']}\nDescription: {company.get('description', 'N/A')}\nIndustry: {company.get('industry', 'N/A')}", metadata={"source": "company_info"}))

        # 2. Fetch Competitors
        competitors = await db.get_competitors_by_company(company_id)
        for comp in competitors:
            comp_text = f"Competitor: {comp['name']}\nDescription: {comp.get('description', 'N/A')}\nStrengths: {'; '.join(comp.get('strengths', []))}\nWeaknesses: {'; '.join(comp.get('weaknesses', []))}"
            documents.append(Document(page_content=comp_text, metadata={"source": "competitor_info", "competitor_name": comp['name']}))
            # Include Deep Research if available
            if comp.get('deep_research_status') == 'completed' and comp.get('deep_research_markdown'):
                logger.info(f"Adding deep research for {comp['name']} to RAG index.")
                # Split potentially large markdown
                research_chunks = self.text_splitter.split_text(comp['deep_research_markdown'])
                for chunk in research_chunks:
                    documents.append(Document(page_content=f"Deep Research for {comp['name']}:\n{chunk}", metadata={"source": "deep_research", "competitor_name": comp['name']}))


        # 3. Fetch News (All competitors)
        for comp in competitors:
            comp_id = comp['id']
            comp_name = comp['name']
            news_items = await db.get_news_by_competitor(comp_id)
            for item in news_items:
                news_text = f"News/Development for {comp_name}:\nTitle: {item['title']}\nSource: {item['source']}\nPublished: {item.get('published_at', 'N/A')}\nContent: {item['content']}"
                documents.append(Document(page_content=news_text, metadata={"source": "news", "competitor_name": comp_name, "url": item.get('url')}))

        # 4. Fetch Insights
        insights = await db.get_insights_by_company(company_id)
        for insight in insights:
            insight_text = f"Generated Insight:\n{insight['content']}"
            documents.append(Document(page_content=insight_text, metadata={"source": "insight"}))

        if not documents:
            logger.warning(f"No documents found to index for company_id: {company_id}")
            return

        # Split documents if necessary (some are already split)
        split_docs = self.text_splitter.split_documents(documents)
        logger.info(f"Created {len(split_docs)} chunks for RAG indexing.")

        # Create and save FAISS index
        try:
            vector_store = FAISS.from_documents(split_docs, self.embeddings)
            index_path = self._get_index_path(company_id)
            vector_store.save_local(index_path)
            logger.info(f"RAG index saved successfully to {index_path}")
        except Exception as e:
             logger.error(f"Error creating/saving FAISS index for {company_id}: {e}")
             raise


    async def ask_question(self, query: str, company_id: str) -> str:
        """Answers a question using the RAG index for the company."""
        index_path = self._get_index_path(company_id)
        if not os.path.exists(index_path):
            # Optionally trigger indexing here if not found, or just return error
            logger.warning(f"RAG index not found for company_id: {company_id}. Trying to build it now.")
            await self.update_rag_index(company_id)
            if not os.path.exists(index_path):
                 return "I don't have enough information indexed for this company yet. Please try again shortly."

        try:
            # Load the index
            vector_store = FAISS.load_local(index_path, self.embeddings, allow_dangerous_deserialization=True) # Required for FAISS loading
            retriever = vector_store.as_retriever(search_kwargs={"k": 5}) # Retrieve top 5 chunks

            # Define RAG prompt
            template = """Answer the question based only on the following context:
            {context}

            Question: {question}
            """
            prompt = ChatPromptTemplate.from_template(template)

            # Define RAG chain
            rag_chain = (
                {"context": retriever, "question": RunnablePassthrough()}
                | prompt
                | self.llm
                | StrOutputParser()
            )

            logger.info(f"Invoking RAG chain for company {company_id} with query: {query}")
            answer = await rag_chain.ainvoke(query)
            return answer

        except Exception as e:
            logger.error(f"Error during RAG question answering for {company_id}: {e}")
            return "Sorry, I encountered an error while trying to answer your question."

# Instantiate the service (can be used globally or injected)
rag_service = RAGService() 