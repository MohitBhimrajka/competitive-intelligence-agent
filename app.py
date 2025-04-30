import streamlit as st
import requests
import pandas as pd
import time
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timezone, timedelta
import base64
import io
from PIL import Image
import re
import os
import subprocess
import tempfile
from pathlib import Path
import threading
import warnings
import sys
from markdown_to_json import dictify

# API Configuration
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
SUPERVITY_API_TOKEN = "720819056d1a426837896db9"
SUPERVITY_API_ORG = "2051"
SUPERVITY_AGENT_ID = "cma11km3i00f5nvo7yn2bcwqs"
SUPERVITY_SKILL_ID = "ca4o24jvtsjzkocdr5gml3x0"
SUPERVITY_EMAIL_AGENT_ID = "cma11km3i00f5nvo7yn2bcwqs"
SUPERVITY_EMAIL_SKILL_ID = "ca4o24jvtsjzkocdr5gml3x0"

# Page configuration
st.set_page_config(
    page_title="Competitive Intelligence Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Improved Custom CSS
st.markdown(
    """
    <style>
    .main {
        background-color: #f5f7fa;
        padding: 1.5rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        border-bottom: 2px solid #e0e4e8;
        padding-bottom: 8px;
        margin-bottom: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 60px;
        white-space: pre-wrap;
        background-color: #f1f3f8;
        border-radius: 8px 8px 0px 0px;
        padding: 12px 24px;
        font-weight: 500;
        letter-spacing: 0.3px;
        transition: all 0.2s ease;
        border: 1px solid #e0e4e8;
        border-bottom: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4361ee;
        color: white;
        transform: translateY(-4px);
        border-color: #3a56e4;
        box-shadow: 0 4px 10px rgba(67, 97, 238, 0.15);
    }
    .competitor-card {
        background-color: white;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.05);
        margin-bottom: 24px;
        border: 1px solid #f0f0f0;
        transition: transform 0.2s;
    }
    .competitor-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.08);
    }
    .insight-card {
        background-color: white;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
        border-left: 4px solid #4361ee;
    }
    .metrics-container {
        display: flex;
        justify-content: space-between;
        margin-bottom: 24px;
        gap: 16px;
    }
    .metric-item {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.05);
        flex: 1;
        text-align: center;
    }
    .news-card {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        border-left: 4px solid #3498db;
        transition: transform 0.2s;
    }
    .news-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
    }
    .news-source {
        font-size: 12px;
        color: #6c757d;
        margin-top: 4px;
    }
    .news-title {
        font-weight: 600;
        font-size: 16px;
        color: #2c3e50;
        margin-bottom: 4px;
    }
    .news-date {
        font-size: 12px;
        color: #6c757d;
        margin-bottom: 8px;
    }
    .tab-subheader {
        font-size: 1.5rem;
        font-weight: 600;
        margin-top: 1.5rem;
        margin-bottom: 1.5rem;
        color: #2c3e50;
        border-bottom: 2px solid #f0f0f0;
        padding-bottom: 10px;
    }
    .chat-message {
        padding: 16px;
        border-radius: 12px;
        margin-bottom: 12px;
        max-width: 85%;
    }
    .user-message {
        background-color: #e9ecef;
        margin-left: auto;
        border-top-right-radius: 2px;
    }
    .assistant-message {
        background-color: #4361ee;
        color: white;
        margin-right: auto;
        border-top-left-radius: 2px;
    }
    .chat-container {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.05);
    }
    .loading-animation {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100px;
    }
    .strength-item {
        background-color: #e3f8e5;
        border-radius: 6px;
        padding: 8px 12px;
        margin-bottom: 8px;
        border-left: 3px solid #28a745;
    }
    .weakness-item {
        background-color: #fbeaea;
        border-radius: 6px;
        padding: 8px 12px;
        margin-bottom: 8px;
        border-left: 3px solid #dc3545;
    }
    div[data-testid="stMetric"] {
        background-color: white;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }
    div[data-testid="stMetricLabel"] {
        font-size: 14px;
        font-weight: 600;
    }
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        font-weight: 700;
        color: #4361ee;
    }
    button[data-testid="baseButton-primary"] {
        background-color: #4361ee;
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s;
        padding: 0.5rem 1.5rem;
    }
    button[data-testid="baseButton-primary"]:hover {
        background-color: #3a56e4;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(67, 97, 238, 0.25);
    }
    .sidebar .block-container {
        padding-top: 2rem;
    }
    .section-divider {
        height: 2px;
        background-color: #f0f0f0;
        margin: 24px 0;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# Additional Helper Functions for Supervity API
def save_json_as_text(data, file_path=None):
    """Save JSON data as a text file.

    Args:
        data: The data to save (dict or list that can be serialized to JSON)
        file_path: Optional path to save the file. If None, creates a temporary file.

    Returns:
        The path to the saved file
    """
    if file_path is None:
        # Create a temporary file with .txt extension
        fd, file_path = tempfile.mkstemp(suffix=".txt")
        os.close(fd)

    # Convert data to JSON string and write to file
    with open(file_path, "w", encoding="utf-8") as f:
        if isinstance(data, str):
            f.write(data)
        else:
            json.dump(data, f, indent=2)

    return file_path


def call_supervity_api(input_file_path, agent_id=None, skill_id=None):
    """Call the Supervity API using the provided input file.

    Args:
        input_file_path: Path to the input file to be processed
        agent_id: Optional Agent ID (defaults to SUPERVITY_AGENT_ID if None)
        skill_id: Optional Skill ID (defaults to SUPERVITY_SKILL_ID if None)

    Returns:
        API response or error message
    """
    try:
        # Ensure file exists
        if not os.path.exists(input_file_path):
            print(f"Error: Input file not found: {input_file_path}")
            return {"error": f"Input file not found: {input_file_path}"}

        # Use default values if not provided
        agent_id = agent_id or SUPERVITY_AGENT_ID
        skill_id = skill_id or SUPERVITY_SKILL_ID

        # Build the curl command as a string to ensure proper quoting
        cmd = f'curl -L -X POST "https://api.supervity.ai/botapi/draftSkills/v2/execute/" --header \'x-api-token: {SUPERVITY_API_TOKEN}\' --header \'x-api-org: {SUPERVITY_API_ORG}\' --form \'v2AgentId={agent_id}\' --form \'v2SkillId={skill_id}\' --form \'inputFiles=@"{input_file_path}"\''

        # Log the command (with sensitive information masked)
        print(f"Executing curl command: {cmd}")

        # Execute the command with shell=True to preserve quotes
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)

        # Check if the command was successful
        if result.returncode == 0:
            print(f"Supervity API call successful. Response: {result.stdout[:100]}...")
            try:
                # Try to parse JSON response
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                # Return raw output if not JSON
                return {"response": result.stdout}
        else:
            print(f"Supervity API call failed with error: {result.stderr}")
            return {"error": result.stderr}

    except Exception as e:
        print(f"Exception in call_supervity_api: {str(e)}")
        return {"error": str(e)}


def process_data_with_supervity(
    data, file_name=None, agent_id=None, skill_id=None, is_email=False
):
    """Process data with Supervity API.

    Args:
        data: The data to process (dict or list)
        file_name: Optional name for the temporary file
        agent_id: Optional custom agent ID
        skill_id: Optional custom skill ID
        is_email: Whether this is an email request (uses email agent/skill IDs)

    Returns:
        The API response
    """
    # Set appropriate agent and skill IDs based on request type
    if is_email:
        agent_id = agent_id or SUPERVITY_EMAIL_AGENT_ID
        skill_id = skill_id or SUPERVITY_EMAIL_SKILL_ID
    else:
        agent_id = agent_id or SUPERVITY_AGENT_ID
        skill_id = skill_id or SUPERVITY_SKILL_ID

    # Create a temporary file if no file name is provided
    if file_name:
        # Create a temporary file with the specified name
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, file_name)
    else:
        # Create a file with a random name
        file_path = None

    # Save data to file
    file_path = save_json_as_text(data, file_path)

    try:
        # Call the API
        response = call_supervity_api(file_path, agent_id, skill_id)

        # Clean up - remove temporary file
        if os.path.exists(file_path):
            os.remove(file_path)

        return response
    except Exception as e:
        # Make sure to clean up even if there's an error
        if os.path.exists(file_path):
            os.remove(file_path)
        return {"error": str(e)}


# Helper Functions
def check_api_health():
    """Check if the API is running and healthy."""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        return (
            response.status_code == 200 and response.json().get("status") == "healthy"
        )
    except:
        return False


def initialize_company_analysis(company_name):
    """Start analysis for a company and return the ID."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/company", json={"name": company_name}
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
        response = requests.post(
            f"{API_BASE_URL}/api/insights/company/{company_id}/refresh"
        )
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
            f"{API_BASE_URL}/api/chat/{company_id}", json={"query": query}, timeout=60
        )
        if response.status_code == 200:
            return response.json().get("answer")
        elif response.status_code == 500:
            # Check if the error is related to the RAG index being built
            error_text = response.json().get("detail", "").lower()
            if "index" in error_text and "built" in error_text:
                return (
                    "The RAG index is still being built. Please try again in a moment."
                )
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
        response = requests.post(
            f"{API_BASE_URL}/api/competitor/{competitor_id}/deep-research"
        )
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
            json={"competitor_ids": competitor_ids},
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
            timeout=15,  # Short timeout, as backend responds quickly (202)
        )
        if response.status_code == 202:  # Accepted
            return {
                "status": "accepted",
                "message": response.json().get("message", "Report generation initiated.")
            }
        else:
            error_detail = f"Error {response.status_code}: {response.text}"
            try:
                # Try to parse detail from JSON error response
                error_detail = response.json().get("detail", error_detail)
            except json.JSONDecodeError:
                pass  # Keep original text if not JSON
            return {
                "status": "error", 
                "detail": error_detail
            }
    except requests.exceptions.RequestException as e:
        error_msg = f"API connection error: {e}"
        return {"status": "error", "detail": error_msg}
    except Exception as e:
        error_msg = f"An unexpected error occurred: {e}"
        return {"status": "error", "detail": error_msg}


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
                    sorted_articles = sorted(
                        articles, key=lambda x: x.get("published_at", ""), reverse=True
                    )
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
        company_name = company_details["name"].replace(" ", "_")
        filename = f"{company_name}_Competitive_Intelligence_Report.pdf"

        return f'<a href="data:application/pdf;base64,{b64}" download="{filename}" style="text-decoration:none; color:#4e8df5; font-weight:bold;"><i class="fas fa-file-pdf"></i> Download Complete Report (PDF)</a>'
    except:
        # Fallback to HTML download if pdfkit is not available
        import base64

        b64 = base64.b64encode(html.encode()).decode()
        company_name = company_details["name"].replace(" ", "_")
        filename = f"{company_name}_Competitive_Intelligence_Report.html"

        return f'<a href="data:text/html;base64,{b64}" download="{filename}" style="text-decoration:none; color:#4e8df5; font-weight:bold;"><i class="fas fa-file-code"></i> Download Complete Report (HTML)</a>'


