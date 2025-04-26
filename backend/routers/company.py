from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
from typing import Optional, List
import uuid

from services.database import db
from services.gemini_service import GeminiService

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
gemini_service = GeminiService()

class CompanyRequest(BaseModel):
    name: str

class CompanyResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    industry: Optional[str] = None
    welcome_message: str

class CompetitorResponse(BaseModel):
    id: str
    name: str
    company_id: str
    description: Optional[str] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None

class CompetitorsListResponse(BaseModel):
    company_id: str
    company_name: str
    competitors: List[CompetitorResponse]

@router.post("/", response_model=CompanyResponse)
async def analyze_company(company_request: CompanyRequest, background_tasks: BackgroundTasks):
    """
    Analyze a company and kick off the competitive intelligence workflow.
    """
    try:
        # Check if we already have this company
        existing_company = await db.get_company_by_name(company_request.name)
        if existing_company:
            # Get company information
            company_info = {
                "id": existing_company["id"],
                "name": existing_company["name"],
                "description": existing_company["description"],
                "industry": existing_company["industry"],
                "welcome_message": f"Welcome back! We're updating competitive intelligence for {existing_company['name']}."
            }
            
            # Trigger the background task to refresh data
            background_tasks.add_task(refresh_company_data, existing_company["id"])
            
            return company_info
        
        # If company doesn't exist, analyze it with Gemini
        company_analysis = await gemini_service.analyze_company(company_request.name)
        
        # Create new company in database
        new_company = await db.create_company(
            name=company_request.name,
            description=company_analysis.get("description"),
            industry=company_analysis.get("industry")
        )
        
        # Prepare response
        response = {
            "id": new_company["id"],
            "name": new_company["name"],
            "description": new_company["description"],
            "industry": new_company["industry"],
            "welcome_message": company_analysis.get("welcome_message", f"Welcome to your competitive intelligence dashboard for {company_request.name}!")
        }
        
        # Kick off the background task to get competitors and news
        background_tasks.add_task(process_company_data, new_company["id"])
        
        return response
        
    except Exception as e:
        logger.error(f"Error in analyze_company: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company_details(company_id: str):
    """
    Get company details by ID.
    """
    try:
        company = await db.get_company(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        return {
            "id": company["id"],
            "name": company["name"],
            "description": company["description"],
            "industry": company["industry"],
            "welcome_message": f"Welcome back to your competitive intelligence dashboard for {company['name']}!"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_company_details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{company_id}/competitors", response_model=CompetitorsListResponse)
async def get_company_competitors(company_id: str):
    """
    Get all competitors for a specific company.
    """
    try:
        # Get company
        company = await db.get_company(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Get competitors
        competitors = await db.get_competitors_by_company(company_id)
        
        # Format response
        competitor_list = []
        for competitor in competitors:
            competitor_list.append({
                "id": competitor["id"],
                "name": competitor["name"],
                "company_id": competitor["company_id"],
                "description": competitor.get("description"),
                "strengths": competitor.get("strengths", []),
                "weaknesses": competitor.get("weaknesses", [])
            })
        
        return {
            "company_id": company_id,
            "company_name": company["name"],
            "competitors": competitor_list
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_company_competitors: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_company_data(company_id: str):
    """
    Background task to process competitors and news for a company.
    """
    try:
        from routers.insights import generate_company_insights
        
        company = await db.get_company(company_id)
        if not company:
            logger.error(f"Company not found for ID: {company_id}")
            return
        
        # 1. Identify competitors
        competitors_data = await gemini_service.identify_competitors(
            company["name"],
            company["description"] or "",
            company["industry"] or ""
        )
        
        # 2. Store competitors in database
        for competitor in competitors_data.get("competitors", []):
            await db.create_competitor(
                name=competitor["name"],
                company_id=company_id,
                description=competitor.get("description"),
                strengths=competitor.get("strengths"),
                weaknesses=competitor.get("weaknesses")
            )
            
        # 3. Generate insights (handled by insights router)
        await generate_company_insights(company_id)
        
        logger.info(f"Completed processing company data for {company['name']}")
            
    except Exception as e:
        logger.error(f"Error in process_company_data background task: {e}")

async def refresh_company_data(company_id: str):
    """
    Background task to refresh company data.
    """
    try:
        # Just reuse the same process as for new companies
        await process_company_data(company_id)
        logger.info(f"Refreshed company data for ID: {company_id}")
            
    except Exception as e:
        logger.error(f"Error in refresh_company_data background task: {e}") 