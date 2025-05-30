# backend/test_deep_research.py
"""
Competitive Intelligence Agent - Deep Research Test Script

This script tests the deep research workflow for one or multiple competitors.

Usage:
    python test_deep_research.py [company_name]

Example:
    python test_deep_research.py "Salesforce"
"""

import os
import sys
import json
import time
import requests
import logging
import argparse
from dotenv import load_dotenv

# Ensure we load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_deep_research')

# API base URL
API_BASE_URL = "http://localhost:8000"

# --- Helper Functions (Mostly copied/adapted from test_api.py) ---

def test_health_check():
    """Test the health check endpoint."""
    print("\n" + "-"*40)
    print("Checking API Health...")
    print("-"*40)
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200 and response.json().get("status") == "healthy":
            print("API is healthy.")
            return True
        else:
            print(f"API health check failed: Status {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        print(f"ERROR checking API health: {e}")
        return False

def analyze_company(company_name: str):
    """Initiates company analysis and returns company_id."""
    print("\n" + "-"*40)
    print(f"Initiating Analysis for Company: {company_name}")
    print("-"*40)
    try:
        # Payload for registering a new company analysis
        payload = {"name": company_name}
        
        response = requests.post(f"{API_BASE_URL}/api/company", json=payload)
        print(f"Status code: {response.status_code}")
        
        if response.status_code not in (200, 201):
            print(f"Response text: {response.text}")
            return None
            
        data = response.json()
        company_id = data.get("id")
        print(f"Company created with ID: {company_id}")
        return company_id
    except Exception as e:
        logger.error(f"Error in company analysis: {e}")
        print(f"ERROR: {e}")
        return None

def wait_for_competitors(company_id, max_wait_minutes=5):
    """Polls until competitors are available."""
    print("\n" + "-"*40)
    print(f"Waiting for Competitors for Company ID: {company_id} (Max Wait: {max_wait_minutes} mins)")
    print("-"*40)
    start_time = time.time()
    max_wait_seconds = max_wait_minutes * 60
    poll_interval = 10 # Check every 10 seconds

    while time.time() - start_time < max_wait_seconds:
        try:
            response = requests.get(f"{API_BASE_URL}/api/company/{company_id}/competitors")
            if response.status_code == 200:
                competitors_data = response.json()
                competitors_list = competitors_data.get('competitors')
                # Check if the 'competitors' key exists and the list is not None or empty
                if isinstance(competitors_list, list) and len(competitors_list) > 0:
                    print(f"Found {len(competitors_list)} competitors.")
                    return competitors_list # Return just the list of competitors
                else:
                    print(f"Competitors list empty or not ready yet. Waiting... (Elapsed: {int(time.time() - start_time)}s)")
            elif response.status_code == 404:
                print(f"Company {company_id} not found (yet?). Waiting...")
            else:
                print(f"Polling failed: Status {response.status_code}. Waiting...")

            time.sleep(poll_interval)
        except Exception as e:
            logger.error(f"Error polling for competitors: {e}")
            print(f"ERROR polling: {e}")
            time.sleep(poll_interval)

    print(f"TIMEOUT: Competitors did not appear for {company_id} within {max_wait_minutes} minutes.")
    return None

def trigger_deep_research(competitor_id: str):
    """Triggers deep research for a specific competitor."""
    print("\n" + "-"*40)
    print(f"Triggering Deep Research for Competitor ID: {competitor_id}")
    print("-"*40)
    try:
        response = requests.post(f"{API_BASE_URL}/api/competitor/{competitor_id}/deep-research")
        print(f"Status code: {response.status_code}")
        if response.status_code != 200:
            print(f"Error response: {response.text}")
            return False
        data = response.json()
        print(f"Response: {data}")
        if data.get("status") == "pending" or "already in progress" in data.get("message", ""):
             print("Deep research trigger successful or already running.")
             return True
        else:
             print("Deep research trigger failed.")
             return False
    except Exception as e:
        logger.error(f"Error triggering deep research: {e}")
        print(f"ERROR: {e}")
        return False

def trigger_multiple_deep_research(competitor_ids: list):
    """Triggers deep research for multiple competitors at once."""
    print("\n" + "-"*40)
    print(f"Triggering Deep Research for {len(competitor_ids)} Competitors")
    print("-"*40)
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/competitor/deep-research/multiple", 
            json={"competitor_ids": competitor_ids}
        )
        print(f"Status code: {response.status_code}")
        if response.status_code != 200:
            print(f"Error response: {response.text}")
            return False
        data = response.json()
        print(f"Response: {data}")
        return True
    except Exception as e:
        logger.error(f"Error triggering multiple deep research: {e}")
        print(f"ERROR: {e}")
        return False

