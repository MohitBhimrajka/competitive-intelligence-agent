from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from typing import List, Optional, Dict

from services.database import db
from services.news_service import NewsService

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
news_service = NewsService()

class NewsArticleBase(BaseModel):
    title: str
    source: str
    url: str
    published_at: str
    content: str

class NewsArticleResponse(NewsArticleBase):
    id: str
    competitor_id: str

class CompetitorNewsResponse(BaseModel):
    competitor_id: str
    competitor_name: str
    articles: List[NewsArticleBase]

@router.get("/competitor/{competitor_id}", response_model=CompetitorNewsResponse)
async def get_competitor_news(competitor_id: str):
    """
    Get news articles for a specific competitor.
    """
    try:
        # Get competitor info
        competitor = await db.get_competitor(competitor_id)
        if not competitor:
            raise HTTPException(status_code=404, detail="Competitor not found")
        
        # Get stored news articles
        stored_articles = await db.get_news_by_competitor(competitor_id)
        
        # Fetch fresh news if we don't have any stored
        if not stored_articles:
            await fetch_and_store_competitor_news(competitor_id)
            stored_articles = await db.get_news_by_competitor(competitor_id)
        
        # Format the response
        articles = []
        for article in stored_articles:
            articles.append({
                "title": article["title"],
                "source": article["source"],
                "url": article["url"],
                "published_at": article["published_at"],
                "content": article["content"]
            })
            
        return {
            "competitor_id": competitor_id,
            "competitor_name": competitor["name"],
            "articles": articles
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_competitor_news: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/company/{company_id}", response_model=Dict[str, List[NewsArticleBase]])
async def get_company_competitors_news(company_id: str):
    """
    Get news for all competitors of a company.
    """
    try:
        # Get company
        company = await db.get_company(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Get all competitors for this company
        competitors = await db.get_competitors_by_company(company_id)
        if not competitors:
            return {}
        
        # Get news for each competitor
        result = {}
        for competitor in competitors:
            competitor_id = competitor["id"]
            
            # Get stored news
            news_articles = await db.get_news_by_competitor(competitor_id)
            
            # If no news stored, fetch new ones
            if not news_articles:
                await fetch_and_store_competitor_news(competitor_id)
                news_articles = await db.get_news_by_competitor(competitor_id)
            
            # Format articles
            articles = []
            for article in news_articles:
                articles.append({
                    "title": article["title"],
                    "source": article["source"],
                    "url": article["url"],
                    "published_at": article["published_at"],
                    "content": article["content"]
                })
                
            result[competitor["name"]] = articles
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_company_competitors_news: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def fetch_and_store_competitor_news(competitor_id: str):
    """
    Fetch and store news for a competitor.
    """
    try:
        competitor = await db.get_competitor(competitor_id)
        if not competitor:
            logger.error(f"Competitor not found: {competitor_id}")
            return
        
        # Fetch news from the NewsAPI
        articles = await news_service.get_competitor_news(competitor["name"])
        
        # Store articles in the database
        for article in articles:
            await db.create_news_article(
                competitor_id=competitor_id,
                title=article["title"],
                source=article["source"],
                url=article["url"],
                content=article["content"],
                published_at=article["published_at"]
            )
            
        logger.info(f"Stored {len(articles)} news articles for competitor: {competitor['name']}")
            
    except Exception as e:
        logger.error(f"Error fetching news for competitor {competitor_id}: {e}") 