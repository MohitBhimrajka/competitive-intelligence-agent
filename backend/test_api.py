"""
Competitive Intelligence Agent - API Test Script

This script tests the API endpoints of the competitive intelligence application,
simulating the flow that would happen from the frontend.

Usage:
    python test_api.py [company_name]

Example:
    python test_api.py "Apple"
"""

import os
import sys
import json
import time
import asyncio
import requests
import logging
from pprint import pprint
from dotenv import load_dotenv

# Ensure we load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_api')

# API base URL
API_BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint."""
    print("\n" + "-"*40)
    print("TESTING HEALTH CHECK ENDPOINT")
    print("-"*40)
    
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        return True
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        print(f"ERROR: {e}")
        return False

def analyze_company(company_name):
    """Test the company analysis endpoint."""
    print("\n" + "-"*40)
    print(f"TESTING COMPANY ANALYSIS: {company_name}")
    print("-"*40)
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/company",
            json={"name": company_name}
        )
        print(f"Status code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error response: {response.text}")
            return None
        
        company_data = response.json()
        print(f"Company ID: {company_data['id']}")
        print(f"Name: {company_data['name']}")
        print(f"Description: {company_data['description']}")
        print(f"Industry: {company_data['industry']}")
        print(f"Welcome Message: {company_data['welcome_message']}")
        
        return company_data
    except Exception as e:
        logger.error(f"Error in company analysis: {e}")
        print(f"ERROR: {e}")
        return None

def get_company_details(company_id):
    """Test the get company details endpoint."""
    print("\n" + "-"*40)
    print(f"TESTING GET COMPANY DETAILS: {company_id}")
    print("-"*40)
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/company/{company_id}")
        print(f"Status code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error response: {response.text}")
            return None
        
        company_data = response.json()
        print(f"Company ID: {company_data['id']}")
        print(f"Name: {company_data['name']}")
        print(f"Description: {company_data['description']}")
        print(f"Industry: {company_data['industry']}")
        print(f"Welcome Message: {company_data['welcome_message']}")
        
        return company_data
    except Exception as e:
        logger.error(f"Error getting company details: {e}")
        print(f"ERROR: {e}")
        return None

def get_company_competitors(company_id):
    """Test the get company competitors endpoint."""
    print("\n" + "-"*40)
    print(f"TESTING GET COMPANY COMPETITORS: {company_id}")
    print("-"*40)
    
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            response = requests.get(f"{API_BASE_URL}/api/company/{company_id}/competitors")
            print(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                competitors_data = response.json()
                print(f"Company ID: {competitors_data['company_id']}")
                print(f"Company Name: {competitors_data['company_name']}")
                print(f"Number of competitors: {len(competitors_data['competitors'])}")
                
                # Print competitor details
                for idx, competitor in enumerate(competitors_data['competitors'], 1):
                    print(f"\n{idx}. {competitor['name']}")
                    print(f"   ID: {competitor['id']}")
                    print(f"   Description: {competitor.get('description', 'N/A')}")
                    
                    if competitor.get('strengths'):
                        print("   Strengths:")
                        for strength in competitor['strengths']:
                            print(f"    - {strength}")
                            
                    if competitor.get('weaknesses'):
                        print("   Weaknesses:")
                        for weakness in competitor['weaknesses']:
                            print(f"    - {weakness}")
                
                return competitors_data
            elif response.status_code == 404:
                # Competitors might not be ready yet, retry after a delay
                print(f"Competitors not ready yet, retrying in 2 seconds... (Attempt {retry_count+1}/{max_retries})")
                time.sleep(2)
                retry_count += 1
            else:
                print(f"Error response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting company competitors: {e}")
            print(f"ERROR: {e}")
            return None
    
    print(f"Failed to get competitors after {max_retries} attempts")
    return None

def get_competitor_news(competitor_id):
    """Test the get competitor news endpoint."""
    print("\n" + "-"*40)
    print(f"TESTING GET COMPETITOR NEWS: {competitor_id}")
    print("-"*40)
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/news/competitor/{competitor_id}")
        print(f"Status code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error response: {response.text}")
            return None
        
        news_data = response.json()
        print(f"Competitor ID: {news_data['competitor_id']}")
        print(f"Competitor Name: {news_data['competitor_name']}")
        print(f"Number of articles: {len(news_data['articles'])}")
        
        # Print article details (just a few for brevity)
        for idx, article in enumerate(news_data['articles'][:3], 1):
            print(f"\n{idx}. {article['title']}")
            print(f"   Source: {article['source']}")
            print(f"   URL: {article['url']}")
            print(f"   Published: {article['published_at']}")
            content_preview = article['content'][:150] + "..." if len(article['content']) > 150 else article['content']
            print(f"   Content preview: {content_preview}")
        
        return news_data
    except Exception as e:
        logger.error(f"Error getting competitor news: {e}")
        print(f"ERROR: {e}")
        return None

def get_company_news(company_id):
    """Test the get company news endpoint."""
    print("\n" + "-"*40)
    print(f"TESTING GET COMPANY NEWS: {company_id}")
    print("-"*40)
    
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            response = requests.get(f"{API_BASE_URL}/api/news/company/{company_id}")
            print(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                news_data = response.json()
                
                if not news_data:
                    print("No news data available yet, retrying in 2 seconds...")
                    time.sleep(2)
                    retry_count += 1
                    continue
                
                print(f"Number of competitors with news: {len(news_data)}")
                
                # Print news by competitor
                for competitor_name, articles in news_data.items():
                    print(f"\nCompetitor: {competitor_name}")
                    print(f"Number of articles: {len(articles)}")
                    
                    # Print a sample of articles
                    for idx, article in enumerate(articles[:2], 1):
                        print(f"  {idx}. {article['title']}")
                        print(f"     Source: {article['source']}")
                        print(f"     URL: {article['url']}")
                
                return news_data
            elif response.status_code == 404:
                print(f"News not ready yet, retrying in 2 seconds... (Attempt {retry_count+1}/{max_retries})")
                time.sleep(2)
                retry_count += 1
            else:
                print(f"Error response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting company news: {e}")
            print(f"ERROR: {e}")
            return None
    
    print(f"Failed to get company news after {max_retries} attempts")
    return None

def get_company_insights(company_id):
    """Test the get company insights endpoint."""
    print("\n" + "-"*40)
    print(f"TESTING GET COMPANY INSIGHTS: {company_id}")
    print("-"*40)
    
    max_retries = 10
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            response = requests.get(f"{API_BASE_URL}/api/insights/company/{company_id}")
            print(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                insights_data = response.json()
                print(f"Company ID: {insights_data['company_id']}")
                print(f"Company Name: {insights_data['company_name']}")
                print(f"Number of insights: {len(insights_data['insights'])}")
                
                # Print insight details
                for idx, insight in enumerate(insights_data['insights'], 1):
                    print(f"\n{idx}. {insight['content']}")
                    print(f"   ID: {insight['id']}")
                    print(f"   Source: {insight['source']}")
                
                return insights_data
            elif response.status_code == 404 or len(response.json().get('insights', [])) == 0:
                # Insights might not be ready yet, retry after a delay
                print(f"Insights not ready yet, retrying in 3 seconds... (Attempt {retry_count+1}/{max_retries})")
                time.sleep(3)
                retry_count += 1
            else:
                print(f"Error response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting company insights: {e}")
            print(f"ERROR: {e}")
            retry_count += 1
            time.sleep(3)
    
    print(f"Failed to get insights after {max_retries} attempts")
    return None

def refresh_company_insights(company_id):
    """Test the refresh company insights endpoint."""
    print("\n" + "-"*40)
    print(f"TESTING REFRESH COMPANY INSIGHTS: {company_id}")
    print("-"*40)
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/insights/company/{company_id}/refresh")
        print(f"Status code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error response: {response.text}")
            return None
        
        insights_data = response.json()
        print(f"Company ID: {insights_data['company_id']}")
        print(f"Company Name: {insights_data['company_name']}")
        print(f"Number of insights: {len(insights_data['insights'])}")
        
        # We've already printed insights in the previous call
        print("Insights refreshed successfully")
        
        return insights_data
    except Exception as e:
        logger.error(f"Error refreshing company insights: {e}")
        print(f"ERROR: {e}")
        return None

def test_full_api_workflow(company_name):
    """Test the full API workflow."""
    print("\n" + "="*80)
    print(f"TESTING FULL API WORKFLOW FOR: {company_name}")
    print("="*80 + "\n")
    
    # Make sure the API is running
    if not test_health_check():
        print("API health check failed. Is the server running?")
        sys.exit(1)
    
    # Step 1: Analyze company
    company_data = analyze_company(company_name)
    if not company_data:
        print("Company analysis failed")
        sys.exit(1)
    
    company_id = company_data["id"]
    
    # Step 2: Get company details (just to verify)
    company_details = get_company_details(company_id)
    if not company_details:
        print("Failed to get company details")
        sys.exit(1)
    
    # Step 3: Get competitors (may need to wait for processing)
    print("\nWaiting for competitor identification (this may take a moment)...")
    time.sleep(3)  # Give some time for background processing
    
    competitors_data = get_company_competitors(company_id)
    if not competitors_data:
        print("Failed to get competitors")
        sys.exit(1)
    
    # Step 4: Get news for a competitor
    if competitors_data.get('competitors'):
        competitor_id = competitors_data['competitors'][0]['id']
        competitor_news = get_competitor_news(competitor_id)
        if not competitor_news:
            print(f"Failed to get news for competitor {competitor_id}")
    else:
        print("No competitors found to get news for")
    
    # Step 5: Get news for all competitors
    company_news = get_company_news(company_id)
    if not company_news:
        print("Failed to get company news")
        # Don't exit, try insights anyway
    
    # Step 6: Get insights
    print("\nWaiting for insight generation (this may take a few moments)...")
    time.sleep(5)  # Give more time for insights to be generated
    
    insights_data = get_company_insights(company_id)
    if not insights_data or len(insights_data.get('insights', [])) == 0:
        print("Failed to get insights or no insights available")
        # Try refreshing insights
        refresh_result = refresh_company_insights(company_id)
        if refresh_result and len(refresh_result.get('insights', [])) > 0:
            insights_data = refresh_result
        else:
            print("Failed to refresh insights")
    
    # Final summary
    print("\n" + "="*80)
    print("API WORKFLOW SUMMARY")
    print("="*80)
    
    print(f"\nCompany: {company_name}")
    print(f"Company ID: {company_id}")
    
    competitors_count = len(competitors_data.get('competitors', [])) if competitors_data else 0
    print(f"Competitors identified: {competitors_count}")
    
    insights_count = len(insights_data.get('insights', [])) if insights_data else 0
    print(f"Insights generated: {insights_count}")
    
    print("\nAPI workflow test completed")
    print("\nFrontend can now use these endpoints:")
    print(f"- Company details: GET /api/company/{company_id}")
    print(f"- Competitors: GET /api/company/{company_id}/competitors")
    print(f"- News: GET /api/news/company/{company_id}")
    print(f"- Insights: GET /api/insights/company/{company_id}")
    
    # Print the exact URL to test in the browser
    print("\nTry these URLs in your browser:")
    print(f"{API_BASE_URL}/api/company/{company_id}")
    print(f"{API_BASE_URL}/api/company/{company_id}/competitors")
    print(f"{API_BASE_URL}/api/news/company/{company_id}")
    print(f"{API_BASE_URL}/api/insights/company/{company_id}")

def main():
    """Main entry point for the script."""
    # Check if API is accessible
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code != 200:
            print(f"ERROR: API at {API_BASE_URL} is not accessible or not healthy")
            print("Start the FastAPI server first with: cd backend && python -m uvicorn main:app --reload")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Cannot connect to API at {API_BASE_URL}")
        print("Start the FastAPI server first with: cd backend && python -m uvicorn main:app --reload")
        sys.exit(1)
    
    # Get company name from command line argument or use default
    if len(sys.argv) > 1:
        company_name = sys.argv[1]
    else:
        company_name = input("Enter a company name to analyze: ")
    
    test_full_api_workflow(company_name)


if __name__ == "__main__":
    main() 