"""
Competitive Intelligence Agent - Full Workflow Test

This script tests the entire workflow of the competitive intelligence application:
1. Company analysis with welcome message
2. Competitor identification
3. News gathering for competitors
4. Insight generation

Usage:
    python test_workflow.py [company_name]

Example:
    python test_workflow.py "Microsoft"
"""

import os
import sys
import json
import asyncio
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
logger = logging.getLogger('test_workflow')

# Import services directly
from services.gemini_service import GeminiService
from services.news_service import NewsService
from services.database import db
from routers.news import fetch_and_store_competitor_news  # Import the function to parallelize

async def test_full_workflow(company_name: str):
    """Test the full workflow with a given company name."""
    print("\n" + "="*80)
    print(f"STARTING COMPETITIVE INTELLIGENCE WORKFLOW FOR: {company_name}")
    print("="*80 + "\n")

    # Initialize services
    gemini_service = GeminiService()
    news_service = NewsService()

    # STEP 1: Company Analysis
    print("\n" + "-"*40)
    print("STEP 1: COMPANY ANALYSIS")
    print("-"*40)
    
    try:
        print(f"Analyzing company: {company_name}")
        company_analysis = await gemini_service.analyze_company(company_name)
        
        print("\nCompany Analysis Results:")
        print(f"Description: {company_analysis.get('description', 'N/A')}")
        print(f"Industry: {company_analysis.get('industry', 'N/A')}")
        print(f"Welcome Message: {company_analysis.get('welcome_message', 'N/A')}")
        
        # Create company in database
        company = await db.create_company(
            name=company_name,
            description=company_analysis.get("description"),
            industry=company_analysis.get("industry"),
            welcome_message=company_analysis.get("welcome_message")  # Store welcome_message
        )
        print(f"\nCompany created in database with ID: {company['id']}")
        
    except Exception as e:
        logger.error(f"Error in company analysis: {e}")
        print(f"ERROR: {e}")
        sys.exit(1)

    # STEP 2: Competitor Identification
    print("\n" + "-"*40)
    print("STEP 2: COMPETITOR IDENTIFICATION")
    print("-"*40)
    
    try:
        print(f"Identifying competitors for {company_name}...")
        competitors_data = await gemini_service.identify_competitors(
            company["name"],
            company["description"] or "",
            company["industry"] or ""
        )
        
        print(f"\nIdentified {len(competitors_data.get('competitors', []))} competitors:")
        
        # Store competitors in database
        competitor_ids = {}
        competitor_list_for_insights = []  # Prepare structure for insights step
        for idx, competitor in enumerate(competitors_data.get("competitors", []), 1):
            print(f"\n{idx}. {competitor['name']}")
            print(f"   Description: {competitor.get('description', 'N/A')}")
            print("   Strengths:")
            for strength in competitor.get("strengths", []):
                print(f"    - {strength}")
            print("   Weaknesses:")
            for weakness in competitor.get("weaknesses", []):
                print(f"    - {weakness}")
                
            # Create competitor in database
            db_competitor = await db.create_competitor(
                name=competitor["name"],
                company_id=company["id"],
                description=competitor.get("description"),
                strengths=competitor.get("strengths"),
                weaknesses=competitor.get("weaknesses")
            )
            competitor_ids[competitor["name"]] = db_competitor["id"]
            competitor_list_for_insights.append(db_competitor)  # Add full db object
            
    except Exception as e:
        logger.error(f"Error in competitor identification: {e}")
        print(f"ERROR: {e}")
        sys.exit(1)

    # STEP 3: News Gathering (PARALLELIZED)
    print("\n" + "-"*40)
    print("STEP 3: NEWS GATHERING (PARALLELIZED)")
    print("-"*40)
    
    try:
        news_fetch_tasks = []
        competitor_names_to_fetch = []
        
        for competitor_name, competitor_id in competitor_ids.items():
            # Prepare a task to fetch and store news for this competitor
            news_fetch_tasks.append(fetch_and_store_competitor_news(competitor_id))
            competitor_names_to_fetch.append(competitor_name)
        
        if news_fetch_tasks:
            print(f"Fetching news concurrently for {len(news_fetch_tasks)} competitors...")
            # Run the tasks concurrently and wait for them to complete
            await asyncio.gather(*news_fetch_tasks)
            print("Concurrent news fetching completed.")
            
            # After fetching, retrieve all news from the DB to display
            all_news_for_insights = {}
            total_news_count = 0
            print("\nGathering fetched news:")
            
            for comp_name, comp_id in competitor_ids.items():
                news_articles = await db.get_news_by_competitor(comp_id)
                all_news_for_insights[comp_name] = news_articles  # Store raw articles for insights
                total_news_count += len(news_articles)
                
                print(f"\nFound {len(news_articles)} articles for {comp_name}")
                # Print a sample of articles (top 3)
                for i, article in enumerate(news_articles[:3], 1):
                    print(f"\n{i}. {article['title']}")
                    print(f"   Source: {article['source']}")
                    print(f"   URL: {article['url']}")
                    # Assuming published_at is string/iso format from DB/fetch
                    print(f"   Date: {article.get('published_at', 'N/A')}")
                    # Show a summary/preview
                    content_preview = article.get('content', 'No content').strip()
                    summary_preview = content_preview[:150] + "..." if len(content_preview) > 150 else content_preview
                    print(f"   Summary: {summary_preview}")
                    
            print(f"\nTotal news articles gathered across competitors: {total_news_count}")
        else:
            print("No competitors found to fetch news for.")
                
    except Exception as e:
        logger.error(f"Error in news gathering: {e}")
        print(f"ERROR: {e}")
        sys.exit(1)

    # STEP 4: Insight Generation
    print("\n" + "-"*40)
    print("STEP 4: INSIGHT GENERATION")
    print("-"*40)
    
    try:
        print(f"Generating insights for {company_name} based on competitor data and news...")
        
        # Prepare competitor data structure matching what generate_insights expects
        competitors_for_gemini = []
        for competitor in competitor_list_for_insights:
            competitors_for_gemini.append({
                "name": competitor["name"],
                "description": competitor["description"],
                "strengths": competitor["strengths"],
                "weaknesses": competitor["weaknesses"]
            })
        
        # Fetch news data from the database - the news is already stored in step 3
        news_data = {}
        for competitor_name, competitor_id in competitor_ids.items():
            news_articles = await db.get_news_by_competitor(competitor_id)
            if news_articles:
                news_data[competitor_name] = [
                    {
                        "title": article["title"],
                        "content": article["content"],
                        "source": article["source"],
                        "url": article["url"]
                    }
                    for article in news_articles
                ]
            else:
                news_data[competitor_name] = []
        
        insights_response = await gemini_service.generate_insights(
            company["name"],
            {"competitors": competitors_for_gemini},
            news_data
        )
        
        print(f"\nGenerated {len(insights_response.get('insights', []))} insights:")
        
        # Store insights in database
        for i, insight in enumerate(insights_response.get("insights", []), 1):
            print(f"\n{i}. {insight.get('title', 'Untitled Insight')}")
            print(f"   Type: {insight.get('type', 'N/A')}")
            print(f"   Description: {insight.get('description', 'N/A')}")
            print(f"   Related Competitors: {', '.join(insight.get('related_competitors', ['None']))}")
            
            # Store insight in database
            db_insight = await db.create_insight(
                company_id=company["id"],
                content=f"{insight.get('title', 'Insight')}: {insight.get('description', '')}"
            )
            
    except Exception as e:
        logger.error(f"Error in insight generation: {e}")
        print(f"ERROR: {e}")
        # Don't sys.exit here, still show the summary

    # Workflow Summary
    print("\n" + "="*80)
    print("WORKFLOW SUMMARY")
    print("="*80)
    
    print(f"\nCompany: {company['name']}")
    print(f"Industry: {company.get('industry', 'N/A')}")
    print(f"Competitors identified: {len(competitor_ids)}")
    
    # Calculate total news count from DB
    total_news = 0
    for comp_id in competitor_ids.values():
        total_news += len(await db.get_news_by_competitor(comp_id))
    print(f"News articles gathered: {total_news}")
    
    # Calculate total insights
    insights_count = len(await db.get_insights_by_company(company["id"]))
    print(f"Insights generated: {insights_count}")
    
    print("\nWorkflow completed successfully!")
    print("\nYou can now test the frontend by navigating to http://localhost:5173")
    print("\nAPI endpoints to test:")
    print(f"- Company details: GET /api/company/{company['id']}")
    print(f"- Competitors: GET /api/company/{company['id']}/competitors")
    print(f"- News: GET /api/news/company/{company['id']}")
    print(f"- Insights: GET /api/insights/company/{company['id']}")

async def main():
    """Main entry point for the script."""
    # Check for API keys
    if not os.getenv("GOOGLE_API_KEY"):
        print("ERROR: GOOGLE_API_KEY environment variable not set.")
        print("Please create a .env file with your API keys.")
        sys.exit(1)
    
    if not os.getenv("NEWS_API_KEY"):
        print("WARNING: NEWS_API_KEY environment variable not set.")
        print("News fetching will rely solely on Gemini's search capability.")
        # Don't exit, just warn
    
    # Get company name from command line argument or use default
    if len(sys.argv) > 1:
        company_name = sys.argv[1]
    else:
        company_name = input("Enter a company name to analyze: ")
    
    await test_full_workflow(company_name)

if __name__ == "__main__":
    asyncio.run(main()) 