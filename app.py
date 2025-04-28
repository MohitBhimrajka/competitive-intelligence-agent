import streamlit as st
import requests
import pandas as pd
import time
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import base64
import io
from PIL import Image
import re

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="Competitive Intelligence Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f1f3f6;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4e8df5;
        color: white;
    }
    .competitor-card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .insight-card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .metrics-container {
        display: flex;
        justify-content: space-between;
        margin-bottom: 20px;
    }
    .metric-item {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        flex: 1;
        margin: 0 10px;
        text-align: center;
    }
    .news-card {
        background-color: white;
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .news-source {
        font-size: 12px;
        color: #666;
    }
    .news-title {
        font-weight: bold;
    }
    .news-date {
        font-size: 12px;
        color: #666;
    }
    .tab-subheader {
        font-size: 1.25rem;
        font-weight: 600;
        margin-top: 1rem;
        margin-bottom: 1rem;
        color: #333;
    }
    </style>
""", unsafe_allow_html=True)

# Helper Functions
def check_api_health():
    """Check if the API is running and healthy."""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        return response.status_code == 200 and response.json().get("status") == "healthy"
    except:
        return False

def initialize_company_analysis(company_name):
    """Start analysis for a company and return the ID."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/company",
            json={"name": company_name}
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error initiating analysis: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        return None

def get_company_details(company_id):
    """Get detailed information about a company."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/company/{company_id}")
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None

def get_company_competitors(company_id):
    """Get competitors for a company."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/company/{company_id}/competitors")
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None

def get_company_news(company_id):
    """Get news articles for a company and its competitors."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/news/company/{company_id}")
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None

def get_company_insights(company_id):
    """Get insights for a company."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/insights/company/{company_id}")
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None

def refresh_company_insights(company_id):
    """Refresh insights for a company."""
    try:
        response = requests.post(f"{API_BASE_URL}/api/insights/company/{company_id}/refresh")
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None

def ask_rag_question(company_id, query):
    """Ask a question to the RAG system."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/chat/{company_id}",
            json={"query": query},
            timeout=60
        )
        if response.status_code == 200:
            return response.json().get("answer")
        elif response.status_code == 500:
            # Check if the error is related to the RAG index being built
            error_text = response.json().get("detail", "").lower()
            if "index" in error_text and "built" in error_text:
                return "The RAG index is still being built. Please try again in a moment."
            else:
                return f"Error: {response.json().get('detail', 'Unknown server error')}"
        else:
            return f"Error: {response.text}"
    except requests.exceptions.Timeout:
        return "The request timed out. The server might be processing a lot of data. Please try again later."
    except requests.exceptions.ConnectionError:
        return "Connection error. Please ensure the backend server is running."
    except Exception as e:
        return f"Error: {str(e)}"

def trigger_deep_research(competitor_id):
    """Trigger deep research for a competitor."""
    try:
        response = requests.post(f"{API_BASE_URL}/api/competitor/{competitor_id}/deep-research")
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None

def trigger_multiple_deep_research(competitor_ids):
    """Trigger deep research for multiple competitors."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/competitor/deep-research/multiple",
            json={"competitor_ids": competitor_ids}
        )
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None