def check_deep_research_status(company_id: str, competitor_id: str, target_status: str = "completed", max_wait_minutes: int = 15):
    """Polls the competitors endpoint until the research status matches the target."""
    print("\n" + "-"*40)
    print(f"Polling Deep Research Status for {competitor_id} (Target: {target_status}, Max Wait: {max_wait_minutes} mins)")
    print("-"*40)
    start_time = time.time()
    max_wait_seconds = max_wait_minutes * 60
    poll_interval = 20 # Check less frequently for long tasks

    while time.time() - start_time < max_wait_seconds:
        try:
            response = requests.get(f"{API_BASE_URL}/api/company/{company_id}/competitors")
            if response.status_code == 200:
                competitors_data = response.json()
                target_competitor = next((c for c in competitors_data.get('competitors', []) if c['id'] == competitor_id), None)

                if target_competitor:
                    current_status = target_competitor.get("deep_research_status")
                    print(f"Polling... Current status for {competitor_id}: {current_status} (Elapsed: {int(time.time() - start_time)}s)")
                    if current_status == target_status:
                        print(f"Target status '{target_status}' reached!")
                        return target_competitor # Return competitor data with markdown
                    elif current_status == "error":
                        print(f"ERROR status reported for deep research: {competitor_id}")
                        print(f"Error Markdown: {target_competitor.get('deep_research_markdown', 'N/A')}")
                        return None # Indicate failure
                    # Continue polling if status is pending or not_started
                else:
                    print(f"ERROR: Competitor {competitor_id} not found in list during status check.")
                    return None # Competitor disappeared?

            else:
                print(f"Polling competitors endpoint failed: Status {response.status_code}")

            time.sleep(poll_interval)
        except Exception as e:
            logger.error(f"Error polling deep research status: {e}")
            print(f"ERROR polling: {e}")
            time.sleep(poll_interval)

    print(f"TIMEOUT: Deep research for {competitor_id} did not reach status '{target_status}' within {max_wait_minutes} minutes.")
    return None

