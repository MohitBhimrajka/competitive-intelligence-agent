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
            industry=company_analysis.get("industry")
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
            
    except Exception as e:
        logger.error(f"Error in competitor identification: {e}")
        print(f"ERROR: {e}")
        sys.exit(1)

    # STEP 3: News Gathering
    print("\n" + "-"*40)
    print("STEP 3: NEWS GATHERING")
    print("-"*40)
    
    all_news = {}
    try:
        for competitor_name, competitor_id in competitor_ids.items():
            print(f"\nFetching news for {competitor_name}...")
            news_articles = await news_service.get_competitor_news(competitor_name, days_back=30)
            
            print(f"Found {len(news_articles)} articles for {competitor_name}")
            
            # Store a sample of articles
            all_news[competitor_name] = []
            for i, article in enumerate(news_articles[:3], 1):  # Only show top 3 articles
                print(f"\n{i}. {article['title']}")
                print(f"   Source: {article['source']}")
                print(f"   URL: {article['url']}")
                print(f"   Date: {article['published_at']}")
                print(f"   Summary: {article['content'][:150]}...")
                
                # Store article in database
                db_article = await db.create_news_article(
                    competitor_id=competitor_id,
                    title=article["title"],
                    source=article["source"],
                    url=article["url"],
                    content=article["content"],
                    published_at=article["published_at"]
                )
                
                all_news[competitor_name].append(article)
                
    except Exception as e:
        logger.error(f"Error in news gathering: {e}")
        print(f"ERROR: {e}")
        sys.exit(1)

    # STEP 4: Insight Generation
    print("\n" + "-"*40)
    print("STEP 4: INSIGHT GENERATION")
    print("-"*40)
    
    try:
        print(f"Generating insights for {company_name} based on competitor news...")
        
        # Prepare competitor data for insight generation
        competitor_list = []
        for competitor_name, competitor_id in competitor_ids.items():
            competitor = await db.get_competitor(competitor_id)
            if competitor:
                competitor_list.append({
                    "name": competitor["name"],
                    "description": competitor["description"],
                    "strengths": competitor["strengths"],
                    "weaknesses": competitor["weaknesses"]
                })
        
        insights_response = await gemini_service.generate_insights(
            company["name"],
            {"competitors": competitor_list},
            all_news
        )
        
        print(f"\nGenerated {len(insights_response.get('insights', []))} insights:")
        
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
        sys.exit(1)

    # Workflow Summary
    print("\n" + "="*80)
    print("WORKFLOW SUMMARY")
    print("="*80)
    
    print(f"\nCompany: {company['name']}")
    print(f"Industry: {company['industry']}")
    print(f"Competitors identified: {len(competitor_ids)}")
    
    total_news = sum(len(articles) for articles in all_news.values())
    print(f"News articles gathered: {total_news}")
    
    insights_count = len(insights_response.get('insights', []))
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
        print("ERROR: NEWS_API_KEY environment variable not set.")
        print("Please create a .env file with your API keys.")
        sys.exit(1)
    
    # Get company name from command line argument or use default
    if len(sys.argv) > 1:
        company_name = sys.argv[1]
    else:
        company_name = input("Enter a company name to analyze: ")
    
    await test_full_workflow(company_name)


if __name__ == "__main__":
    asyncio.run(main()) 