# NEW Helper function to call the email report endpoint
def request_email_report(company_id, user_email):
    """Requests the backend to generate and email the report."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/competitor/report/email",
            json={"company_id": company_id, "user_email": user_email},
            timeout=15 # Short timeout, as backend responds quickly (202)
        )
        if response.status_code == 202: # Accepted
            return True, response.json().get("message", "Report generation initiated.")
        else:
            error_detail = f"Error {response.status_code}: {response.text}"
            try:
                # Try to parse detail from JSON error response
                error_detail = response.json().get("detail", error_detail)
            except json.JSONDecodeError:
                pass # Keep original text if not JSON
            st.error(f"Failed to initiate report: {error_detail}")
            return False, f"Failed to initiate report: {error_detail}"
    except requests.exceptions.RequestException as e:
        st.error(f"API connection error: {e}")
        return False, f"API connection error: {e}"
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return False, f"An unexpected error occurred: {e}"

def display_loading_animation():
    """Display a loading animation."""
    with st.spinner("Processing..."):
        progress_bar = st.progress(0)
        for i in range(101):
            time.sleep(0.01)
            progress_bar.progress(i)
        progress_bar.empty()

def generate_report_html(company_details, competitors, news, insights):
    """Generate an HTML report with all analysis data."""
    if not company_details:
        return None
    
    html = f"""
    <html>
    <head>
        <title>Competitive Intelligence Report - {company_details['name']}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.5; }}
            h1 {{ color: #2c3e50; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
            h2 {{ color: #3498db; margin-top: 30px; }}
            h3 {{ color: #2980b9; }}
            .company-info {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            .competitor {{ background-color: #f5f5f5; padding: 15px; margin-bottom: 15px; border-radius: 5px; }}
            .strengths {{ color: #27ae60; }}
            .weaknesses {{ color: #e74c3c; }}
            .news-item {{ border-left: 3px solid #3498db; padding-left: 10px; margin-bottom: 10px; }}
            .insight {{ background-color: #ebf5fb; padding: 10px; margin-bottom: 10px; border-radius: 5px; }}
            .news-date {{ color: #7f8c8d; font-size: 0.9em; }}
            .news-source {{ color: #7f8c8d; font-size: 0.9em; }}
            .news-title {{ font-weight: bold; }}
        </style>
    </head>
    <body>
        <h1>Competitive Intelligence Report</h1>
        
        <div class="company-info">
            <h2>{company_details['name']}</h2>
            <p><strong>Industry:</strong> {company_details.get('industry', 'N/A')}</p>
            <p>{company_details.get('description', 'No description available.')}</p>
        </div>
        
        <h2>Competitor Analysis</h2>
    """
    
    # Add competitors
    if competitors and competitors.get("competitors"):
        for comp in competitors["competitors"]:
            html += f"""
            <div class="competitor">
                <h3>{comp["name"]}</h3>
                <p>{comp.get('description', 'No description available.')}</p>
                
                <h4 class="strengths">Strengths</h4>
                <ul>
            """
            
            strengths = comp.get("strengths", [])
            if strengths:
                for strength in strengths:
                    html += f"<li>{strength}</li>"
            else:
                html += "<li>No strengths identified.</li>"
            
            html += """
                </ul>
                
                <h4 class="weaknesses">Weaknesses</h4>
                <ul>
            """
            
            weaknesses = comp.get("weaknesses", [])
            if weaknesses:
                for weakness in weaknesses:
                    html += f"<li>{weakness}</li>"
            else:
                html += "<li>No weaknesses identified.</li>"
            
            html += """
                </ul>
            </div>
            """
    else:
        html += "<p>No competitors identified.</p>"
    
    # Add insights
    html += "<h2>Strategic Insights</h2>"
    
    if insights and insights.get("insights"):
        for insight in insights["insights"]:
            html += f"""
            <div class="insight">
                <p>{insight["content"]}</p>
                <p class="news-source">Source: {insight.get("source", "Unknown")}</p>
            </div>
            """
    else:
        html += "<p>No insights generated.</p>"
    
    # Add news by competitor
    html += "<h2>News and Developments</h2>"
    
    if news and len(news) > 0:
        # Group news by competitor
        for competitor_name, articles in news.items():
            if articles:
                html += f"<h3>News about {competitor_name}</h3>"
                
                # Sort articles by date (most recent first)
                try:
                    sorted_articles = sorted(articles, key=lambda x: x.get("published_at", ""), reverse=True)
                except:
                    sorted_articles = articles
                
                for article in sorted_articles:
                    html += f"""
                    <div class="news-item">
                        <p class="news-title">{article.get('title', 'No title')}</p>
                        <p class="news-source">Source: {article.get('source', 'Unknown')} | Published: {article.get('published_at', 'Unknown date')}</p>
                        <p>{article.get('content', 'No content available.')[:300]}...</p>
                    """
                    
                    if "url" in article:
                        html += f'<p><a href="{article["url"]}" target="_blank">Read original article</a></p>'
                    
                    html += "</div>"
    else:
        html += "<p>No news articles collected.</p>"
    
    html += """
    </body>
    </html>
    """
    
    return html

def get_report_download_link(company_details, competitors, news, insights):
    """Generate a download link for the report PDF."""
    # Generate HTML report
    html = generate_report_html(company_details, competitors, news, insights)
    if not html:
        return None
    
    # Convert HTML to PDF using pdfkit (if available) or use a fallback method with HTML download
    try:
        import pdfkit
        from io import BytesIO
        import base64
        
        # Try to generate PDF
        pdf = pdfkit.from_string(html, False)
        b64 = base64.b64encode(pdf).decode()
        company_name = company_details['name'].replace(" ", "_")
        filename = f"{company_name}_Competitive_Intelligence_Report.pdf"
        
        return f'<a href="data:application/pdf;base64,{b64}" download="{filename}" style="text-decoration:none; color:#4e8df5; font-weight:bold;"><i class="fas fa-file-pdf"></i> Download Complete Report (PDF)</a>'
    except:
        # Fallback to HTML download if pdfkit is not available
        import base64
        
        b64 = base64.b64encode(html.encode()).decode()
        company_name = company_details['name'].replace(" ", "_")
        filename = f"{company_name}_Competitive_Intelligence_Report.html"
        
        return f'<a href="data:text/html;base64,{b64}" download="{filename}" style="text-decoration:none; color:#4e8df5; font-weight:bold;"><i class="fas fa-file-code"></i> Download Complete Report (HTML)</a>'

# Initialize session state
if 'company_id' not in st.session_state:
    st.session_state.company_id = None
if 'company_details' not in st.session_state:
    st.session_state.company_details = None
if 'competitors' not in st.session_state:
    st.session_state.competitors = None
if 'news' not in st.session_state:
    st.session_state.news = None
if 'insights' not in st.session_state:
    st.session_state.insights = None
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'report_ready' not in st.session_state:
    st.session_state.report_ready = False
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'deep_research_status' not in st.session_state:
    st.session_state.deep_research_status = {}
# NEW state variables for email functionality
if 'requesting_email_report' not in st.session_state:
    st.session_state.requesting_email_report = False
if 'user_email_for_report' not in st.session_state:
    st.session_state.user_email_for_report = ""

# App Header
st.title("🔍 Competitive Intelligence Agent")
st.markdown("""
This application helps you analyze your company's competitive landscape.
Enter your company name to get started!
""")

# Check API Health
api_healthy = check_api_health()
if not api_healthy:
    st.error("⚠️ Cannot connect to the backend API. Please make sure it's running at " + API_BASE_URL)
    st.stop()

# Landing Page / Company Input
if not st.session_state.company_id:
    st.subheader("Start Your Competitive Analysis")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        company_name = st.text_input("Enter company name:", placeholder="e.g., Tesla, Microsoft, Stripe")
    with col2:
        analyze_button = st.button("Analyze", type="primary", key="analyze_button")
    
    if analyze_button and company_name:
        with st.spinner("Initiating analysis..."):
            # Initialize company analysis
            initiate_data = initialize_company_analysis(company_name)
            
            if initiate_data:
                st.session_state.company_id = initiate_data["id"]
                
                # Display progress
                st.markdown("### Analysis Progress")
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Poll for company details
                status_text.markdown("🔍 Analyzing company details...")
                for i in range(10):
                    company_details = get_company_details(st.session_state.company_id)
                    if company_details and company_details.get("description"):
                        st.session_state.company_details = company_details
                        break
                    progress_bar.progress((i + 1) * 10)
                    time.sleep(2)
                
                progress_bar.progress(40)
                status_text.markdown("🏢 Identifying competitors...")
                
                # Poll for competitors
                for i in range(10):
                    competitors_data = get_company_competitors(st.session_state.company_id)
                    if competitors_data and competitors_data.get("competitors"):
                        st.session_state.competitors = competitors_data
                        break
                    progress_bar.progress(40 + (i + 1) * 2)
                    time.sleep(2)
                
                progress_bar.progress(60)
                status_text.markdown("📰 Gathering news articles...")
                
                # Poll for news
                for i in range(10):
                    news_data = get_company_news(st.session_state.company_id)
                    if news_data:
                        st.session_state.news = news_data
                        break
                    progress_bar.progress(60 + (i + 1) * 2)
                    time.sleep(2)
                
                progress_bar.progress(80)
                status_text.markdown("💡 Generating insights...")
                
                # Poll for insights
                for i in range(10):
                    insights_data = get_company_insights(st.session_state.company_id)
                    if insights_data and insights_data.get("insights"):
                        st.session_state.insights = insights_data
                        break
                    progress_bar.progress(80 + (i + 1) * 2)
                    time.sleep(2)
                
                progress_bar.progress(100)
                status_text.markdown("✅ Analysis complete! Loading dashboard...")
                
                st.session_state.analysis_complete = True
                time.sleep(1)
                st.experimental_rerun()
    
    # Sample companies to analyze
    st.markdown("### Try with sample companies:")
    col1, col2, col3 = st.columns(3)
    
    if col1.button("Analyze Tesla"):
        st.session_state.temp_company = "Tesla"
        st.experimental_rerun()
    
    if col2.button("Analyze Airbnb"):
        st.session_state.temp_company = "Airbnb"
        st.experimental_rerun()
    
    if col3.button("Analyze Netflix"):
        st.session_state.temp_company = "Netflix"
        st.experimental_rerun()
    
    if 'temp_company' in st.session_state:
        company_name = st.session_state.temp_company
        del st.session_state.temp_company
        with st.spinner(f"Initiating analysis for {company_name}..."):
            initiate_data = initialize_company_analysis(company_name)
            if initiate_data:
                st.session_state.company_id = initiate_data["id"]
                st.experimental_rerun()

# Dashboard (after analysis initiated)
else:
    # Sidebar for navigation and controls
    with st.sidebar:
        st.markdown("### Company Analysis")
        
        # Show company details if available
        if st.session_state.company_details:
            st.markdown(f"**{st.session_state.company_details['name']}**")
            st.markdown(f"*{st.session_state.company_details['industry']}*")
        
        # Refresh button
        if st.button("Refresh Data"):
            with st.spinner("Refreshing data..."):
                company_details = get_company_details(st.session_state.company_id)
                if company_details:
                    st.session_state.company_details = company_details
                
                competitors_data = get_company_competitors(st.session_state.company_id)
                if competitors_data:
                    st.session_state.competitors = competitors_data
                
                news_data = get_company_news(st.session_state.company_id)
                if news_data:
                    st.session_state.news = news_data
                
                insights_data = refresh_company_insights(st.session_state.company_id)
                if insights_data:
                    st.session_state.insights = insights_data
                
                st.success("Data refreshed successfully!")
                # Set report ready flag if all data is available
                if (st.session_state.company_details and st.session_state.competitors and 
                    st.session_state.news and st.session_state.insights):
                    st.session_state.report_ready = True
        
        # Download report option (visible only when report is ready)
        if (st.session_state.company_details and st.session_state.competitors and 
            st.session_state.news and st.session_state.insights):
            st.session_state.report_ready = True
            
        if st.session_state.report_ready:
            st.markdown("---")
            st.markdown("### 📊 Analysis Report")
            report_link = get_report_download_link(
                st.session_state.company_details,
                st.session_state.competitors,
                st.session_state.news,
                st.session_state.insights
            )
            if report_link:
                st.markdown(report_link, unsafe_allow_html=True)
                st.markdown("Get a complete report with all competitor analysis, news, and insights in one document.")
        
        # Reset button
        st.markdown("---")
        if st.button("Start New Analysis"):
            st.session_state.clear()
            st.experimental_rerun()
    
    # Check if data is loaded
    if not st.session_state.company_details:
        with st.spinner("Loading company details..."):
            company_details = get_company_details(st.session_state.company_id)
            if company_details:
                st.session_state.company_details = company_details
    
    if not st.session_state.competitors:
        with st.spinner("Loading competitors..."):
            competitors_data = get_company_competitors(st.session_state.company_id)
            if competitors_data:
                st.session_state.competitors = competitors_data
    
    if not st.session_state.news:
        with st.spinner("Loading news..."):
            news_data = get_company_news(st.session_state.company_id)
            if news_data:
                st.session_state.news = news_data
    
    if not st.session_state.insights:
        with st.spinner("Loading insights..."):
            insights_data = get_company_insights(st.session_state.company_id)
            if insights_data:
                st.session_state.insights = insights_data
    
    # Main Dashboard
    if st.session_state.company_details:
        # Display welcome message
        if "welcome_message" in st.session_state.company_details and st.session_state.company_details["welcome_message"]:
            st.markdown("### 🎉 " + st.session_state.company_details["welcome_message"])
        
        # Dashboard tabs
        tabs = st.tabs([
            "📊 Overview", 
            "🏢 Competitors", 
            "📰 News", 
            "💡 Insights", 
            "📑 Deep Research",
            "💬 Chat"
        ])
        
        # Overview Tab
        with tabs[0]:
            st.subheader(f"{st.session_state.company_details['name']} Competitive Analysis")
            
            # Company description
            st.markdown("### About")
            st.write(st.session_state.company_details.get("description", "No description available."))
            
            # Metrics
            st.markdown("### Metrics")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                competitors_count = len(st.session_state.competitors.get("competitors", [])) if st.session_state.competitors else 0
                st.metric("Competitors", competitors_count)
            
            with col2:
                news_count = 0
                if st.session_state.news:
                    for competitor_name, articles in st.session_state.news.items():
                        news_count += len(articles)
                st.metric("News Articles", news_count)
            
            with col3:
                insights_count = len(st.session_state.insights.get("insights", [])) if st.session_state.insights else 0
                st.metric("Insights", insights_count)
            
            # Visualization - Competitor Comparison
            if st.session_state.competitors and len(st.session_state.competitors.get("competitors", [])) > 0:
                st.markdown("### Competitor News Analysis")
                
                # Create a dataframe for competitor news analysis
                competitor_data = []
                
                # Check if news data is available
                if st.session_state.news and len(st.session_state.news) > 0:
                    # Count news articles for each competitor
                    for comp in st.session_state.competitors["competitors"]:
                        news_count = 0
                        comp_name = comp["name"]
                        
                        # Find news count for this competitor
                        if comp_name in st.session_state.news:
                            news_count = len(st.session_state.news[comp_name])
                        
                        competitor_data.append({
                            "name": comp_name,
                            "news_count": news_count
                        })
                else:
                    # Create empty data if no news available
                    for comp in st.session_state.competitors["competitors"]:
                        competitor_data.append({
                            "name": comp["name"],
                            "news_count": 0
                        })
                
                comp_df = pd.DataFrame(competitor_data)
                
                # Sort by news count descending
                comp_df = comp_df.sort_values(by="news_count", ascending=False)
                
                # Bar chart for news count
                if not comp_df.empty:
                    fig = go.Figure()
                    
                    # Add trace for news count
                    fig.add_trace(go.Bar(
                        x=comp_df["name"],
                        y=comp_df["news_count"],
                        name="News Articles",
                        marker_color="#3498db"
                    ))
                    
                    fig.update_layout(
                        title="News Articles Collected per Competitor",
                        xaxis_title="Competitor",
                        yaxis_title="Number of Articles",
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        )
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    if sum(comp_df["news_count"]) == 0:
                        st.info("No news articles have been collected yet for these competitors.")
            
            # Recent News
            if st.session_state.news and len(st.session_state.news) > 0:
                st.markdown("### Recent News")
                
                # Flatten news articles
                all_articles = []
                for competitor_name, articles in st.session_state.news.items():
                    for article in articles:
                        article["competitor_name"] = competitor_name
                        all_articles.append(article)
                
                # Sort by date (most recent first)
                if all_articles:
                    try:
                        # Sort by published_at if available
                        all_articles = sorted(all_articles, key=lambda x: x.get("published_at", ""), reverse=True)
                    except:
                        pass
                
                # Display recent news
                for i, article in enumerate(all_articles[:5]):
                    with st.container():
                        st.markdown(f"""
                        <div class="news-card">
                            <div class="news-title">{article.get('title', 'No title')}</div>
                            <div class="news-source">Source: {article.get('source', 'Unknown')} | Competitor: {article.get('competitor_name', 'Unknown')}</div>
                            <div class="news-date">Published: {article.get('published_at', 'Unknown date')}</div>
                        </div>
                        """, unsafe_allow_html=True)
        
        # Competitors Tab
        with tabs[1]:
            st.subheader("Competitor Analysis")
            
            if st.session_state.competitors and len(st.session_state.competitors.get("competitors", [])) > 0:
                # Display competitors in cards
                for comp in st.session_state.competitors["competitors"]:
                    with st.container():
                        st.markdown(f"""
                        <div class="competitor-card">
                            <h3>{comp["name"]}</h3>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown("#### Description")
                        st.write(comp.get("description", "No description available."))
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("#### Strengths")
                            strengths = comp.get("strengths", [])
                            if strengths:
                                for strength in strengths:
                                    st.markdown(f"- {strength}")
                            else:
                                st.write("No strengths identified.")
                        
                        with col2:
                            st.markdown("#### Weaknesses")
                            weaknesses = comp.get("weaknesses", [])
                            if weaknesses:
                                for weakness in weaknesses:
                                    st.markdown(f"- {weakness}")
                            else:
                                st.write("No weaknesses identified.")
                        
                        st.markdown("---")
            else:
                st.info("No competitors have been identified yet. Please wait for the analysis to complete.")
        
        # News Tab
        with tabs[2]:
            st.subheader("News Monitoring")
            
            if st.session_state.news and len(st.session_state.news) > 0:
                # Competitor filter
                competitors = list(st.session_state.news.keys())
                selected_competitor = st.selectbox("Filter by competitor:", ["All"] + competitors)
                
                # Flatten and filter news articles
                all_articles = []
                if selected_competitor == "All":
                    for competitor_name, articles in st.session_state.news.items():
                        for article in articles:
                            article["competitor_name"] = competitor_name
                            all_articles.append(article)
                else:
                    articles = st.session_state.news.get(selected_competitor, [])
                    for article in articles:
                        article["competitor_name"] = selected_competitor
                        all_articles.append(article)
                
                # Sort by date (most recent first)
                if all_articles:
                    try:
                        # Sort by published_at if available
                        all_articles = sorted(all_articles, key=lambda x: x.get("published_at", ""), reverse=True)
                    except:
                        pass
                
                # Display articles
                if all_articles:
                    for i, article in enumerate(all_articles):
                        with st.container():
                            st.markdown(f"""
                            <div class="news-card">
                                <div class="news-title">{article.get('title', 'No title')}</div>
                                <div class="news-source">Source: {article.get('source', 'Unknown')} | Competitor: {article.get('competitor_name', 'Unknown')}</div>
                                <div class="news-date">Published: {article.get('published_at', 'Unknown date')}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            with st.expander("View Content"):
                                st.write(article.get("content", "No content available."))
                                
                                if "url" in article:
                                    st.markdown(f"[Read original article]({article['url']})")
                else:
                    st.info("No news articles found for the selected competitor.")
            else:
                st.info("No news articles have been collected yet. Please wait for the analysis to complete.")
        
        # Insights Tab
        with tabs[3]:
            st.subheader("Strategic Insights")
            
            if st.session_state.insights and st.session_state.insights.get("insights"):
                # Add a refresh button
                if st.button("Generate New Insights"):
                    with st.spinner("Generating new insights..."):
                        insights_data = refresh_company_insights(st.session_state.company_id)
                        if insights_data:
                            st.session_state.insights = insights_data
                            st.success("New insights generated!")
                
                # Display insights
                for i, insight in enumerate(st.session_state.insights["insights"]):
                    with st.container():
                        st.markdown(f"""
                        <div class="insight-card">
                            <p>{insight["content"]}</p>
                            <p class="news-source">Source: {insight.get("source", "Unknown")}</p>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No insights have been generated yet. Please wait for the analysis to complete.")
                
                # Add a generate button
                if st.button("Generate Insights Now"):
                    with st.spinner("Generating insights..."):
                        insights_data = refresh_company_insights(st.session_state.company_id)
                        if insights_data:
                            st.session_state.insights = insights_data
                            st.success("Insights generated successfully!")
                            st.experimental_rerun()
        
        # Deep Research Tab
        with tabs[4]:
            st.subheader("Deep Competitor Research")
            
            if st.session_state.competitors and len(st.session_state.competitors.get("competitors", [])) > 0:
                competitors = st.session_state.competitors["competitors"]

                # --- Keep Competitor Selection and Research Trigger ---
                # Update status tracking if needed
                for comp in competitors:
                    comp_id = comp["id"]
                    if comp_id not in st.session_state.deep_research_status:
                        st.session_state.deep_research_status[comp_id] = comp.get("deep_research_status", "not_started")
                    else: # Update if already exists
                         st.session_state.deep_research_status[comp_id] = comp.get("deep_research_status", st.session_state.deep_research_status[comp_id])

                selected_competitors = st.multiselect(
                    "Select competitors to research (if not already researched):",
                    options=[comp["name"] for comp in competitors if comp.get("deep_research_status", "not_started") not in ["completed", "pending"]],
                    format_func=lambda x: x,
                    key="deep_research_select"
                )

                selected_competitor_ids_to_start = [
                    comp["id"] for comp in competitors
                    if comp["name"] in selected_competitors
                ]

                if selected_competitor_ids_to_start:
                    if st.button("Start Deep Research", type="primary", key="start_deep_research_btn"):
                        with st.spinner("Initiating deep research..."):
                            if len(selected_competitor_ids_to_start) == 1:
                                result = trigger_deep_research(selected_competitor_ids_to_start[0])
                            else:
                                result = trigger_multiple_deep_research(selected_competitor_ids_to_start)

                            if result:
                                for comp_id in selected_competitor_ids_to_start:
                                    st.session_state.deep_research_status[comp_id] = "pending"
                                st.success("Deep research initiated successfully! Refresh status periodically.")
                                # Refresh competitors data immediately to show pending status
                                time.sleep(1) # Small delay before refresh
                                competitors_data = get_company_competitors(st.session_state.company_id)
                                if competitors_data:
                                    st.session_state.competitors = competitors_data
                                    st.experimental_rerun() # Rerun to update display
                            else:
                                st.error("Failed to initiate deep research.")
                # --- End Research Trigger ---

                st.markdown("---")
                st.markdown("### Research Status")

                completed_competitor_ids = []
                for comp in competitors:
                    comp_id = comp["id"]
                    comp_name = comp["name"]
                    # Get latest status directly from potentially refreshed competitor data
                    status = comp.get("deep_research_status", st.session_state.deep_research_status.get(comp_id, "not_started"))
                    # Update session state just in case
                    st.session_state.deep_research_status[comp_id] = status

                    if status == "completed":
                        status_color = "green"
                        icon = "✅"
                        completed_competitor_ids.append(comp_id)
                    elif status == "pending":
                        status_color = "orange"
                        icon = "🔄"
                    elif status == "error":
                        status_color = "red"
                        icon = "❌"
                    else: # not_started or unknown
                        status_color = "gray"
                        icon = "⏱️"

                    st.markdown(f"<span style='color:{status_color};'>{icon} **{comp_name}**: {status.replace('_', ' ').capitalize()}</span>", unsafe_allow_html=True)

                # Refresh button for research status (Keep)
                if st.button("Refresh Research Status", key="refresh_status_btn"):
                    with st.spinner("Refreshing status..."):
                        competitors_data = get_company_competitors(st.session_state.company_id)
                        if competitors_data:
                            st.session_state.competitors = competitors_data
                            # Force status update from refreshed data
                            for comp_refr in st.session_state.competitors["competitors"]:
                                st.session_state.deep_research_status[comp_refr['id']] = comp_refr.get('deep_research_status', 'not_started')
                            st.success("Research status refreshed!")
                            st.experimental_rerun() # Rerun to update display
                        else:
                            st.error("Failed to refresh competitor data.")

                st.markdown("---")

                # --- NEW: Email Report Section ---
                if completed_competitor_ids:
                    st.markdown("### Get Combined Report via Email")
                    st.info(f"A combined report can be generated for the {len(completed_competitor_ids)} competitor(s) with completed research.")

                    if st.button("Prepare Email Report", key="prepare_email_button"):
                        st.session_state.requesting_email_report = True
                        st.session_state.user_email_for_report = "" # Reset email field
                        st.experimental_rerun() # Rerun to show email input

                    if st.session_state.requesting_email_report:
                        st.session_state.user_email_for_report = st.text_input(
                            "Enter your email address:",
                            value=st.session_state.user_email_for_report,
                            key="user_email_input_field"
                        )

                        if st.button("Send Report via Email", key="send_email_report_btn"):
                            email = st.session_state.user_email_for_report.strip()
                            if email and "@" in email and "." in email: # Basic validation
                                with st.spinner("Initiating report generation and sending... This may take a moment."):
                                    success, message = request_email_report(st.session_state.company_id, email)
                                    if success:
                                        st.success(message)
                                        st.session_state.requesting_email_report = False # Reset state
                                        st.session_state.user_email_for_report = ""
                                        st.experimental_rerun() # Rerun to hide email input
                                    else:
                                        st.error(f"Failed: {message}") # Error already shown by helper, but repeat message
                            else:
                                st.warning("Please enter a valid email address.")
                        if st.button("Cancel", key="cancel_email_report_btn"):
                             st.session_state.requesting_email_report = False
                             st.session_state.user_email_for_report = ""
                             st.experimental_rerun()

                else:
                    st.info("No deep research reports have been completed yet. Start research and check back later.")

            else:
                st.info("No competitors identified yet. Please wait for the initial analysis to complete.")
        
        # Chat Tab
        with tabs[5]:
            st.subheader("Ask About Your Competitors")
            
            # Display chat history
            chat_container = st.container()
            with chat_container:
                for i, (query, response) in enumerate(st.session_state.chat_history):
                    st.markdown(f"**You**: {query}")
                    
                    # Check if the response contains an error message
                    if response.startswith("Error:") or "error" in response.lower() or "index is still being built" in response.lower():
                        st.error(response)
                        # Add a retry button for failed queries
                        if st.button(f"Retry this question", key=f"retry_{i}"):
                            with st.spinner("Regenerating response..."):
                                retry_response = ask_rag_question(st.session_state.company_id, query)
                                # Update the response in chat history
                                st.session_state.chat_history[i] = (query, retry_response)
                                st.experimental_rerun()
                    else:
                        st.markdown(f"**AI**: {response}")
                    
                    st.markdown("---")
            
            # Chat input - store in session state to maintain value during reruns
            if "chat_input" not in st.session_state:
                st.session_state.chat_input = ""
                
            user_query = st.text_input("Ask a question:", value=st.session_state.chat_input, key="chat_input_field")
            
            # Suggested questions
            st.markdown("**Suggested Questions:**")
            
            company_name = st.session_state.company_details["name"]
            
            suggested_questions = [
                f"What is the main industry for {company_name}?",
                "List the identified competitors.",
                "What are the recent industry trends?"
            ]
            
            # Add competitor-specific questions if competitors exist
            if st.session_state.competitors and st.session_state.competitors.get("competitors"):
                competitors = st.session_state.competitors["competitors"]
                if len(competitors) > 0:
                    first_comp_name = competitors[0]["name"]
                    suggested_questions.append(f"What are the strengths of {first_comp_name}?")
                    suggested_questions.append(f"What are the weaknesses of {first_comp_name}?")
                    if len(competitors) > 1:
                        second_comp_name = competitors[1]["name"]
                        suggested_questions.append(f"Compare {first_comp_name} and {second_comp_name}.")
            
            # Display suggestion buttons in columns
            cols = st.columns(3)
            for i, question in enumerate(suggested_questions):
                col_idx = i % 3
                if cols[col_idx].button(question, key=f"suggest_{i}"):
                    # Set the question in the session state
                    st.session_state.chat_input = question
                    st.experimental_rerun()
            
            # Send button and clear button in columns
            col1, col2 = st.columns([1, 5])
            
            with col1:
                send_pressed = st.button("Send", type="primary")
            
            with col2:
                if st.button("Clear History"):
                    st.session_state.chat_history = []
                    st.session_state.chat_input = ""
                    st.experimental_rerun()
            
            if send_pressed and user_query:
                with st.spinner("Generating response..."):
                    response = ask_rag_question(st.session_state.company_id, user_query)
                    # Add to chat history
                    st.session_state.chat_history.append((user_query, response))
                    # Clear input
                    st.session_state.chat_input = ""
                    st.experimental_rerun()
    else:
        # Still waiting for data
        st.markdown("### Loading Data")
        
        with st.spinner("Waiting for data to be loaded..."):
            # Attempt to fetch company details again
            company_details = get_company_details(st.session_state.company_id)
            if company_details:
                st.session_state.company_details = company_details
                st.experimental_rerun()
            
            # Progress indicator
            st.progress(50)
            st.markdown("Please wait while we analyze your company data. This may take a few moments.")

# Footer
st.markdown("---")
st.markdown("### About Competitive Intelligence Agent")
st.markdown("""
This application uses AI to analyze your company's competitive landscape.
It identifies competitors, collects news, generates insights, and provides deep research reports.
""") 