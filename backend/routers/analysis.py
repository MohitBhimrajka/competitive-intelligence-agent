from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
from datetime import datetime
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from routers.documents import vector_store

router = APIRouter()

class AnalysisQuery(BaseModel):
    query: str
    competitor_id: int

class AnalysisResult(BaseModel):
    query: str
    answer: str
    sources: List[str]
    timestamp: datetime

# Template for the analysis prompt
ANALYSIS_PROMPT = PromptTemplate(
    template="""You are a competitive intelligence analyst. Analyze the following information about {competitor_name} and answer the query.
    
    Query: {query}
    
    Context: {context}
    
    Provide a detailed analysis focusing on:
    1. Key findings
    2. Strategic implications
    3. Potential impact
    4. Recommended actions
    
    Answer:""",
    input_variables=["competitor_name", "query", "context"]
)

@router.post("/query", response_model=AnalysisResult)
async def analyze_competitor(query_data: AnalysisQuery):
    if vector_store is None:
        raise HTTPException(status_code=400, detail="No documents have been processed yet")
    
    try:
        # Create the QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=ChatOpenAI(temperature=0),
            chain_type="stuff",
            retriever=vector_store.as_retriever(),
            chain_type_kwargs={"prompt": ANALYSIS_PROMPT}
        )
        
        # Get competitor name (in a real app, this would come from the database)
        competitor_name = "Competitor"  # Replace with actual competitor name
        
        # Execute the query
        result = qa_chain({"query": query_data.query, "competitor_name": competitor_name})
        
        # Get relevant sources
        docs = vector_store.similarity_search(query_data.query, k=3)
        sources = [doc.metadata.get("source", "Unknown") for doc in docs]
        
        return AnalysisResult(
            query=query_data.query,
            answer=result["result"],
            sources=sources,
            timestamp=datetime.utcnow()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trends/{competitor_id}")
async def get_competitor_trends(competitor_id: int):
    # This would typically analyze historical data and identify trends
    # For now, returning mock data
    return {
        "competitor_id": competitor_id,
        "trends": [
            {
                "metric": "Product Launches",
                "trend": "Increasing",
                "period": "Last 6 months",
                "details": "3 new product launches detected"
            },
            {
                "metric": "Pricing Changes",
                "trend": "Stable",
                "period": "Last 3 months",
                "details": "No significant pricing changes"
            }
        ]
    }

@router.get("/insights/{competitor_id}")
async def get_competitor_insights(competitor_id: int):
    # This would generate insights based on all available data
    # For now, returning mock data
    return {
        "competitor_id": competitor_id,
        "insights": [
            {
                "type": "Strategic",
                "description": "Expanding into new market segments",
                "confidence": "High",
                "evidence": ["Recent job postings", "Product roadmap leaks"]
            },
            {
                "type": "Financial",
                "description": "Increased R&D spending",
                "confidence": "Medium",
                "evidence": ["Quarterly reports", "Investor presentations"]
            }
        ]
    } 