def check_multiple_research_status(company_id: str, competitor_ids: list, target_status: str = "completed", max_wait_minutes: int = 20):
    """Polls the competitors endpoint until all research statuses match the target."""
    print("\n" + "-"*40)
    print(f"Polling Deep Research Status for {len(competitor_ids)} competitors (Target: {target_status}, Max Wait: {max_wait_minutes} mins)")
    print("-"*40)
    start_time = time.time()
    max_wait_seconds = max_wait_minutes * 60
    poll_interval = 30  # Check less frequently for multiple long tasks

    # Store the competitors that have reached completion
    completed_competitors = {}
    
    while time.time() - start_time < max_wait_seconds:
        try:
            response = requests.get(f"{API_BASE_URL}/api/company/{company_id}/competitors")
            if response.status_code == 200:
                competitors_data = response.json()
                all_competitors = competitors_data.get('competitors', [])
                
                # Filter to just our target competitors
                target_competitors = [c for c in all_competitors if c['id'] in competitor_ids]
                
                # Count statuses
                status_counts = {"completed": 0, "pending": 0, "error": 0, "not_started": 0}
                
                # Update our completed_competitors dict with any newly completed ones
                for competitor in target_competitors:
                    comp_id = competitor['id']
                    status = competitor.get("deep_research_status")
                    
                    # Count statuses
                    if status in status_counts:
                        status_counts[status] += 1
                    
                    # Store completed competitor data
                    if status == target_status and comp_id not in completed_competitors:
                        completed_competitors[comp_id] = competitor
                    
                    # Report errors
                    if status == "error" and comp_id not in completed_competitors:
                        print(f"ERROR status reported for {competitor['name']} ({comp_id})")
                        print(f"Error Markdown: {competitor.get('deep_research_markdown', 'N/A')[:200]}...")
                
                # Print status summary
                elapsed = int(time.time() - start_time)
                print(f"Polling... Status summary: {status_counts} (Elapsed: {elapsed}s)")
                
                # Check if all are completed
                if len(completed_competitors) == len(competitor_ids):
                    print(f"All {len(competitor_ids)} competitors have reached '{target_status}' status!")
                    return list(completed_competitors.values())
                
                # Check if any error statuses mean we should abort
                if status_counts["error"] > 0:
                    print(f"Some competitors have error status. Continuing to wait for others...")
                
            else:
                print(f"Polling competitors endpoint failed: Status {response.status_code}")

            time.sleep(poll_interval)
        except Exception as e:
            logger.error(f"Error polling multiple research status: {e}")
            print(f"ERROR polling: {e}")
            time.sleep(poll_interval)

    # If we get here, we timed out. Return what we have.
    print(f"TIMEOUT: Not all competitors reached '{target_status}' within {max_wait_minutes} minutes.")
    print(f"Completed: {len(completed_competitors)} of {len(competitor_ids)}")
    
    if completed_competitors:
        return list(completed_competitors.values())
    return None

def download_research_pdf(competitor_id: str, competitor_name: str):
    """Downloads the deep research PDF report and checks headers."""
    print("\n" + "-"*40)
    print(f"Attempting to Download Deep Research PDF for: {competitor_name} ({competitor_id})")
    print("-"*40)
    download_dir = "test_downloads" # Optional: Directory to save PDFs
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    try:
        response = requests.get(f"{API_BASE_URL}/api/competitor/{competitor_id}/deep-research/download", stream=True, timeout=60)
        print(f"Status code: {response.status_code}")
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        print(f"Headers: {response.headers}")
        content_type = response.headers.get('content-type')
        content_disp = response.headers.get('Content-Disposition')

        # Check for PDF content type
        if content_type == 'application/pdf' and content_disp:
            # Extract filename safely
            filename_part = content_disp.split('filename=')[-1]
            if filename_part:
                filename = filename_part.strip('"')
            else: # Fallback filename
                 safe_name = "".join(c for c in competitor_name if c.isalnum() or c in (' ', '_')).rstrip()
                 filename = f"{safe_name}_Deep_Research_Report.pdf" # Ensure .pdf

            save_path = os.path.join(download_dir, filename)
            print(f"Attempting to save PDF as: {save_path}")
            content_length = 0
            try:
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        content_length += len(chunk)
                if content_length > 100: # Basic check: is the PDF file reasonably sized?
                    print(f"Successfully saved PDF ({content_length} bytes): {save_path}")
                    return True
                else:
                    print(f"ERROR: Saved PDF file seems too small ({content_length} bytes). Check content.")
                    return False
            except Exception as save_err:
                logger.error(f"Error saving PDF file {save_path}: {save_err}")
                print(f"ERROR saving PDF: {save_err}")
                return False
        else:
            print("ERROR: Invalid headers received for PDF download.")
            print(f"Content-Type: {content_type}, Content-Disposition: {content_disp}")
            # Print response text if not PDF, might contain error details
            if content_type != 'application/pdf':
                 print(f"Response Text (first 500 chars): {response.text[:500]}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading PDF: {e}")
        print(f"ERROR downloading PDF: {e}")
        # Print response text if available on error
        if hasattr(e, 'response') and e.response is not None:
             print(f"Error Response Text (first 500 chars): {e.response.text[:500]}")
        return False
    except Exception as e: # Catch other potential errors
         logger.error(f"Unexpected error during PDF download: {e}")
         print(f"UNEXPECTED ERROR during PDF download: {e}")
         return False

