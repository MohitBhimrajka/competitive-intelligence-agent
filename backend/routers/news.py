from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from typing import List, Optional, Dict
import asyncio  # Import asyncio

from services.database import db
from services.news_service import NewsService

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
news_service = NewsService()

class NewsArticleBase(BaseModel):
    title: str
    source: str
    url: Optional[str] = None
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
                "url": article.get("url"),
                "published_at": article.get("published_at", ""),
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
    Get news for all competitors of a company, fetching concurrently if needed.
    """
    try:
        # Get company
        company = await db.get_company(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Get all competitors for this company
        competitors = await db.get_competitors_by_company(company_id)
        if not competitors:
            logger.info(f"No competitors found for company: {company['name']} to fetch news for.")
            return {}

        # Prepare tasks for fetching and storing news concurrently for all competitors
        fetch_tasks = [fetch_and_store_competitor_news(comp["id"]) for comp in competitors]

        # Run tasks concurrently
        logger.info(f"Fetching news concurrently for {len(competitors)} competitors of {company['name']}...")
        await asyncio.gather(*fetch_tasks)
        logger.info("Concurrent news fetching completed.")

        # After fetching/storing, retrieve all news from the database
        result = {}
        for competitor in competitors:
            competitor_id = competitor["id"]
            news_articles = await db.get_news_by_competitor(competitor_id)

            # Format articles
            articles = []
            for article in news_articles:
                articles.append({
                    "title": article["title"],
                    "source": article["source"],
                    "url": article.get("url"),
                    "published_at": article.get("published_at", ""),
                    "content": article["content"]
                })

            result[competitor["name"]] = articles
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_company_competitors_news: {e}")
        # Log the validation error details if possible
        from fastapi.exceptions import ResponseValidationError
        if isinstance(e, ResponseValidationError):
            logger.error(f"Response validation error details: {e.errors()}")
        raise HTTPException(status_code=500, detail=str(e))

async def fetch_and_store_competitor_news(competitor_id: str):
    """
    Fetch and store news for a competitor if not already present.
    """
    try:
        # Check if news already exists for this competitor
        existing_news = await db.get_news_by_competitor(competitor_id)
        if existing_news:
            logger.info(f"News already exists for competitor {competitor_id}, skipping fetch.")
            return # News already exists, no need to fetch

        competitor = await db.get_competitor(competitor_id)
        if not competitor:
            logger.error(f"Competitor not found: {competitor_id} during news fetch.")
            return

        logger.info(f"Fetching news/developments for competitor: {competitor['name']} (ID: {competitor_id})")

        # Fetch news from the NewsAPI and developments from Gemini
        # get_competitor_news now returns a mix, let's rename the variable
        items = await news_service.get_competitor_news(competitor["name"])

        # Store items in the database
        stored_count = 0
        for item in items:
            await db.create_news_article(
                competitor_id=competitor_id,
                title=item["title"],
                source=item["source"],
                url=item.get("url"),
                content=item["content"],
                published_at=item.get("published_at", "")
            )
            stored_count += 1

        logger.info(f"Stored {stored_count} news/development items for competitor: {competitor['name']}")

    except Exception as e:
        logger.error(f"Error fetching or storing news for competitor {competitor_id}: {e}") 