# Initialize session state
if "company_id" not in st.session_state:
    st.session_state.company_id = None
if "company_details" not in st.session_state:
    st.session_state.company_details = None
if "competitors" not in st.session_state:
    st.session_state.competitors = None
if "news" not in st.session_state:
    st.session_state.news = None
if "insights" not in st.session_state:
    st.session_state.insights = None
if "analysis_complete" not in st.session_state:
    st.session_state.analysis_complete = False
if "report_ready" not in st.session_state:
    st.session_state.report_ready = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "deep_research_status" not in st.session_state:
    st.session_state.deep_research_status = {}
# NEW state variables for email functionality
if "requesting_email_report" not in st.session_state:
    st.session_state.requesting_email_report = False
if "user_email_for_report" not in st.session_state:
    st.session_state.user_email_for_report = ""

# App Header
st.title("🔍 Competitive Intelligence Agent")
st.markdown(
    """
This application helps you analyze your company's competitive landscape.
Enter your company name to get started!
"""
)

# Check API Health
api_healthy = check_api_health()
if not api_healthy:
    st.error(
        "⚠️ Cannot connect to the backend API. Please make sure it's running at "
        + API_BASE_URL
    )
    st.stop()

# Landing Page / Company Input
if not st.session_state.company_id:
    st.subheader("Start Your Competitive Analysis")

    col1, col2 = st.columns([3, 1])
    with col1:
        company_name = st.text_input(
            "Enter company name:", placeholder="e.g., Tesla, Microsoft, Stripe"
        )
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
                    competitors_data = get_company_competitors(
                        st.session_state.company_id
                    )
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
                st.rerun()

    # Sample companies to analyze
    st.markdown("### Try with sample companies:")
    col1, col2, col3 = st.columns(3)

    if col1.button("Analyze Tesla"):
        st.session_state.temp_company = "Tesla"
        st.rerun()

    if col2.button("Analyze Airbnb"):
        st.session_state.temp_company = "Airbnb"
        st.rerun()

    if col3.button("Analyze Netflix"):
        st.session_state.temp_company = "Netflix"
        st.rerun()

    if "temp_company" in st.session_state:
        company_name = st.session_state.temp_company
        del st.session_state.temp_company
        with st.spinner(f"Initiating analysis for {company_name}..."):
            initiate_data = initialize_company_analysis(company_name)
            if initiate_data:
                st.session_state.company_id = initiate_data["id"]
                st.rerun()

