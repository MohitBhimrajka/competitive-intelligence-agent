from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
from typing import Optional, List, Dict, Any
import uuid

from services.database import db
from services.gemini_service import GeminiService

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
gemini_service = GeminiService()

class CompanyRequest(BaseModel):
    name: str

# New response model for the initial POST call
class CompanyInitiateResponse(BaseModel):
    id: str
    name: str
    status: str
    message: str

# Updated response model for GET /company/{company_id}
class CompanyDetailsResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    industry: Optional[str] = None
    welcome_message: Optional[str] = None

class CompetitorResponse(BaseModel):
    id: str
    name: str
    company_id: str
    description: Optional[str] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    deep_research_status: Optional[str] = None
    deep_research_markdown: Optional[str] = None

class CompetitorsListResponse(BaseModel):
    company_id: str
    company_name: str
    competitors: List[CompetitorResponse]

@router.post("/", response_model=CompanyInitiateResponse)
async def analyze_company(company_request: CompanyRequest, background_tasks: BackgroundTasks):
    """
    Initiate analysis for a company. Returns ID immediately and starts background tasks.
    """
    try:
        # Check if we already have this company
        existing_company = await db.get_company_by_name(company_request.name)
        if existing_company:
            company_id = existing_company["id"]
            message = f"Analysis already initiated for {existing_company['name']}. Refreshing data."
            # Trigger the background task to refresh data
            background_tasks.add_task(process_company_data, company_id)
            
            return CompanyInitiateResponse(id=company_id, name=existing_company["name"], status="processing", message=message)
        
        # If company doesn't exist, create it with minimal info first
        # The detailed analysis happens in the background task
        new_company = await db.create_company(name=company_request.name)
        company_id = new_company["id"]
        message = f"Initiated analysis for {company_request.name}."
        
        # Kick off the background task to get details, competitors, news, insights
        background_tasks.add_task(process_company_data, company_id)
        
        return CompanyInitiateResponse(id=company_id, name=new_company["name"], status="processing", message=message)
        
    except Exception as e:
        logger.error(f"Error in analyze_company endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{company_id}", response_model=CompanyDetailsResponse)
async def get_company_details(company_id: str):
    """
    Get company details (name, description, industry, welcome message) by ID.
    """
    try:
        company = await db.get_company(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Return details including potentially generated welcome message
        return CompanyDetailsResponse(
            id=company["id"],
            name=company["name"],
            description=company.get("description"),
            industry=company.get("industry"),
            welcome_message=company.get("welcome_message")
        )
        
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
        company = await db.get_company(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        competitors = await db.get_competitors_by_company(company_id)
        
        competitor_list = []
        for competitor in competitors:
            competitor_list.append({
                "id": competitor["id"],
                "name": competitor["name"],
                "company_id": competitor["company_id"],
                "description": competitor.get("description"),
                "strengths": competitor.get("strengths", []),
                "weaknesses": competitor.get("weaknesses", []),
                "deep_research_status": competitor.get("deep_research_status"),
                "deep_research_markdown": competitor.get("deep_research_markdown")
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
    Background task to process company details, competitors, and news.
    Then triggers insight generation.
    """
    try:
        from routers.insights import generate_company_insights
        
        company = await db.get_company(company_id)
        if not company:
            logger.error(f"Company not found for ID: {company_id} in background task")
            return
        
        logger.info(f"Starting background data processing for {company['name']} (ID: {company_id})")
        
        # 1. Analyze company details (description, industry, welcome message)
        logger.info(f"Analyzing details for {company['name']}...")
        company_analysis = await gemini_service.analyze_company(company["name"], max_retries=1)
        await db.update_company(
            company_id=company_id,
            description=company_analysis.get("description"),
            industry=company_analysis.get("industry"),
            welcome_message=company_analysis.get("welcome_message")
        )
        
        # Re-fetch company object to ensure it has the updated details for competitor identification
        company = await db.get_company(company_id)
        if not company:
            logger.error(f"Company disappeared after update: {company_id}")
            return

        # 2. Identify competitors
        logger.info(f"Identifying competitors for {company['name']}...")
        competitors_data = await gemini_service.identify_competitors(company["name"])
        
        # Log the results clearly
        if not competitors_data or not competitors_data.get('competitors'):
            logger.warning(f"No competitors identified for {company['name']}. This may indicate an issue with the API response.")
        else:
            logger.info(f"Successfully identified {len(competitors_data.get('competitors', []))} competitors for {company['name']}")
        
        # 3. Store competitors in database
        logger.info(f"Storing {len(competitors_data.get('competitors', []))} competitors...")
        for competitor in competitors_data.get("competitors", []):
            # Check if competitor already exists for this company before creating
            existing_competitors = await db.get_competitors_by_company(company_id)
            if not any(c['name'].lower() == competitor['name'].lower() for c in existing_competitors):
                await db.create_competitor(
                    name=competitor["name"],
                    company_id=company_id,
                    description=competitor.get("description"),
                    strengths=competitor.get("strengths"),
                    weaknesses=competitor.get("weaknesses")
                )
            else:
                logger.info(f"Competitor {competitor['name']} already exists for {company['name']}, skipping creation.")

        # 4. Generate insights (handled by insights router)
        logger.info(f"Triggering insight generation for {company['name']}...")
        await generate_company_insights(company_id)
        
        # 5. Update RAG index with all data
        try:
            from services.rag_service import rag_service
            logger.info(f"Updating RAG index for {company['name']}...")
            await rag_service.update_rag_index(company_id)
        except ImportError:
            logger.info("RAG service not available, skipping index update.")

        logger.info(f"Completed processing company data for {company['name']}")

    except Exception as e:
        logger.error(f"Error in process_company_data background task for {company_id}: {e}")

async def refresh_company_data(company_id: str):
    """
    Background task to refresh company data (details, competitors, news, insights).
    Essentially re-runs the processing.
    """
    try:
        logger.info(f"Starting background data refresh for ID: {company_id}")
        await process_company_data(company_id)
        logger.info(f"Refreshed company data for ID: {company_id}")
    except Exception as e:
        logger.error(f"Error in refresh_company_data background task for {company_id}: {e}") 