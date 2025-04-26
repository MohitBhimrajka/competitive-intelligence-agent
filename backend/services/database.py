import uuid
from datetime import datetime
import logging
from typing import Dict, List, Optional, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory database (for simplicity)
class InMemoryDB:
    def __init__(self):
        self.companies = {}
        self.competitors = {}
        self.news_articles = {}
        self.insights = {}
        logger.info("In-memory database initialized")
    
    # Company operations
    async def create_company(self, name: str, description: Optional[str] = None, industry: Optional[str] = None) -> Dict[str, Any]:
        company_id = str(uuid.uuid4())
        company = {
            "id": company_id,
            "name": name,
            "description": description,
            "industry": industry,
            "created_at": datetime.now()
        }
        self.companies[company_id] = company
        logger.info(f"Created company: {name} (ID: {company_id})")
        return company
    
    async def get_company(self, company_id: str) -> Optional[Dict[str, Any]]:
        return self.companies.get(company_id)
    
    async def get_company_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        for company in self.companies.values():
            if company["name"].lower() == name.lower():
                return company
        return None
    
    # Competitor operations
    async def create_competitor(self, name: str, company_id: str, description: Optional[str] = None, 
                               strengths: Optional[List[str]] = None, weaknesses: Optional[List[str]] = None) -> Dict[str, Any]:
        competitor_id = str(uuid.uuid4())
        competitor = {
            "id": competitor_id,
            "name": name,
            "company_id": company_id,
            "description": description,
            "strengths": strengths or [],
            "weaknesses": weaknesses or [],
            "created_at": datetime.now()
        }
        self.competitors[competitor_id] = competitor
        logger.info(f"Created competitor: {name} (ID: {competitor_id})")
        return competitor
    
    async def get_competitor(self, competitor_id: str) -> Optional[Dict[str, Any]]:
        return self.competitors.get(competitor_id)
    
    async def get_competitors_by_company(self, company_id: str) -> List[Dict[str, Any]]:
        result = []
        for competitor in self.competitors.values():
            if competitor["company_id"] == company_id:
                result.append(competitor)
        return result
    
    # News article operations
    async def create_news_article(self, competitor_id: str, title: str, source: str, url: str, 
                                 content: str, published_at: Optional[str] = None) -> Dict[str, Any]:
        article_id = str(uuid.uuid4())
        article = {
            "id": article_id,
            "competitor_id": competitor_id,
            "title": title,
            "source": source,
            "url": url,
            "content": content,
            "published_at": published_at or datetime.now().isoformat(),
            "created_at": datetime.now()
        }
        self.news_articles[article_id] = article
        return article
    
    async def get_news_by_competitor(self, competitor_id: str) -> List[Dict[str, Any]]:
        result = []
        for article in self.news_articles.values():
            if article["competitor_id"] == competitor_id:
                result.append(article)
        return result
    
    # Insight operations
    async def create_insight(self, company_id: str, content: str, 
                            competitor_id: Optional[str] = None) -> Dict[str, Any]:
        insight_id = str(uuid.uuid4())
        insight = {
            "id": insight_id,
            "company_id": company_id,
            "competitor_id": competitor_id,
            "content": content,
            "created_at": datetime.now()
        }
        self.insights[insight_id] = insight
        return insight
    
    async def get_insights_by_company(self, company_id: str) -> List[Dict[str, Any]]:
        result = []
        for insight in self.insights.values():
            if insight["company_id"] == company_id:
                result.append(insight)
        return result

# Create a global database instance
db = InMemoryDB() 