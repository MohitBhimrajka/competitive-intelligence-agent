from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging
import io
import markdown
from xhtml2pdf import pisa

from services.database import db
from services.gemini_service import GeminiService

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

@router.get("/{competitor_id}/deep-research/download")
async def download_deep_research_pdf(competitor_id: str):
    """Downloads the deep research report as a PDF."""
    competitor = await db.get_competitor(competitor_id)
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    markdown_content = competitor.get("deep_research_markdown")
    status = competitor.get("deep_research_status")

    if status != "completed" or not markdown_content:
        raise HTTPException(status_code=404, detail=f"Deep research not completed or available for {competitor['name']}.")

    # Convert Markdown to HTML
    try:
        html_content = markdown.markdown(markdown_content, extensions=['extra', 'sane_lists'])
        # Basic CSS for better PDF readability
        html_with_style = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: sans-serif; line-height: 1.4; }}
                h1, h2, h3 {{ color: #333; }}
                code {{ background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px; }}
                pre {{ background-color: #f0f0f0; padding: 10px; border-radius: 5px; overflow-x: auto; }}
                li {{ margin-bottom: 5px; }}
            </style>
        </head>
        <body>
            <h1>Deep Research Report: {competitor['name']}</h1>
            {html_content}
        </body>
        </html>
        """
    except Exception as e:
         logger.error(f"Markdown conversion error: {e}")
         raise HTTPException(status_code=500, detail="Failed to convert report to HTML format.")

    # Convert HTML to PDF
    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.StringIO(html_with_style), dest=pdf_buffer)

    if pisa_status.err:
        logger.error(f"PDF generation error: {pisa_status.err}")
        raise HTTPException(status_code=500, detail="Failed to generate PDF report.")

    pdf_buffer.seek(0)

    # Create filename
    safe_filename = "".join(c for c in competitor['name'] if c.isalnum() or c in (' ', '_')).rstrip()
    filename = f"{safe_filename}_Deep_Research.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )

async def run_deep_research(competitor_id: str):
    """Background task to execute deep research and update DB."""
    try:
        competitor = await db.get_competitor(competitor_id)
        if not competitor:
            logger.error(f"[Deep Research Task] Competitor {competitor_id} not found.")
            return
        
        company_id = competitor.get("company_id")
        logger.info(f"[Deep Research Task] Starting for {competitor['name']} ({competitor_id})")
        markdown_report = await gemini_service.deep_research_competitor(
            competitor['name'],
            competitor.get('description')
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