# Dashboard (after analysis initiated)
else:
    # Sidebar for navigation and controls
    with st.sidebar:
        st.markdown(
            """<div style="text-align: center;">
        <h3 style="margin-bottom: 2px;">Company Analysis</h3>
        <div class="section-divider"></div>
        </div>""",
            unsafe_allow_html=True,
        )

        # Show company details if available
        if st.session_state.company_details:
            st.markdown(
                f"""<div style="text-align: center; margin-bottom: 20px;">
            <h2 style="color: #4361ee; margin-bottom: 2px;">{st.session_state.company_details['name']}</h2>
            <p style="color: #6c757d; font-style: italic;">{st.session_state.company_details['industry']}</p>
            </div>""",
                unsafe_allow_html=True,
            )

        # Refresh button
        if st.button("🔄 Refresh Data", key="refresh_button"):
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
                if (
                    st.session_state.company_details
                    and st.session_state.competitors
                    and st.session_state.news
                    and st.session_state.insights
                ):
                    st.session_state.report_ready = True

        # Download report option (visible only when report is ready)
        if (
            st.session_state.company_details
            and st.session_state.competitors
            and st.session_state.news
            and st.session_state.insights
        ):
            st.session_state.report_ready = True

        if st.session_state.report_ready:
            st.markdown(
                """<div class="section-divider"></div>
            <h3 style="margin-bottom: 12px;">📊 Analysis Report</h3>""",
                unsafe_allow_html=True,
            )
            report_link = get_report_download_link(
                st.session_state.company_details,
                st.session_state.competitors,
                st.session_state.news,
                st.session_state.insights,
            )
            if report_link:
                st.markdown(report_link, unsafe_allow_html=True)
                st.markdown(
                    """<p style="font-size: 14px; color: #6c757d;">Get a complete report with all competitor analysis, news, and insights in one document.</p>""",
                    unsafe_allow_html=True,
                )

        # Reset button
        st.markdown("""<div class="section-divider"></div>""", unsafe_allow_html=True)
        if st.button("🔄 Start New Analysis", key="reset_button"):
            st.session_state.clear()
            st.rerun()

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
        if (
            "welcome_message" in st.session_state.company_details
            and st.session_state.company_details["welcome_message"]
        ):
            st.markdown(
                f"""<div style="background-color: #e3f2fd; border-radius: 12px; padding: 16px; margin-bottom: 24px; border-left: 4px solid #4361ee;">
            <h4 style="margin: 0;">🎉 {st.session_state.company_details["welcome_message"]}</h4>
            </div>""",
                unsafe_allow_html=True,
            )

        # Dashboard tabs
        tabs = st.tabs(
            [
                "📊 Overview",
                "🏢 Competitors",
                "📰 News",
                "💡 Insights",
                "📑 Deep Research",
                "💬 Chat",
                "🔄 Integrations",
            ]
        )

        # Overview Tab
        with tabs[0]:
            st.markdown(
                f"""<h2 style="color: #2c3e50; margin-bottom: 24px;">
            {st.session_state.company_details['name']} Competitive Analysis</h2>""",
                unsafe_allow_html=True,
            )

            # Company description
            st.markdown(
                """<div class="tab-subheader">About</div>""", unsafe_allow_html=True
            )
            st.markdown(
                f"""<div style="background-color: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);">
            {st.session_state.company_details.get("description", "No description available.")}
            </div>""",
                unsafe_allow_html=True,
            )

            # Metrics
            st.markdown(
                """<div class="tab-subheader">Metrics</div>""", unsafe_allow_html=True
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                competitors_count = (
                    len(st.session_state.competitors.get("competitors", []))
                    if st.session_state.competitors
                    else 0
                )
                st.metric("Competitors", competitors_count)

            with col2:
                news_count = 0
                if st.session_state.news:
                    for competitor_name, articles in st.session_state.news.items():
                        news_count += len(articles)
                st.metric("News Articles", news_count)

            with col3:
                insights_count = (
                    len(st.session_state.insights.get("insights", []))
                    if st.session_state.insights
                    else 0
                )
                st.metric("Insights", insights_count)

            # Visualization - Competitor Comparison
            if (
                st.session_state.competitors
                and len(st.session_state.competitors.get("competitors", [])) > 0
            ):
                st.markdown(
                    """<div class="tab-subheader">Competitor News Analysis</div>""",
                    unsafe_allow_html=True,
                )

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

                        competitor_data.append(
                            {"name": comp_name, "news_count": news_count}
                        )
                else:
                    # Create empty data if no news available
                    for comp in st.session_state.competitors["competitors"]:
                        competitor_data.append({"name": comp["name"], "news_count": 0})

                comp_df = pd.DataFrame(competitor_data)

                # Sort by news count descending
                comp_df = comp_df.sort_values(by="news_count", ascending=False)

                # Bar chart for news count
                if not comp_df.empty:
                    fig = go.Figure()

                    # Add trace for news count
                    fig.add_trace(
                        go.Bar(
                            x=comp_df["name"],
                            y=comp_df["news_count"],
                            name="News Articles",
                            marker_color="#4361ee",
                        )
                    )

                    fig.update_layout(
                        title="News Articles Collected per Competitor",
                        xaxis_title="Competitor",
                        yaxis_title="Number of Articles",
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        font=dict(family="Arial, sans-serif", size=14, color="#2c3e50"),
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1,
                        ),
                    )

                    fig.update_xaxes(
                        showgrid=True, gridwidth=1, gridcolor="rgba(211, 211, 211, 0.3)"
                    )

                    fig.update_yaxes(
                        showgrid=True, gridwidth=1, gridcolor="rgba(211, 211, 211, 0.3)"
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    if sum(comp_df["news_count"]) == 0:
                        st.info(
                            "No news articles have been collected yet for these competitors."
                        )

            # Recent News
            if st.session_state.news and len(st.session_state.news) > 0:
                st.markdown(
                    """<div class="tab-subheader">Recent News</div>""",
                    unsafe_allow_html=True,
                )

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
                        all_articles = sorted(
                            all_articles,
                            key=lambda x: x.get("published_at", ""),
                            reverse=True,
                        )
                    except:
                        pass

                # Display recent news
                for i, article in enumerate(all_articles[:5]):
                    with st.container():
                        st.markdown(
                            f"""
                        <div class="news-card">
                            <div class="news-title">{article.get('title', 'No title')}</div>
                            <div class="news-source">Source: {article.get('source', 'Unknown')} | Competitor: {article.get('competitor_name', 'Unknown')}</div>
                            <div class="news-date">Published: {article.get('published_at', 'Unknown date')}</div>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

        # Competitors Tab
        with tabs[1]:
            st.markdown(
                """<h2 style="color: #2c3e50; margin-bottom: 24px;">Competitor Analysis</h2>""",
                unsafe_allow_html=True,
            )

            if (
                st.session_state.competitors
                and len(st.session_state.competitors.get("competitors", [])) > 0
            ):
                # Display competitors in cards
                for comp in st.session_state.competitors["competitors"]:
                    with st.container():
                        st.markdown(
                            f"""
                        <div class="competitor-card">
                            <h3 style="color: #4361ee; margin-top: 0;">{comp["name"]}</h3>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                        st.markdown(
                            """<div class="tab-subheader" style="font-size: 1.2rem;">Description</div>""",
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f"""<div style="background-color: white; border-radius: 8px; padding: 16px; margin-bottom: 20px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.03);">
                        {comp.get("description", "No description available.")}
                        </div>""",
                            unsafe_allow_html=True,
                        )

                        col1, col2 = st.columns(2)

                        with col1:
                            st.markdown(
                                """<div class="tab-subheader" style="font-size: 1.2rem;">Strengths</div>""",
                                unsafe_allow_html=True,
                            )
                            strengths = comp.get("strengths", [])
                            if strengths:
                                for strength in strengths:
                                    st.markdown(
                                        f"""<div class="strength-item">{strength}</div>""",
                                        unsafe_allow_html=True,
                                    )
                            else:
                                st.write("No strengths identified.")

                        with col2:
                            st.markdown(
                                """<div class="tab-subheader" style="font-size: 1.2rem;">Weaknesses</div>""",
                                unsafe_allow_html=True,
                            )
                            weaknesses = comp.get("weaknesses", [])
                            if weaknesses:
                                for weakness in weaknesses:
                                    st.markdown(
                                        f"""<div class="weakness-item">{weakness}</div>""",
                                        unsafe_allow_html=True,
                                    )
                            else:
                                st.write("No weaknesses identified.")

                        st.markdown(
                            """<div class="section-divider"></div>""",
                            unsafe_allow_html=True,
                        )
            else:
                st.info(
                    "No competitors have been identified yet. Please wait for the analysis to complete."
                )

        # News Tab
        with tabs[2]:
            st.markdown(
                """<h2 style="color: #2c3e50; margin-bottom: 24px;">News Monitoring</h2>""",
                unsafe_allow_html=True,
            )

            if st.session_state.news and len(st.session_state.news) > 0:
                # Improved filter container
                with st.container():
                    st.markdown(
                        """<div style="background-color: white; border-radius: 8px; padding: 16px; margin-bottom: 20px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.03);">""",
                        unsafe_allow_html=True,
                    )
                    # Competitor filter
                    competitors = list(st.session_state.news.keys())
                    selected_competitor = st.selectbox(
                        "Filter by competitor:", ["All"] + competitors
                    )
                    st.markdown("""</div>""", unsafe_allow_html=True)

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
                        all_articles = sorted(
                            all_articles,
                            key=lambda x: x.get("published_at", ""),
                            reverse=True,
                        )
                    except:
                        pass

                # Display articles
                if all_articles:
                    for i, article in enumerate(all_articles):
                        with st.container():
                            st.markdown(
                                f"""
                            <div class="news-card">
                                <div class="news-title">{article.get('title', 'No title')}</div>
                                <div class="news-source">Source: {article.get('source', 'Unknown')} | Competitor: {article.get('competitor_name', 'Unknown')}</div>
                                <div class="news-date">Published: {article.get('published_at', 'Unknown date')}</div>
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )

                            with st.expander("View Content"):
                                st.write(
                                    article.get("content", "No content available.")
                                )

                                if "url" in article:
                                    st.markdown(
                                        f"[Read original article]({article['url']})"
                                    )
                else:
                    st.info("No news articles found for the selected competitor.")
            else:
                st.info(
                    "No news articles have been collected yet. Please wait for the analysis to complete."
                )

        # Insights Tab
        with tabs[3]:
            st.markdown(
                """<h2 style="color: #2c3e50; margin-bottom: 24px;">Strategic Insights</h2>""",
                unsafe_allow_html=True,
            )

            if st.session_state.insights and st.session_state.insights.get("insights"):
                # Add a refresh button
                if st.button("Generate New Insights"):
                    with st.spinner("Generating new insights..."):
                        insights_data = refresh_company_insights(
                            st.session_state.company_id
                        )
                        if insights_data:
                            st.session_state.insights = insights_data
                            st.success("New insights generated!")

                # Display insights
                for i, insight in enumerate(st.session_state.insights["insights"]):
                    with st.container():
                        st.markdown(
                            f"""
                        <div class="insight-card">
                            <p>{insight["content"]}</p>
                            <p class="news-source">Source: {insight.get("source", "Unknown")}</p>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )
            else:
                st.info(
                    "No insights have been generated yet. Please wait for the analysis to complete."
                )

                # Add a generate button
                if st.button("Generate Insights Now"):
                    with st.spinner("Generating insights..."):
                        insights_data = refresh_company_insights(
                            st.session_state.company_id
                        )
                        if insights_data:
                            st.session_state.insights = insights_data
                            st.success("Insights generated successfully!")
                            st.rerun()

        # Deep Research Tab
        with tabs[4]:
            st.markdown(
                """<h2 style="color: #2c3e50; margin-bottom: 24px;">Deep Competitor Research</h2>""",
                unsafe_allow_html=True,
            )

            if (
                st.session_state.competitors
                and len(st.session_state.competitors.get("competitors", [])) > 0
            ):
                competitors = st.session_state.competitors["competitors"]

                # --- Keep Competitor Selection and Research Trigger ---
                # Update status tracking if needed
                for comp in competitors:
                    comp_id = comp["id"]
                    if comp_id not in st.session_state.deep_research_status:
                        st.session_state.deep_research_status[comp_id] = comp.get(
                            "deep_research_status", "not_started"
                        )
                    else:  # Update if already exists
                        st.session_state.deep_research_status[comp_id] = comp.get(
                            "deep_research_status",
                            st.session_state.deep_research_status[comp_id],
                        )

                selected_competitors = st.multiselect(
                    "Select competitors to research (if not already researched):",
                    options=[
                        comp["name"]
                        for comp in competitors
                        if comp.get("deep_research_status", "not_started")
                        not in ["completed", "pending"]
                    ],
                    format_func=lambda x: x,
                    key="deep_research_select",
                )

                selected_competitor_ids_to_start = [
                    comp["id"]
                    for comp in competitors
                    if comp["name"] in selected_competitors
                ]

                if selected_competitor_ids_to_start:
                    if st.button(
                        "Start Deep Research",
                        type="primary",
                        key="start_deep_research_btn",
                    ):
                        with st.spinner("Initiating deep research..."):
                            if len(selected_competitor_ids_to_start) == 1:
                                result = trigger_deep_research(
                                    selected_competitor_ids_to_start[0]
                                )
                            else:
                                result = trigger_multiple_deep_research(
                                    selected_competitor_ids_to_start
                                )

                            if result:
                                for comp_id in selected_competitor_ids_to_start:
                                    st.session_state.deep_research_status[comp_id] = (
                                        "pending"
                                    )
                                st.success(
                                    "Deep research initiated successfully! Refresh status periodically."
                                )
                                # Refresh competitors data immediately to show pending status
                                time.sleep(1)  # Small delay before refresh
                                competitors_data = get_company_competitors(
                                    st.session_state.company_id
                                )
                                if competitors_data:
                                    st.session_state.competitors = competitors_data
                                    st.rerun()  # Rerun to update display
                            else:
                                st.error("Failed to initiate deep research.")
                # --- End Research Trigger ---

                st.markdown(
                    """<div class="section-divider"></div>""", unsafe_allow_html=True
                )
                st.markdown(
                    """<h3 style="margin-bottom: 12px;">Research Status</h3>""",
                    unsafe_allow_html=True,
                )

                completed_competitor_ids = []
                for comp in competitors:
                    comp_id = comp["id"]
                    comp_name = comp["name"]
                    # Get latest status directly from potentially refreshed competitor data
                    status = comp.get(
                        "deep_research_status",
                        st.session_state.deep_research_status.get(
                            comp_id, "not_started"
                        ),
                    )
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
                    else:  # not_started or unknown
                        status_color = "gray"
                        icon = "⏱️"

                    st.markdown(
                        f"""<span style='color:{status_color};'>{icon} **{comp_name}**: {status.replace('_', ' ').capitalize()}</span>""",
                        unsafe_allow_html=True,
                    )

                # Refresh button for research status (Keep)
                if st.button("Refresh Research Status", key="refresh_status_btn"):
                    with st.spinner("Refreshing status..."):
                        competitors_data = get_company_competitors(
                            st.session_state.company_id
                        )
                        if competitors_data:
                            st.session_state.competitors = competitors_data
                            # Force status update from refreshed data
                            for comp_refr in st.session_state.competitors[
                                "competitors"
                            ]:
                                st.session_state.deep_research_status[
                                    comp_refr["id"]
                                ] = comp_refr.get("deep_research_status", "not_started")
                            st.success("Research status refreshed!")
                            st.rerun()  # Rerun to update display
                        else:
                            st.error("Failed to refresh competitor data.")

                st.markdown(
                    """<div class="section-divider"></div>""", unsafe_allow_html=True
                )

                # --- NEW: Email Report Section ---
                if completed_competitor_ids:
                    st.markdown(
                        """<div class="section-divider"></div>
                    <h3 style="margin-bottom: 12px;">Get Combined Report via Email</h3>""",
                        unsafe_allow_html=True,
                    )
                    st.info(
                        f"A combined report can be generated for the {len(completed_competitor_ids)} competitor(s) with completed research."
                    )

                    if st.button("Prepare Email Report", key="prepare_email_button"):
                        st.session_state.requesting_email_report = True
                        st.session_state.user_email_for_report = ""  # Reset email field
                        st.rerun()  # Rerun to show email input

                    if st.session_state.requesting_email_report:
                        st.session_state.user_email_for_report = st.text_input(
                            "Enter your email address:",
                            value=st.session_state.user_email_for_report,
                            key="user_email_input_field",
                        )

                        if st.button(
                            "Send Report via Email", key="send_email_report_btn"
                        ):
                            email = st.session_state.user_email_for_report.strip()
                            if (
                                email and "@" in email and "." in email
                            ):  # Basic validation
                                with st.spinner(
                                    "Initiating report generation and sending... This may take a moment."
                                ):
                                    # Call the backend API to generate the report and get link
                                    result = request_email_report(
                                        st.session_state.company_id, email
                                    )

                                    if result["status"] == "accepted":
                                        st.success(result["message"])
                                        st.session_state.requesting_email_report = (
                                            False  # Reset state
                                        )
                                        st.session_state.user_email_for_report = ""
                                        st.rerun()  # Rerun to hide email input
                                    else:
                                        st.error(
                                            f"Failed: {result['detail']}"
                                        )  # Error already shown by helper, but repeat message
                            else:
                                st.warning("Please enter a valid email address.")
                        if st.button("Cancel", key="cancel_email_report_btn"):
                            st.session_state.requesting_email_report = False
                            st.session_state.user_email_for_report = ""
                            st.rerun()

                else:
                    st.info(
                        "No deep research reports have been completed yet. Start research and check back later."
                    )

            else:
                st.info(
                    "No competitors identified yet. Please wait for the initial analysis to complete."
                )

        # Chat Tab
        with tabs[5]:
            st.markdown(
                """<h2 style="color: #2c3e50; margin-bottom: 24px;">Chat with Your Data</h2>""",
                unsafe_allow_html=True,
            )

            # Instructions
            st.markdown(
                """<div style="background-color: white; border-radius: 12px; padding: 16px; margin-bottom: 20px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);">
            <p>Ask questions about your company and its competitors. The AI assistant will search through the collected news, analysis, and insights to provide relevant answers.</p>
            </div>""",
                unsafe_allow_html=True,
            )

            # Chat container
            st.markdown("""<div class="chat-container">""", unsafe_allow_html=True)

            # Display chat history
            for message in st.session_state.chat_history:
                if message["role"] == "user":
                    st.markdown(
                        f"""<div class="chat-message user-message">{message["content"]}</div>""",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"""<div class="chat-message assistant-message">{message["content"]}</div>""",
                        unsafe_allow_html=True,
                    )

            st.markdown("""</div>""", unsafe_allow_html=True)

            # Initialize chat_input in session state if not present
            if "chat_input_value" not in st.session_state:
                st.session_state.chat_input_value = ""

            # Chat input - use session_state.chat_input_value to store the value between reruns
            chat_input = st.text_input(
                "Ask a question:",
                value=st.session_state.chat_input_value,
                key="chat_input_field",
            )

            # Suggested questions
            st.markdown(
                """<div style="margin-top: 12px; margin-bottom: 20px;">
            <p style="font-weight: 600; color: #2c3e50;">Suggested Questions:</p>
            </div>""",
                unsafe_allow_html=True,
            )

            company_name = st.session_state.company_details["name"]

            suggested_questions = [
                f"What is the main industry for {company_name}?",
                "List the identified competitors.",
                "What are the recent industry trends?",
            ]

            # Add competitor-specific questions if competitors exist
            if st.session_state.competitors and st.session_state.competitors.get(
                "competitors"
            ):
                competitors = st.session_state.competitors["competitors"]
                if len(competitors) > 0:
                    first_comp_name = competitors[0]["name"]
                    suggested_questions.append(
                        f"What are the strengths of {first_comp_name}?"
                    )
                    suggested_questions.append(
                        f"What are the weaknesses of {first_comp_name}?"
                    )
                    if len(competitors) > 1:
                        second_comp_name = competitors[1]["name"]
                        suggested_questions.append(
                            f"Compare {first_comp_name} and {second_comp_name}."
                        )

            # Display suggestion buttons in columns with improved styling
            cols = st.columns(3)
            for i, question in enumerate(suggested_questions):
                col_idx = i % 3
                if cols[col_idx].button(
                    question,
                    key=f"suggest_{i}",
                    use_container_width=True,
                ):
                    # Update the chat input value in session state
                    st.session_state.chat_input_value = question

                    # Add user message to chat history
                    st.session_state.chat_history.append(
                        {"role": "user", "content": question}
                    )

                    # Get response from RAG system
                    with st.spinner("Generating response..."):
                        answer = ask_rag_question(st.session_state.company_id, question)

                    # Add assistant response to chat history
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": answer}
                    )

                    # Clear input value for next question
                    st.session_state.chat_input_value = ""

                    # Rerun to update UI
                    st.rerun()

            # Send button and clear history in columns
            col1, col2 = st.columns([1, 5])

            with col1:
                send_pressed = st.button("Send", type="primary", key="send_chat")

            with col2:
                if st.button("Clear History", key="clear_chat"):
                    st.session_state.chat_history = []
                    st.session_state.chat_input_value = ""
                    st.rerun()

            # Process user input
            if send_pressed and chat_input.strip():
                # Store user input
                user_input = chat_input.strip()

                # Add user message to chat history
                st.session_state.chat_history.append(
                    {"role": "user", "content": user_input}
                )

                # Get response from RAG system
                with st.spinner("Generating response..."):
                    answer = ask_rag_question(st.session_state.company_id, user_input)

                # Add assistant response to chat history
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": answer}
                )

                # Clear input value for next question
                st.session_state.chat_input_value = ""

                # Rerun to update UI
                st.rerun()

        # New Supervity API Tab (renamed to Integrations)
        with tabs[6]:
            st.markdown(
                """<h2 style="color: #2c3e50; margin-bottom: 24px;">Integrations</h2>""",
                unsafe_allow_html=True,
            )

            st.markdown(
                """<div style="background-color: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05); margin-bottom: 24px;">
            <p>This integration allows you to send a competitive intelligence report via email. The system will generate a PDF and email it to the specified address.</p>
            </div>""",
                unsafe_allow_html=True,
            )

            # Initialize session state for Email Report
            if "email_recipient" not in st.session_state:
                st.session_state.email_recipient = ""
            if "email_result" not in st.session_state:
                st.session_state.email_result = None

            st.markdown(
                """<div style="background-color: #f5f7fa; border-radius: 8px; padding: 16px; margin-top: 16px;">""",
                unsafe_allow_html=True,
            )
            st.markdown("### Email Settings")

            # Email recipient
            email_recipient = st.text_input(
                "Email address:",
                value=st.session_state.email_recipient,
                key="email_recipient_input",
            )

            st.session_state.email_recipient = email_recipient

            st.markdown("""</div>""", unsafe_allow_html=True)

            # Send button
            if st.button(
                "Send Report via Email",
                type="primary",
                key="send_email_button",
            ):
                if st.session_state.company_id and email_recipient:
                    with st.spinner("Sending report via email..."):
                        # Request email report
                        result = request_email_report(
                            st.session_state.company_id, email_recipient
                        )
                        st.session_state.email_result = result

                        if result["status"] == "accepted":
                            st.success("✓ Report generation and email delivery initiated")
                        else:
                            st.error(f"Error: {result['detail']}")
                else:
                    if not st.session_state.company_id:
                        st.warning("Please select a company first.")
                    if not email_recipient:
                        st.warning("Please enter an email address.")
    else:
        # Still waiting for data
        st.markdown("### Loading Data")

        with st.spinner("Waiting for data to be loaded..."):
            # Attempt to fetch company details again
            company_details = get_company_details(st.session_state.company_id)
            if company_details:
                st.session_state.company_details = company_details
                st.rerun()

            # Progress indicator
            st.progress(50)
            st.markdown(
                "Please wait while we analyze your company data. This may take a few moments."
            )

# Footer
st.markdown("---")
st.markdown("### About Competitive Intelligence Agent")
st.markdown(
    """
This application uses AI to analyze your company's competitive landscape.
It identifies competitors, collects news, generates insights, and provides deep research reports.
"""
)
