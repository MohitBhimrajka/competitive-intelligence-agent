from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from typing import List, Optional, Dict, Any

from services.database import db
from services.gemini_service import GeminiService
from routers.news import fetch_and_store_competitor_news

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
gemini_service = GeminiService()

class InsightBase(BaseModel):
    content: str
    source: str = "ai-generated"

class InsightResponse(InsightBase):
    id: str
    company_id: str
    competitor_id: Optional[str] = None

class CompanyInsightsResponse(BaseModel):
    company_id: str
    company_name: str
    insights: List[InsightResponse]

@router.get("/company/{company_id}", response_model=CompanyInsightsResponse)
async def get_company_insights(company_id: str):
    """
    Get insights for a specific company.
    """
    try:
        # Get company info
        company = await db.get_company(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Get stored insights
        insights = await db.get_insights_by_company(company_id)
        
        # Generate insights if none exist
        if not insights:
            await generate_company_insights(company_id)
            insights = await db.get_insights_by_company(company_id)
        
        # Format the response
        insights_list = []
        for insight in insights:
            insights_list.append({
                "id": insight["id"],
                "company_id": insight["company_id"],
                "competitor_id": insight.get("competitor_id"),
                "content": insight["content"],
                "source": insight.get("source", "ai-generated")
            })
            
        return {
            "company_id": company_id,
            "company_name": company["name"],
            "insights": insights_list
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_company_insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/company/{company_id}/refresh", response_model=CompanyInsightsResponse)
async def refresh_company_insights(company_id: str):
    """
    Force refresh insights for a company.
    """
    try:
        # Get company info
        company = await db.get_company(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Generate new insights
        await generate_company_insights(company_id, force=True)
        
        # Get updated insights
        insights = await db.get_insights_by_company(company_id)
        
        # Format the response
        insights_list = []
        for insight in insights:
            insights_list.append({
                "id": insight["id"],
                "company_id": insight["company_id"],
                "competitor_id": insight.get("competitor_id"),
                "content": insight["content"],
                "source": insight.get("source", "ai-generated")
            })
            
        return {
            "company_id": company_id,
            "company_name": company["name"],
            "insights": insights_list
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in refresh_company_insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def generate_company_insights(company_id: str, force: bool = False):
    """
    Generate insights for a company based on competitors and news.
    """
    try:
        # Get company
        company = await db.get_company(company_id)
        if not company:
            logger.error(f"Company not found: {company_id}")
            return
        
        # Get competitors
        competitors = await db.get_competitors_by_company(company_id)
        if not competitors:
            logger.warning(f"No competitors found for company: {company['name']}")
            return
        
        # Prepare data for Gemini
        competitors_data = []
        news_data = {}
        
        for competitor in competitors:
            # Add competitor to the data
            competitors_data.append({
                "name": competitor["name"],
                "description": competitor["description"],
                "strengths": competitor["strengths"],
                "weaknesses": competitor["weaknesses"]
            })
            
            # Get news for this competitor
            news_articles = await db.get_news_by_competitor(competitor["id"])
            
            # If no news available, fetch it
            if not news_articles:
                await fetch_and_store_competitor_news(competitor["id"])
                news_articles = await db.get_news_by_competitor(competitor["id"])
            
            # Add news to the data
            if news_articles:
                news_data[competitor["name"]] = [
                    {
                        "title": article["title"],
                        "content": article["content"],
                        "source": article["source"],
                        "url": article["url"]
                    } 
                    for article in news_articles
                ]
        
        # Generate insights using Gemini
        insights_response = await gemini_service.generate_insights(
            company["name"],
            {"competitors": competitors_data},
            news_data
        )
        
        # Clear existing insights if forcing refresh
        if force:
            # In a real implementation, we would delete existing insights
            # Since we're using an in-memory DB, we can't easily do this,
            # so we'll just add new ones
            pass
        
        # Store insights
        for insight in insights_response.get("insights", []):
            await db.create_insight(
                company_id=company_id,
                content=f"{insight.get('title', 'Insight')}: {insight.get('description', '')}"
            )
            
        logger.info(f"Generated {len(insights_response.get('insights', []))} insights for company: {company['name']}")
            
    except Exception as e:
        logger.error(f"Error generating insights for company {company_id}: {e}") 