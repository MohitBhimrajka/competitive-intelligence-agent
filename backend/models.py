from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class CompanyBase(BaseModel):
    name: str

class CompanyCreate(CompanyBase):
    pass

class Company(CompanyBase):
    id: str
    description: Optional[str] = None
    industry: Optional[str] = None
    welcome_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True

class CompetitorBase(BaseModel):
    name: str
    company_id: str

class CompetitorCreate(CompetitorBase):
    description: Optional[str] = None

class Competitor(CompetitorBase):
    id: str
    description: Optional[str] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True

class NewsArticle(BaseModel):
    id: str
    competitor_id: str
    title: str
    source: str
    url: str
    published_at: datetime
    summary: Optional[str] = None
    content: str

    class Config:
        from_attributes = True

class Insight(BaseModel):
    id: str
    company_id: str
    competitor_id: Optional[str] = None
    content: str
    source: str = "ai-generated"
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True

class CompanyResponse(BaseModel):
    company: Company
    message: str

class CompetitorsResponse(BaseModel):
    company: Company
    competitors: List[Competitor]

class NewsResponse(BaseModel):
    competitor: Competitor
    articles: List[NewsArticle]

class InsightsResponse(BaseModel):
    company: Company
    insights: List[Insight] 