def download_combined_research_pdf(competitor_ids: list, company_name: str):
    """Downloads the combined research PDF for multiple competitors."""
    print("\n" + "-"*40)
    print(f"Attempting to Download Combined Research PDF for {len(competitor_ids)} competitors")
    print("-"*40)
    download_dir = "test_downloads"
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/competitor/deep-research/multiple/download",
            json={"competitor_ids": competitor_ids},
            stream=True,
            timeout=60
        )
        print(f"Status code: {response.status_code}")
        response.raise_for_status()

        print(f"Headers: {response.headers}")
        content_type = response.headers.get('content-type')
        content_disp = response.headers.get('Content-Disposition')

        if content_type == 'application/pdf' and content_disp:
            # Extract filename safely
            filename_part = content_disp.split('filename=')[-1]
            if filename_part:
                filename = filename_part.strip('"')
            else: # Fallback filename
                 safe_name = "".join(c for c in company_name if c.isalnum() or c in (' ', '_')).rstrip()
                 filename = f"{safe_name}_Combined_Research_Report.pdf" # Ensure .pdf

            save_path = os.path.join(download_dir, filename)
            print(f"Attempting to save combined PDF as: {save_path}")
            content_length = 0
            try:
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        content_length += len(chunk)
                if content_length > 100: # Basic check
                    print(f"Successfully saved combined PDF ({content_length} bytes): {save_path}")
                    return True
                else:
                     print(f"ERROR: Saved combined PDF seems too small ({content_length} bytes). Check content.")
                     return False
            except Exception as save_err:
                logger.error(f"Error saving combined PDF file {save_path}: {save_err}")
                print(f"ERROR saving combined PDF: {save_err}")
                return False
        else:
            print("ERROR: Invalid headers received for combined PDF download.")
            print(f"Content-Type: {content_type}, Content-Disposition: {content_disp}")
            if content_type != 'application/pdf':
                 print(f"Response Text (first 500 chars): {response.text[:500]}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading combined PDF: {e}")
        print(f"ERROR downloading combined PDF: {e}")
        if hasattr(e, 'response') and e.response is not None:
             print(f"Error Response Text (first 500 chars): {e.response.text[:500]}")
        return False
    except Exception as e: # Catch other potential errors
         logger.error(f"Unexpected error during combined PDF download: {e}")
         print(f"UNEXPECTED ERROR during combined PDF download: {e}")
         return False

def download_combined_research_html(competitor_ids: list, company_name: str):
    """Downloads the combined research HTML for multiple competitors."""
    print("\n" + "-"*40)
    print(f"Attempting to Download Combined Research HTML for {len(competitor_ids)} competitors")
    print("-"*40)
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/competitor/deep-research/multiple/download", 
            json={"competitor_ids": competitor_ids},
            stream=True
        )
        print(f"Status code: {response.status_code}")

        if response.status_code == 200:
            print(f"Headers: {response.headers}")
            content_type = response.headers.get('content-type')
            content_disp = response.headers.get('Content-Disposition')

            if content_type == 'text/html' and content_disp:
                # Extract filename safely
                filename_part = content_disp.split('filename=')[-1]
                if filename_part:
                    filename = filename_part.strip('"')
                else: # Fallback filename
                     safe_name = "".join(c for c in company_name if c.isalnum() or c in (' ', '_')).rstrip()
                     filename = f"{safe_name}_Combined_Research_Report.html"

                print(f"Attempting to save combined HTML as: {filename}")
                try:
                    with open(filename, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"Successfully saved HTML: {filename}")
                    return True
                except Exception as save_err:
                    logger.error(f"Error saving combined HTML file {filename}: {save_err}")
                    print(f"ERROR saving HTML: {save_err}")
                    return False
            else:
                print("ERROR: Invalid headers received for HTML download.")
                print(f"Content-Type: {content_type}, Content-Disposition: {content_disp}")
                return False
        else:
            print(f"Error response during download: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error downloading combined HTML: {e}")
        print(f"ERROR downloading combined HTML: {e}")
        return False

