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
import asyncio  # Import asyncio
import re  # Import regex

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
    """Initiates deep competitor research in the background for a single competitor."""
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

    # Update status to pending
    await db.update_competitor_research(competitor_id, markdown=None, status="pending")
    # Start background task using the single execution helper
    background_tasks.add_task(run_single_research_and_update, competitor_id)

    return ResearchResponse(
        message="Deep research initiated.",
        competitor_id=competitor_id,
        status="pending"
    )

@router.post("/deep-research/multiple", response_model=MultiResearchResponse)
async def trigger_multiple_deep_research(request: MultiResearchRequest, background_tasks: BackgroundTasks):
    """Initiates deep research for multiple competitors concurrently."""
    if not request.competitor_ids:
        raise HTTPException(status_code=400, detail="No competitor IDs provided")
    
    valid_ids = []
    pending_ids = []
    invalid_ids = []
    company_id_for_rag = None  # To store the company ID for the final RAG update
    
    for competitor_id in request.competitor_ids:
        competitor = await db.get_competitor(competitor_id)
        if not competitor:
            invalid_ids.append(competitor_id)
        else:
            # Store the company ID from the first valid competitor
            if company_id_for_rag is None and competitor.get("company_id"):
                company_id_for_rag = competitor.get("company_id")
                
            if competitor.get("deep_research_status") == "pending":
                pending_ids.append(competitor_id)
            else:
                valid_ids.append(competitor_id)  # Add to list of IDs to start research for
    
    if invalid_ids:
        raise HTTPException(
            status_code=404, 
            detail=f"Competitors not found: {', '.join(invalid_ids)}"
        )
    
    # Update status to pending ONLY for those we are about to start
    for competitor_id in valid_ids:
        await db.update_competitor_research(competitor_id, markdown=None, status="pending")
    
    # Start ONE background task to handle all valid IDs concurrently
    if valid_ids:
        background_tasks.add_task(run_multiple_deep_research_concurrently, valid_ids, company_id_for_rag)
        message_start = f"Deep research initiated concurrently for {len(valid_ids)} competitors."
    else:
        message_start = "No new research tasks initiated."
        
    if pending_ids:
        message_end = f" {len(pending_ids)} competitor(s) already had research in progress."
    else:
        message_end = ""
    
    return MultiResearchResponse(
        message=message_start + message_end,
        competitor_ids=request.competitor_ids,  # Return all requested IDs
        status="pending"  # Overall status is pending as tasks are running/queued
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
        # Provide more specific feedback if it's an error status
        detail_msg = f"Deep research not completed (status: {status}) or content unavailable for {competitor['name']}."
        if status == 'error':
            detail_msg = f"Deep research for {competitor['name']} resulted in an error. Cannot download report."
        raise HTTPException(status_code=404, detail=detail_msg)

    try:
        # Generate PDF directly
        title = f"Deep Research: {competitor['name']}"
        pdf_buffer = pdf_service.generate_single_report_pdf(markdown_content, title)
        
        # Create filename
        safe_filename = "".join(c for c in competitor['name'] if c.isalnum() or c in (' ', '_')).rstrip().replace(' ', '_')
        filename = f"{safe_filename}_Deep_Research.pdf"
        
        logger.info(f"PDF report generated successfully for competitor {competitor_id}")
        return StreamingResponse(
            pdf_buffer,
            media_type='application/pdf',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
    
    except Exception as e:
        logger.error(f"PDF report generation error for competitor {competitor_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF report: {str(e)}")

@router.post("/deep-research/multiple/download")
async def download_multiple_deep_research_pdf(request: MultiResearchRequest):
    """Downloads a combined research report for multiple competitors as a PDF."""
    if not request.competitor_ids:
        raise HTTPException(status_code=400, detail="No competitor IDs provided")
    
    # Check if all competitors have completed research
    not_completed_or_error = []
    completed_competitors_data = []
    company_name = "Company" # Default name
    first_company_id = None
    
    for competitor_id in request.competitor_ids:
        competitor = await db.get_competitor(competitor_id)
        if not competitor:
            raise HTTPException(status_code=404, detail=f"Competitor not found: {competitor_id}")
        
        # Store company ID and name from the first valid competitor
        if first_company_id is None and competitor.get("company_id"):
            first_company_id = competitor.get("company_id")
            company = await db.get_company(first_company_id)
            if company:
                company_name = company.get("name", "Company") # Use fetched name
                
        status = competitor.get("deep_research_status")
        markdown_content = competitor.get("deep_research_markdown")
        
        if status != "completed" or not markdown_content or markdown_content.strip().startswith("## Error"):
            status_info = f"status: {status}" if status != 'completed' else ("missing content" if not markdown_content else "error content")
            not_completed_or_error.append(f"{competitor['name']} ({status_info})")
        else:
            completed_competitors_data.append(competitor)
    
    if not completed_competitors_data:
        details = f"No completed research found for the requested competitors. Issues: {', '.join(not_completed_or_error)}" if not_completed_or_error else "No completed research found."
        raise HTTPException(status_code=404, detail=details)
    
    if not_completed_or_error:
        logger.warning(f"Generating combined report, but research is not ready for: {', '.join(not_completed_or_error)}")
    
    # Create temp markdown files for each competitor
    temp_files = []
    try:
        competitor_names = [comp['name'] for comp in completed_competitors_data]
        
        for competitor_data in completed_competitors_data:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.md', mode='w', encoding='utf-8') as temp_f:
                temp_f.write(competitor_data['deep_research_markdown'])
                temp_files.append(temp_f.name)
        
        # Generate title for inside the report (cover page etc.)
        report_internal_title = "Competitive Intelligence Report: "
        title_suffix = ", ".join(competitor_names[:2]) + (f" & {len(competitor_names)-2} more" if len(competitor_names) > 2 else "")
        if company_name != "Company": # Use fetched company name if available
            report_internal_title += f"{company_name} vs {title_suffix}"
        else:
            report_internal_title += title_suffix

        # --- Generate Filename ---
        current_date_str = datetime.now().strftime('%Y%m%d')
        # Sanitize company name for filename
        safe_company_name = re.sub(r'[^\w\-]+', '_', company_name) # Replace non-alphanumeric/- with _
        filename = f"{safe_company_name}_Multi_Competitor_Report_{current_date_str}.pdf"
        # --- End Filename Generation ---
        
        # Generate PDF from combined markdown using the internal title
        pdf_buffer = pdf_service.generate_combined_report_pdf(
            temp_files, 
            competitor_names, 
            title=report_internal_title # Title used *inside* the report
        )
        
        logger.info(f"Combined PDF report generated successfully for {len(completed_competitors_data)} competitors")
        return StreamingResponse(
            pdf_buffer,
            media_type='application/pdf',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'} # Use the new filename here
        )
    
    except Exception as e:
        logger.error(f"Combined PDF report generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate combined PDF report: {str(e)}")
    finally:
        # Clean up temp files
        for temp_file_path in temp_files:
            try:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    logger.debug(f"Cleaned up temporary file: {temp_file_path}")
            except Exception as unlink_e:
                logger.error(f"Error cleaning up temporary file {temp_file_path}: {unlink_e}")

# --- Helper function for single research execution and update ---
async def run_single_research_and_update(competitor_id: str) -> bool:
    """
    Executes deep research for ONE competitor, updates its status in DB.
    Returns True on success, False on failure. Does NOT trigger RAG update.
    """
    competitor = None
    markdown_report = None # Define outside try block
    status_to_set = "error" # Default to error unless successful
    success = False

    try:
        competitor = await db.get_competitor(competitor_id)
        if not competitor:
            logger.error(f"[Single Research Task] Competitor {competitor_id} not found.")
            markdown_report = "## Error\n\nCompetitor data not found in database."
            return False # Indicate failure early

        company_id = competitor.get("company_id")
        company_name = None
        if company_id:
            company = await db.get_company(company_id)
            if company:
                company_name = company.get("name")

        logger.info(f"[Single Research Task] Starting for {competitor['name']} ({competitor_id})")
        markdown_report = await gemini_service.deep_research_competitor(
            competitor['name'],
            competitor.get('description'),
            company_name
        )

        # --- MODIFIED STATUS CHECK ---
        if markdown_report and isinstance(markdown_report, str) and not markdown_report.strip().startswith("## Error") and not markdown_report.strip().startswith("## Warning") and len(markdown_report.strip()) > 100:
            status_to_set = "completed"
            success = True
            logger.info(f"[Single Research Task] Completed successfully for {competitor['name']} ({competitor_id})")
        else:
            # Handle specific error/warning cases or general failure
            if not markdown_report:
                 log_msg = "Received empty report."
                 markdown_report = "## Error\n\nReceived empty report from generation service."
            elif markdown_report.strip().startswith("## Error"):
                 log_msg = "Received error report."
                 # Keep markdown_report as is
            elif markdown_report.strip().startswith("## Warning"):
                 log_msg = "Received warning report."
                 # Keep markdown_report as is, but still mark status as error
            else:
                 log_msg = f"Received short or invalid report (length {len(markdown_report.strip()) if markdown_report else 0})."
                 markdown_report = f"## Error\n\nReceived short or invalid report.\n\n```\n{markdown_report[:500]}...\n```"

            logger.error(f"[Single Research Task] Failed for {competitor['name']} ({competitor_id}). Reason: {log_msg}")
            success = False
        # --- END MODIFICATION ---

    except Exception as e:
        logger.error(f"[Single Research Task] Unhandled exception for {competitor_id} ({competitor.get('name', 'N/A') if competitor else 'N/A'}): {e}", exc_info=True)
        markdown_report = f"## Error\n\nTask failed with unhandled exception: {e}"
        success = False
    finally:
        # Ensure status is updated even if exceptions occur
        if competitor_id: # Check if competitor_id was obtained
             await db.update_competitor_research(competitor_id, markdown=markdown_report, status=status_to_set)
             logger.info(f"[Single Research Task] DB status updated for {competitor_id} to '{status_to_set}'.")
        else:
             logger.error("[Single Research Task] Cannot update DB status, competitor_id not available.")

    return success # Return final success status

# --- NEW background task orchestrator ---
async def run_multiple_deep_research_concurrently(competitor_ids: List[str], company_id_for_rag: Optional[str]):
    """
    Runs deep research for multiple competitor IDs concurrently using asyncio.gather.
    Triggers RAG update once at the end.
    """
    if not competitor_ids:
        return

    logger.info(f"[Multi Research Task] Starting concurrent research for {len(competitor_ids)} competitors: {competitor_ids}")

    # Create a list of coroutine calls
    tasks = [run_single_research_and_update(comp_id) for comp_id in competitor_ids]

    # Run them concurrently and wait for all to complete
    # return_exceptions=True ensures that one failure doesn't stop others
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    success_count = 0
    failure_count = 0
    failed_ids = []
    for i, result in enumerate(results):
        comp_id = competitor_ids[i]
        if isinstance(result, Exception):
            failure_count += 1
            failed_ids.append(comp_id)
            logger.error(f"[Multi Research Task] Competitor {comp_id} failed with exception: {result}")
        elif result is False:  # Explicit False returned by our helper on failure
            failure_count += 1
            failed_ids.append(comp_id)
            # Logging already done in the helper function
        else:  # Result is True
            success_count += 1

    logger.info(f"[Multi Research Task] Finished concurrent research. Success: {success_count}, Failed: {failure_count}.")
    if failed_ids:
        logger.warning(f"[Multi Research Task] Failed competitor IDs: {failed_ids}")

    # Trigger RAG Index Update ONCE after all tasks are done
    if company_id_for_rag:
        try:
            from services.rag_service import rag_service
            logger.info(f"[Multi Research Task] Triggering RAG index update for company {company_id_for_rag} after batch research completion.")
            await rag_service.update_rag_index(company_id_for_rag)
            logger.info(f"[Multi Research Task] RAG index update triggered successfully for {company_id_for_rag}.")
        except ImportError:
            logger.info("[Multi Research Task] RAG service not available, skipping index update.")
        except Exception as rag_e:
            logger.error(f"[Multi Research Task] Error triggering RAG index update for company {company_id_for_rag}: {rag_e}", exc_info=True)
    else:
        logger.warning("[Multi Research Task] No company ID found for triggering RAG update.") 