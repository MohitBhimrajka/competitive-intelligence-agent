# backend/services/rag_service.py

import os
import logging
import faiss # Make sure faiss-cpu or faiss-gpu is installed
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI # Use Gemini Chat
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
import asyncio

# Corrected import path relative to where backend/main.py is run
from services.database import db

# Load environment variables from .env file in the backend directory (if present)
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
FAISS_INDEX_PATH = "./faiss_indexes" # Directory to save indexes relative to where main.py is run
EMBEDDING_MODEL_NAME = "models/embedding-001" # Google's embedding model
# Use a Gemini model for Chat - Flash is faster and cheaper, Pro is more powerful
LLM_MODEL_NAME = "gemini-2.0-flash-001"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Installation Note for FAISS:
# Using pip: `pip install faiss-cpu` (or `faiss-gpu` if you have CUDA setup).
# May require C++ build tools.
# Using conda: `conda install -c pytorch faiss-cpu` is often easier.

class RAGService:
    def __init__(self):
        """Initializes the RAG Service with Embeddings, LLM, and Text Splitter."""
        try:
            google_api_key = os.getenv("GOOGLE_API_KEY")
            if not google_api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment variables.")

            self.embeddings = GoogleGenerativeAIEmbeddings(
                model=EMBEDDING_MODEL_NAME,
                google_api_key=google_api_key
            )
            self.llm = ChatGoogleGenerativeAI(
                model=LLM_MODEL_NAME,
                google_api_key=google_api_key,
                temperature=0.3, # Adjust temperature as needed
                convert_system_message_to_human=True # Often helpful for Gemini
            )
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP,
                length_function=len,
            )
            if not os.path.exists(FAISS_INDEX_PATH):
                os.makedirs(FAISS_INDEX_PATH)
                logger.info(f"Created FAISS index directory: {FAISS_INDEX_PATH}")
            logger.info(f"RAG Service initialized with Embedding: {EMBEDDING_MODEL_NAME} and LLM: {LLM_MODEL_NAME}")

        except Exception as e:
            logger.error(f"Failed to initialize RAG Service: {e}", exc_info=True)
            raise

    def _get_index_path(self, company_id: str) -> str:
        """Generates the file path for a company's FAISS index."""
        # Ensure the path uses OS-independent separators
        return os.path.join(FAISS_INDEX_PATH, f"idx_{company_id}")

    async def _gather_documents_for_company(self, company_id: str) -> List[Document]:
        """Gathers all relevant text data for a company from the database."""
        documents = []
        logger.info(f"Gathering documents for company_id: {company_id}")

        # 1. Fetch Company Data
        company = await db.get_company(company_id)
        if not company:
            logger.warning(f"Company data not found for RAG indexing: {company_id}")
            return [] # Return empty list if company itself not found

        company_name = company.get("name", "Unknown Company")
        documents.append(Document(
            page_content=f"Company Information:\nName: {company_name}\nDescription: {company.get('description', 'N/A')}\nIndustry: {company.get('industry', 'N/A')}",
            metadata={"source": "company_info", "company_name": company_name}
        ))

        # 2. Fetch Competitors
        competitors = await db.get_competitors_by_company(company_id)
        logger.info(f"Found {len(competitors)} competitors for {company_name}")
        for comp in competitors:
            comp_name = comp.get("name", "Unknown Competitor")
            comp_text = (
                f"Competitor Information: {comp_name}\n"
                f"Description: {comp.get('description', 'N/A')}\n"
                f"Strengths: {'; '.join(comp.get('strengths', [])) or 'N/A'}\n"
                f"Weaknesses: {'; '.join(comp.get('weaknesses', [])) or 'N/A'}"
            )
            documents.append(Document(
                page_content=comp_text,
                metadata={"source": "competitor_info", "competitor_name": comp_name, "company_name": company_name}
            ))

            # 3. Include Deep Research (if available and completed)
            if comp.get('deep_research_status') == 'completed' and comp.get('deep_research_markdown'):
                logger.info(f"Adding completed deep research for {comp_name} to RAG documents.")
                # Add the competitor name header explicitly to the research content for context
                research_content = f"Deep Research Report for {comp_name}:\n\n{comp['deep_research_markdown']}"
                # Split potentially large markdown content
                research_chunks = self.text_splitter.split_text(research_content)
                for i, chunk in enumerate(research_chunks):
                    documents.append(Document(
                        page_content=chunk,
                        metadata={"source": "deep_research", "competitor_name": comp_name, "chunk": i, "company_name": company_name}
                    ))
            elif comp.get('deep_research_status') and comp.get('deep_research_status') != 'not_started':
                 logger.info(f"Skipping deep research for {comp_name} (Status: {comp.get('deep_research_status')})")


        # 4. Fetch News (All competitors)
        logger.info(f"Fetching news for {len(competitors)} competitors...")
        news_count = 0
        for comp in competitors:
            comp_id = comp['id']
            comp_name = comp.get("name", "Unknown Competitor")
            news_items = await db.get_news_by_competitor(comp_id)
            for item in news_items:
                news_text = (
                    f"News/Development concerning {comp_name}:\n"
                    f"Title: {item.get('title', 'N/A')}\n"
                    f"Source: {item.get('source', 'N/A')}\n"
                    f"Published: {item.get('published_at', 'N/A')}\n"
                    f"Content: {item.get('content', 'N/A')}"
                )
                documents.append(Document(
                    page_content=news_text,
                    metadata={"source": "news", "competitor_name": comp_name, "url": item.get('url'), "company_name": company_name}
                ))
                news_count += 1
        logger.info(f"Added {news_count} news items.")

        # 5. Fetch Insights
        insights = await db.get_insights_by_company(company_id)
        logger.info(f"Adding {len(insights)} insights.")
        for insight in insights:
            insight_text = f"Generated Strategic Insight:\n{insight.get('content', 'N/A')}"
            documents.append(Document(
                page_content=insight_text,
                metadata={"source": "insight", "company_name": company_name}
            ))

        logger.info(f"Total documents gathered for {company_name} before splitting: {len(documents)}")
        return documents

    async def update_rag_index(self, company_id: str):
        """Fetches all data for a company, chunks it, and updates/creates its FAISS RAG index."""
        try:
            # 1. Gather all documents
            documents = await self._gather_documents_for_company(company_id)

            if not documents:
                logger.warning(f"No documents found to index for company_id: {company_id}. Skipping index creation.")
                return

            # 2. Split documents into chunks
            split_docs = self.text_splitter.split_documents(documents)
            logger.info(f"Split documents into {len(split_docs)} chunks for RAG indexing (Company ID: {company_id}).")

            if not split_docs:
                 logger.error(f"Text splitting resulted in zero chunks for company_id: {company_id}. Cannot create index.")
                 return

            # 3. Create and save FAISS index
            index_path = self._get_index_path(company_id)
            logger.info(f"Creating FAISS index at: {index_path}")
            # Running CPU-bound embedding and FAISS creation in executor to avoid blocking event loop
            loop = asyncio.get_running_loop()
            vector_store = await loop.run_in_executor(
                 None, # Use default thread pool executor
                 FAISS.from_documents,
                 split_docs,
                 self.embeddings
            )
            # Saving is I/O bound but can be slow, also run in executor
            await loop.run_in_executor(
                 None,
                 vector_store.save_local,
                 index_path
            )
            logger.info(f"RAG index saved successfully to {index_path}")

        except Exception as e:
             # Log the exception with traceback
             logger.error(f"Error creating/saving FAISS index for {company_id}: {e}", exc_info=True)
             # Optionally, re-raise if you want the caller to handle it
             # raise

    async def ask_question(self, query: str, company_id: str) -> str:
        """Answers a question using the RAG index for the specified company."""
        index_path = self._get_index_path(company_id)

        # Check if index exists, attempt to build if not
        if not os.path.exists(index_path):
            logger.warning(f"RAG index not found at {index_path}. Attempting to build it now.")
            try:
                await self.update_rag_index(company_id)
                # Check again after attempting build
                if not os.path.exists(index_path):
                    logger.error(f"Failed to build RAG index for {company_id}. Cannot answer question.")
                    return "I apologize, but I don't have the necessary information indexed for this company yet. Please ensure the analysis has fully completed and try again shortly."
            except Exception as build_e:
                logger.error(f"Exception occurred while trying to build missing RAG index for {company_id}: {build_e}", exc_info=True)
                return "I encountered an error while trying to prepare the information needed to answer your question. Please try again later."

        try:
            # Load the index asynchronously (FAISS loading can involve I/O)
            logger.debug(f"Loading FAISS index from: {index_path}")
            loop = asyncio.get_running_loop()
            vector_store = await loop.run_in_executor(
                None,
                FAISS.load_local,
                index_path,
                self.embeddings,
                True # allow_dangerous_deserialization=True
            )
            retriever = vector_store.as_retriever(search_kwargs={"k": 5}) # Retrieve top 5 relevant chunks
            logger.debug(f"Retriever created for company {company_id}")

            # Define RAG prompt template
            template = """You are an AI assistant analyzing competitive intelligence data. Answer the following question based *only* on the provided context. If the context does not contain the answer, state that clearly. Do not make up information.

            Context:
            {context}

            Question: {question}

            Answer:"""
            prompt = ChatPromptTemplate.from_template(template)

            # Define how to format retrieved documents
            def format_docs(docs: List[Document]) -> str:
                return "\n\n".join(f"Source: {doc.metadata.get('source', 'N/A')}\nContent: {doc.page_content}" for doc in docs)

            # Define the RAG chain using LCEL
            rag_chain = (
                RunnableParallel(
                    {"context": retriever | format_docs, "question": RunnablePassthrough()}
                )
                | prompt
                | self.llm
                | StrOutputParser()
            )

            logger.info(f"Invoking RAG chain for company {company_id} with query: '{query[:50]}...'")
            answer = await rag_chain.ainvoke(query)
            logger.info(f"RAG chain invocation complete for company {company_id}.")
            return answer

        except Exception as e:
            logger.error(f"Error during RAG question answering for {company_id}: {e}", exc_info=True)
            return "Sorry, I encountered an internal error while trying to answer your question based on the available documents."

# Instantiate the service (can be imported and used)
try:
    rag_service = RAGService()
except Exception as e:
    # If RAG service fails to initialize (e.g., missing API key),
    # create a dummy service to prevent crashes elsewhere.
    logger.error("RAG Service failed to initialize. Using a dummy service.", exc_info=True)
    class DummyRAGService:
        async def update_rag_index(self, *args, **kwargs):
            logger.warning("DummyRAGService: update_rag_index called, but service is not initialized.")
        async def ask_question(self, *args, **kwargs):
            logger.warning("DummyRAGService: ask_question called, but service is not initialized.")
            return "RAG service is not available due to an initialization error."
    rag_service = DummyRAGService()