# --- Main Test Workflow ---

def test_deep_research_flow(company_name: str):
    """Runs the test sequence for deep research."""

    print("\n" + "="*80)
    print(f"STARTING DEEP RESEARCH TEST FOR COMPANY: {company_name}")
    print("="*80 + "\n")

    # 1. Health Check
    if not test_health_check():
        print("API health check failed. Is the server running at {API_BASE_URL}?")
        sys.exit(1)

    # 2. Initiate Analysis & Get Company ID
    company_id = analyze_company(company_name)
    if not company_id:
        print("Failed to initiate company analysis or get ID.")
        sys.exit(1)

    # 3. Wait for Competitors
    # Give the initial background task time to identify competitors
    competitors_list = wait_for_competitors(company_id, max_wait_minutes=5)
    if not competitors_list:
        print("Failed to retrieve competitors.")
        sys.exit(1)
        
    # 4. Ask user whether to research a single competitor or multiple
    print("\nWould you like to research a single competitor or multiple competitors?")
    research_mode = ""
    while research_mode not in ["single", "multiple"]:
        research_mode = input("Enter 'single' or 'multiple': ").strip().lower()
        if research_mode not in ["single", "multiple"]:
            print("Invalid input. Please enter 'single' or 'multiple'.")
    
    multi_mode = (research_mode == "multiple")
    
    if multi_mode:
        print("Multi-competitor mode selected.")
    else:
        print("Single competitor mode selected.")

    # 5. Select Competitors
    if multi_mode:
        # For multi mode, allow selecting multiple competitors
        print("\nAvailable Competitors:")
        for idx, comp in enumerate(competitors_list):
            print(f"{idx + 1}. {comp['name']} (ID: {comp['id']})")

        selected_competitors = []
        while not selected_competitors:
            try:
                choices = input(f"Enter the numbers of competitors to research (comma-separated, e.g. '1,3,4') or press Enter for the first two: ")
                if not choices:
                    # Default to first two competitors if available
                    selected_competitors = competitors_list[:min(2, len(competitors_list))]
                    break
                    
                # Parse comma-separated choices
                choice_indices = [int(c.strip()) - 1 for c in choices.split(',')]
                
                # Validate all choices
                if all(0 <= idx < len(competitors_list) for idx in choice_indices):
                    selected_competitors = [competitors_list[idx] for idx in choice_indices]
                else:
                    print("One or more invalid choices. Please try again.")
            except ValueError:
                print("Invalid input format. Please enter numbers separated by commas.")
                
        if not selected_competitors:
            print("No valid competitors selected. Exiting.")
            sys.exit(1)
            
        # Extract IDs
        competitor_ids = [comp['id'] for comp in selected_competitors]
        competitor_names = [comp['name'] for comp in selected_competitors]
        
        print(f"\nSelected {len(competitor_ids)} competitors for research: {', '.join(competitor_names)}")
        
        # 6. Trigger Deep Research
        if not trigger_multiple_deep_research(competitor_ids):
            print(f"Failed to trigger deep research for competitors. Check server logs.")
            sys.exit(1)
            
        # 7. Wait for Completion
        completed_data = check_multiple_research_status(company_id, competitor_ids)

        if not completed_data:
            print(f"Deep research did not complete successfully for any competitors.")
            sys.exit(1) # Exit if nothing completed

        print("\n" + "-"*40)
        print(f"Deep Research Completed for {len(completed_data)} of {len(competitor_ids)} competitors!")
        print("-"*40)

        # Download individual PDFs
        download_success_count = 0
        for competitor in completed_data:
            markdown_content = competitor.get('deep_research_markdown')
            status = competitor.get('deep_research_status')
            # Only attempt download if status is completed and markdown exists
            if status == 'completed' and markdown_content and not markdown_content.strip().startswith("## Error"):
                print(f"\nMarkdown Content Snippet for {competitor['name']}:")
                print(markdown_content[:500] + "\n...")
                if download_research_pdf(competitor['id'], competitor['name']):
                     download_success_count += 1
            elif status == 'error':
                 print(f"\nSkipping download for {competitor['name']} due to error status.")
                 print(f"Error Markdown: {markdown_content[:300]}...")
            else:
                 print(f"\nSkipping download for {competitor['name']} (Status: {status}, Markdown Present: {bool(markdown_content)})")

        # Download combined PDF only if there were successful individual reports
        if download_success_count > 0:
            completed_ids = [comp['id'] for comp in completed_data if comp.get('deep_research_status') == 'completed' and comp.get('deep_research_markdown') and not comp.get('deep_research_markdown').strip().startswith("## Error")]
            if completed_ids:
                 download_combined_research_pdf(completed_ids, company_name)
            else:
                 print("\nNo successfully completed reports to combine for PDF download.")
        else:
            print("\nNo successful individual reports to generate a combined PDF.")
                
    else:
        # For single mode, allow selecting one competitor
        print("\nAvailable Competitors:")
        for idx, comp in enumerate(competitors_list):
            print(f"{idx + 1}. {comp['name']} (ID: {comp['id']})")
            
        selected_idx = -1
        while selected_idx < 0 or selected_idx >= len(competitors_list):
            try:
                choice = input(f"Enter the number of a competitor to research (1-{len(competitors_list)}) or press Enter for the first one: ")
                if not choice:
                    selected_idx = 0  # Default to first
                    break
                selected_idx = int(choice) - 1
                if selected_idx < 0 or selected_idx >= len(competitors_list):
                    print(f"Invalid choice. Please enter a number between 1 and {len(competitors_list)}.")
            except ValueError:
                print("Invalid input. Please enter a number.")
                
        competitor = competitors_list[selected_idx]
        competitor_id = competitor['id']
        competitor_name = competitor['name']
        
        print(f"\nSelected competitor for research: {competitor_name}")
        
        # 6. Trigger Deep Research
        if not trigger_deep_research(competitor_id):
            print(f"Failed to trigger deep research for {competitor_name}. Check server logs.")
            sys.exit(1)
            
        # 7. Wait for Completion
        completed_data = check_deep_research_status(company_id, competitor_id)

        if not completed_data:
            print(f"Deep research did not complete successfully for {competitor_name}.")
            sys.exit(1)

        print("\n" + "-"*40)
        print("Deep Research Completed!")
        print("-"*40)
        markdown_content = completed_data.get('deep_research_markdown')
        status = completed_data.get('deep_research_status')

        if status == 'completed' and markdown_content and not markdown_content.strip().startswith("## Error"):
            print("Markdown Content Snippet:")
            print(markdown_content[:1000] + "\n...")
            download_research_pdf(competitor_id, competitor_name)
        elif status == 'error':
            print(f"Research for {competitor_name} resulted in an error.")
            print(f"Error Markdown: {markdown_content[:500]}...")
        else:
             print(f"Research completed for {competitor_name} but content is missing or invalid (Status: {status}). Cannot download PDF.")

    print("\n" + "="*80)
    print("DEEP RESEARCH TEST COMPLETED")
    print("="*80 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test deep research functionality.')
    parser.add_argument('company_name', nargs='?', default='Microsoft', help='Company name to analyze')
    
    args = parser.parse_args()
    test_deep_research_flow(args.company_name)