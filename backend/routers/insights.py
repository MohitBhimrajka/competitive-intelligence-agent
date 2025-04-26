from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from typing import List, Optional, Dict, Any
import asyncio  # Import asyncio

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
        
        # In a real DB, you would clear existing insights here.
        # For the in-memory DB, we'll simulate by just generating new ones,
        # which will appear alongside old ones.
        # Let's add a simple clear for the in-memory DB for demonstration.
        db.insights = {k: v for k, v in db.insights.items() if v.get('company_id') != company_id}
        logger.info(f"Cleared existing insights for {company['name']}.")
        
        # Generate new insights
        await generate_company_insights(company_id)
        
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
    Generate insights for a company based on competitors and news, fetching news concurrently if needed.
    """
    try:
        # Get company
        company = await db.get_company(company_id)
        if not company:
            logger.error(f"Company not found: {company_id} in background task")
            return
        
        # Get competitors
        competitors = await db.get_competitors_by_company(company_id)
        if not competitors:
            logger.warning(f"No competitors found for company: {company['name']} to generate insights from.")
            return

        # Identify which competitors need news fetching
        competitors_to_fetch_news = []
        for competitor in competitors:
            news_articles = await db.get_news_by_competitor(competitor["id"])
            if not news_articles:
                competitors_to_fetch_news.append(competitor["id"])

        # Fetch news concurrently for competitors that need it
        if competitors_to_fetch_news:
            logger.info(f"Fetching news concurrently for {len(competitors_to_fetch_news)} competitors for insight generation...")
            fetch_tasks = [fetch_and_store_competitor_news(comp_id) for comp_id in competitors_to_fetch_news]
            await asyncio.gather(*fetch_tasks)
            logger.info("Concurrent news fetching for insights completed.")
        else:
            logger.info("All competitors already have news stored, skipping news fetch for insights.")
        
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
            
            # Get all news for this competitor (whether new or old)
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
            else:
                # Include competitor in news_data even if no news found
                news_data[competitor["name"]] = []
        
        # Generate insights using Gemini
        logger.info(f"Generating insights for company: {company['name']}")
        insights_response = await gemini_service.generate_insights(
            company["name"],
            {"competitors": competitors_data},
            news_data
        )
        
        # Store insights
        stored_insights_count = 0
        for insight in insights_response.get("insights", []):
            await db.create_insight(
                company_id=company_id,
                content=f"{insight.get('title', 'Insight')}: {insight.get('description', '')}"
            )
            stored_insights_count += 1
            
        logger.info(f"Generated and stored {stored_insights_count} insights for company: {company['name']}")
            
    except Exception as e:
        logger.error(f"Error generating insights for company {company_id}: {e}") 