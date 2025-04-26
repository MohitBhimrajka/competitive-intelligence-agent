from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import logging
import io
import os
import tempfile
import markdown

from services.database import db
from services.gemini_service import GeminiService
from services.pdf_service import pdf_service

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize Gemini Service
gemini_service = GeminiService()

class Competitor(BaseModel):
    id: int
    name: str
    website: str
    description: str
    created_at: datetime
    updated_at: datetime

class CompetitorCreate(BaseModel):
    name: str
    website: str
    description: str

class CompetitorResponse(BaseModel):
    id: str
    name: str
    company_id: str
    description: Optional[str] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None

class ResearchResponse(BaseModel):
    message: str
    competitor_id: str
    status: str

class MultiResearchRequest(BaseModel):
    competitor_ids: List[str]

class MultiResearchResponse(BaseModel):
    message: str
    competitor_ids: List[str]
    status: str

# Mock database
competitors_db = []
current_id = 1

@router.post("/", response_model=Competitor)
async def create_competitor(competitor: CompetitorCreate):
    global current_id
    new_competitor = Competitor(
        id=current_id,
        name=competitor.name,
        website=competitor.website,
        description=competitor.description,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    competitors_db.append(new_competitor)
    current_id += 1
    return new_competitor

@router.get("/", response_model=List[Competitor])
async def get_competitors():
    return competitors_db

@router.get("/{competitor_id}", response_model=Competitor)
async def get_competitor(competitor_id: int):
    competitor = next((c for c in competitors_db if c.id == competitor_id), None)
    if competitor is None:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return competitor

@router.put("/{competitor_id}", response_model=Competitor)
async def update_competitor(competitor_id: int, competitor: CompetitorCreate):
    index = next((i for i, c in enumerate(competitors_db) if c.id == competitor_id), None)
    if index is None:
        raise HTTPException(status_code=404, detail="Competitor not found")
    
    updated_competitor = Competitor(
        id=competitor_id,
        name=competitor.name,
        website=competitor.website,
        description=competitor.description,
        created_at=competitors_db[index].created_at,
        updated_at=datetime.utcnow()
    )
    competitors_db[index] = updated_competitor
    return updated_competitor

@router.delete("/{competitor_id}")
async def delete_competitor(competitor_id: int):
    index = next((i for i, c in enumerate(competitors_db) if c.id == competitor_id), None)
    if index is None:
        raise HTTPException(status_code=404, detail="Competitor not found")
    competitors_db.pop(index)
    return {"message": "Competitor deleted successfully"}

@router.post("/{competitor_id}/deep-research", response_model=ResearchResponse)
async def trigger_deep_research(competitor_id: str, background_tasks: BackgroundTasks):
    """Initiates deep competitor research in the background."""
    competitor = await db.get_competitor(competitor_id)
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    current_status = competitor.get("deep_research_status", "not_started")

    if current_status == "pending":
        return ResearchResponse(
            message="Deep research is already in progress.",
            competitor_id=competitor_id,
            status=current_status
        )

    # Update status to pending and start background task
    await db.update_competitor_research(competitor_id, markdown=None, status="pending")
    background_tasks.add_task(run_deep_research, competitor_id)

    return ResearchResponse(
        message="Deep research initiated.",
        competitor_id=competitor_id,
        status="pending"
    )

@router.post("/deep-research/multiple", response_model=MultiResearchResponse)
async def trigger_multiple_deep_research(request: MultiResearchRequest, background_tasks: BackgroundTasks):
    """Initiates deep research for multiple competitors in parallel."""
    if not request.competitor_ids:
        raise HTTPException(status_code=400, detail="No competitor IDs provided")
    
    # Check if all competitors exist
    invalid_ids = []
    pending_ids = []
    valid_ids = []
    
    for competitor_id in request.competitor_ids:
        competitor = await db.get_competitor(competitor_id)
        if not competitor:
            invalid_ids.append(competitor_id)
        elif competitor.get("deep_research_status") == "pending":
            pending_ids.append(competitor_id)
        else:
            valid_ids.append(competitor_id)
    
    if invalid_ids:
        raise HTTPException(
            status_code=404, 
            detail=f"Competitors not found: {', '.join(invalid_ids)}"
        )
    
    # Update status and start background tasks for valid competitors
    for competitor_id in valid_ids:
        await db.update_competitor_research(competitor_id, markdown=None, status="pending")
        background_tasks.add_task(run_deep_research, competitor_id)
    
    # Create appropriate message
    if pending_ids and valid_ids:
        message = f"Deep research initiated for {len(valid_ids)} competitors. {len(pending_ids)} were already in progress."
    elif pending_ids:
        message = f"All {len(pending_ids)} competitors already had research in progress."
    else:
        message = f"Deep research initiated for all {len(valid_ids)} competitors."
    
    return MultiResearchResponse(
        message=message,
        competitor_ids=request.competitor_ids,
        status="pending"
    )

@router.get("/{competitor_id}/deep-research/download")
async def download_deep_research_pdf(competitor_id: str):
    """Downloads the deep research report."""
    competitor = await db.get_competitor(competitor_id)
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    markdown_content = competitor.get("deep_research_markdown")
    status = competitor.get("deep_research_status")

    if status != "completed" or not markdown_content:
        raise HTTPException(status_code=404, detail=f"Deep research not completed or available for {competitor['name']}.")

    try:
        # Save markdown to temp file for processing
        temp_md = tempfile.NamedTemporaryFile(delete=False, suffix='.md')
        temp_md.write(markdown_content.encode('utf-8'))
        temp_md.close()
        
        # Generate HTML with professional styling
        title = f"Deep Research: {competitor['name']}"
        html_buffer = pdf_service.markdown_to_pdf(markdown_content, title)
        
        # Clean up temp file
        os.unlink(temp_md.name)
        
        # Create filename
        safe_filename = "".join(c for c in competitor['name'] if c.isalnum() or c in (' ', '_')).rstrip().replace(' ', '_')
        filename = f"{safe_filename}_Deep_Research.html"
        
        logger.info(f"HTML report generated successfully for competitor {competitor_id}")
        return HTMLResponse(
            content=html_buffer.read(),
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
    
    except Exception as e:
        logger.error(f"HTML report generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")

@router.post("/deep-research/multiple/download")
async def download_multiple_deep_research_pdf(request: MultiResearchRequest):
    """Downloads a combined research report for multiple competitors."""
    if not request.competitor_ids:
        raise HTTPException(status_code=400, detail="No competitor IDs provided")
    
    # Check if all competitors have completed research
    not_completed = []
    competitors_data = []
    company_name = None
    
    for competitor_id in request.competitor_ids:
        competitor = await db.get_competitor(competitor_id)
        if not competitor:
            raise HTTPException(status_code=404, detail=f"Competitor not found: {competitor_id}")
        
        status = competitor.get("deep_research_status")
        if status != "completed" or not competitor.get("deep_research_markdown"):
            not_completed.append(competitor['name'])
        else:
            competitors_data.append(competitor)
            
        # Get company name for the report title
        if not company_name and competitor.get("company_id"):
            company = await db.get_company(competitor.get("company_id"))
            if company:
                company_name = company.get("name")
    
    if not_completed:
        raise HTTPException(
            status_code=400, 
            detail=f"Research not completed for: {', '.join(not_completed)}"
        )
    
    if not competitors_data:
        raise HTTPException(status_code=404, detail="No completed research found")
    
    try:
        # Create temp markdown files for each competitor
        temp_files = []
        competitor_names = []
        
        for i, competitor in enumerate(competitors_data):
            temp_md = tempfile.NamedTemporaryFile(delete=False, suffix=f'_{i}.md')
            temp_md.write(competitor['deep_research_markdown'].encode('utf-8'))
            temp_md.close()
            temp_files.append(temp_md.name)
            competitor_names.append(competitor['name'])
        
        # Combine markdown files
        combined_markdown = pdf_service.combine_markdown_files(temp_files, competitor_names)
        
        # Generate title
        title = f"Competitive Intelligence: "
        if company_name:
            title += f"{company_name}"
        else:
            # Use first 2 competitor names if no company name
            if len(competitor_names) > 2:
                title += f"{competitor_names[0]}, {competitor_names[1]} & {len(competitor_names)-2} more"
            else:
                title += " & ".join(competitor_names)
        
        # Generate HTML
        html_buffer = pdf_service.markdown_to_pdf(combined_markdown, title)
        
        # Clean up temp files
        for temp_file in temp_files:
            os.unlink(temp_file)
        
        # Create filename
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '_')).rstrip().replace(' ', '_')
        filename = f"{safe_title}_Competitive_Intelligence.html"
        
        logger.info(f"Combined HTML report generated successfully for {len(competitors_data)} competitors")
        return HTMLResponse(
            content=html_buffer.read(),
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
    
    except Exception as e:
        # Clean up temp files in case of error
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass
                
        logger.error(f"Combined HTML report generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate combined report: {str(e)}")

async def run_deep_research(competitor_id: str):
    """Background task to execute deep research and update DB."""
    try:
        competitor = await db.get_competitor(competitor_id)
        if not competitor:
            logger.error(f"[Deep Research Task] Competitor {competitor_id} not found.")
            return
        
        company_id = competitor.get("company_id")
        
        # Get company name if available
        company_name = None
        if company_id:
            company = await db.get_company(company_id)
            if company:
                company_name = company.get("name")
                logger.info(f"[Deep Research Task] Research for {competitor['name']} initiated by company: {company_name}")
        
        logger.info(f"[Deep Research Task] Starting for {competitor['name']} ({competitor_id})")
        markdown_report = await gemini_service.deep_research_competitor(
            competitor['name'],
            competitor.get('description'),
            company_name
        )

        # Check if report generation resulted in an error message
        if markdown_report and markdown_report.strip().startswith("## Error"):
             await db.update_competitor_research(competitor_id, markdown=markdown_report, status="error")
             logger.error(f"[Deep Research Task] Failed for {competitor['name']} ({competitor_id})")
        else:
             await db.update_competitor_research(competitor_id, markdown=markdown_report, status="completed")
             logger.info(f"[Deep Research Task] Completed for {competitor['name']} ({competitor_id})")
             
             # Trigger RAG Index Update if RAG service exists
             try:
                 from services.rag_service import rag_service
                 if company_id:
                     logger.info(f"Triggering RAG index update for company {company_id} after deep research completion.")
                     await rag_service.update_rag_index(company_id)
             except ImportError:
                 logger.info("RAG service not available, skipping index update.")

    except Exception as e:
        logger.error(f"[Deep Research Task] Unhandled exception for {competitor_id}: {e}")
        # Attempt to update status to error in DB
        await db.update_competitor_research(competitor_id, markdown=f"## Error\n\nTask failed with exception: {e}", status="error") 