# mohitbhimrajka-competitive-intelligence-agent/app.py

import streamlit as st
import requests
import json
import asyncio
import time
import threading
from datetime import datetime
import os
import io
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional

# --- Page Config MUST BE THE FIRST STREAMLIT COMMAND ---
st.set_page_config(
    page_title="Competitive Intelligence Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- Configuration & Initialization ---
load_dotenv() # Load environment variables first

# Attempt to import backend services. Handle gracefully if backend/* is not directly importable.
try:
    # Corrected import paths assuming running from root
    from backend.services.gemini_service import GeminiService
    from backend.services.news_service import NewsService
    from backend.services.pdf_service import pdf_service # Singleton instance
    from backend.services.rag_service import rag_service # Singleton instance
    from backend.services.database import db # Import db if needed directly by Streamlit (usually not)
    BACKEND_AVAILABLE = True
except ImportError as e:
    # Display the error message *after* set_page_config
    st.error(f"Failed to import backend services: {e}. Ensure the backend is installed and accessible. App functionality will be limited.")
    BACKEND_AVAILABLE = False
    # Define dummy services/classes *after* the potential error message
    class DummyService:
        async def analyze_company(self, *args, **kwargs): return {"description": "Backend unavailable", "industry": "N/A", "welcome_message": "Backend services could not be loaded."}
        async def identify_competitors(self, *args, **kwargs): return {"competitors": []}
        async def get_competitor_news(self, *args, **kwargs): return []
        async def generate_insights(self, *args, **kwargs): return {"insights": []}
        async def deep_research_competitor(self, *args, **kwargs): return "## Error\nBackend unavailable." # Return error markdown directly
        async def update_rag_index(self, *args, **kwargs): pass
        async def ask_question(self, *args, **kwargs): return "Backend services are unavailable."

    class DummyPDFService:
        def generate_single_report_pdf(self, *args, **kwargs): return io.BytesIO(b"Backend unavailable")

    # Assign dummy classes/instances if backend not available
    GeminiService = DummyService
    NewsService = DummyService
    rag_service = DummyService()
    pdf_service = DummyPDFService()

# --- Configuration & Initialization ---
load_dotenv()

# Initialize services if backend is available
if BACKEND_AVAILABLE:
    gemini_service = GeminiService()
    news_service = NewsService()
    # rag_service and pdf_service are already instantiated singletons from their modules


# --- Custom CSS ---
st.markdown("""
<style>
    /* General */
    .stApp {
        background-color: #F0F2F6; /* Light grey background */
    }
    .main .block-container {
        padding: 1rem 2rem 2rem 2rem; /* More padding */
        max-width: 1400px; /* Limit max width */
    }
    h1 {
        color: #1E3A8A; /* Dark blue */
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 600;
    }

    /* Input Area */
    .input-container {
        background-color: #FFFFFF;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        margin-bottom: 2rem;
        border: 1px solid #E2E8F0;
    }
    .stButton>button {
        background-color: #2563EB; /* Primary blue */
        color: white;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-weight: 500;
        border: none;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #1D4ED8; /* Darker blue on hover */
    }
    .stButton>button:focus {
         box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.4);
         outline: none;
    }
    .stTextInput>div>div>input {
        border-radius: 8px;
        border: 1px solid #CBD5E1;
        padding: 0.6rem 0.8rem;
    }
     .stTextInput>div>div>input:focus {
        border-color: #2563EB;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2);
     }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        border-bottom: 2px solid #E2E8F0;
        padding-bottom: 0;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent;
        border: none;
        border-bottom: 2px solid transparent;
        padding: 0 1rem;
        margin-bottom: -2px; /* Align with border */
        color: #475569; /* Grey text */
        font-weight: 500;
        transition: all 0.3s ease;
    }
    .stTabs [aria-selected="true"] {
        color: #1E3A8A; /* Dark blue for selected */
        border-bottom: 2px solid #1E3A8A;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #F8FAFC; /* Very light grey hover */
        color: #1E3A8A;
    }
    .stTabs [data-baseweb="tab-highlight"] {
         background-color: #1E3A8A; /* Highlight color */
         height: 2px;
    }
    div[data-testid="stTabs"] {
        background-color: #FFFFFF;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        border: 1px solid #E2E8F0;
    }
     div[data-testid="stVerticalBlock"] {
         gap: 1.5rem; /* Spacing between elements in tabs */
     }


    /* Cards */
    .card {
        background-color: #FFFFFF;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border: 1px solid #E2E8F0;
        margin-bottom: 1rem;
        transition: box-shadow 0.3s ease;
    }
    .card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .card h3, .card h4 {
        margin-top: 0;
        color: #1E3A8A;
        border-bottom: 1px solid #E2E8F0;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    .card h5 {
        color: #334155;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }
     .card ul {
         padding-left: 20px;
         margin-bottom: 0;
     }
     .card li {
         margin-bottom: 0.3rem;
         color: #475569;
     }

    /* News Card Specifics */
    .news-card a {
        color: #2563EB;
        text-decoration: none;
        font-weight: 500;
    }
    .news-card a:hover {
        text-decoration: underline;
    }
    .news-card small {
        color: #64748B;
        display: block;
        margin-bottom: 0.5rem;
    }

    /* Insight Card Specifics */
    .insight-card {
        border-left-width: 5px;
        border-left-style: solid;
        padding-left: 1.5rem;
    }
    .insight-opportunity { border-left-color: #10B981; } /* Emerald */
    .insight-threat { border-left-color: #EF4444; }    /* Red */
    .insight-trend { border-left-color: #3B82F6; }     /* Blue */
    .insight-card small {
        color: #64748B;
        display: block;
        margin-top: 0.5rem;
        font-style: italic;
    }

    /* Deep Research Status */
    .status-badge {
        display: inline-block;
        padding: 0.2em 0.6em;
        font-size: 0.9em;
        font-weight: 600;
        border-radius: 1em;
        margin-right: 0.5em;
        vertical-align: middle;
    }
    .status-pending { background-color: #FEF3C7; color: #92400E; } /* Amber */
    .status-completed { background-color: #D1FAE5; color: #065F46; } /* Green */
    .status-error { background-color: #FEE2E2; color: #991B1B; }    /* Red */
    .status-not_started { background-color: #E5E7EB; color: #4B5563; } /* Grey */
    .research-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.8rem 0;
        border-bottom: 1px solid #F3F4F6;
    }
     .research-item:last-child {
         border-bottom: none;
     }

    /* Chat Area */
    .chat-container {
        background-color: #FFFFFF;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        margin-bottom: 2rem;
        border: 1px solid #E2E8F0;
        height: 500px; /* Fixed height */
        display: flex;
        flex-direction: column;
    }
    .chat-container h3 {
         margin-top: 0;
         margin-bottom: 1rem;
         color: #1E3A8A;
         padding-bottom: 0.5rem;
         border-bottom: 1px solid #E2E8F0;
    }
    div[data-testid="stChatMessage"] {
        background-color: #F1F5F9; /* Light background for messages */
        border-radius: 10px;
        padding: 0.7rem 1rem;
        margin-bottom: 0.6rem;
    }
    div[data-testid="stChatMessage"] span[data-testid="stAvatar"] { /* Avatar styling */
        width: 35px;
        height: 35px;
        font-size: 1.2rem;
        background-color: #94A3B8;
        color: white;
    }
     div[data-testid="stChatMessage"]:has(span[title="user"]) span[data-testid="stAvatar"] {
         background-color: #6366F1; /* Indigo for user */
     }
     div[data-testid="stChatMessage"]:has(span[title="assistant"]) span[data-testid="stAvatar"] {
         background-color: #10B981; /* Emerald for assistant */
     }
     div[data-testid="chatScrollContainer"] { /* Make message area scrollable */
         flex-grow: 1;
         overflow-y: auto;
         padding-right: 10px; /* Space for scrollbar */
         margin-bottom: 1rem;
     }
     /* Customize scrollbar */
    div[data-testid="chatScrollContainer"]::-webkit-scrollbar {
        width: 8px;
    }
    div[data-testid="chatScrollContainer"]::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    div[data-testid="chatScrollContainer"]::-webkit-scrollbar-thumb {
        background: #cbd5e1;
        border-radius: 10px;
    }
    div[data-testid="chatScrollContainer"]::-webkit-scrollbar-thumb:hover {
        background: #94a3b8;
    }
     div[data-testid="stChatInput"] {
         border-top: 1px solid #E2E8F0;
         padding-top: 1rem;
     }
     div[data-testid="stChatInput"] textarea {
         border-radius: 8px;
         border: 1px solid #CBD5E1;
     }
      div[data-testid="stChatInput"] textarea:focus {
         border-color: #2563EB;
         box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2);
      }

    /* Utility */
    .mb-1 { margin-bottom: 1rem !important; }
    .mt-1 { margin-top: 1rem !important; }

</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
# Helper to initialize state keys
def init_state(key, default_value):
    if key not in st.session_state:
        st.session_state[key] = default_value

init_state('company_name', None)
init_state('company_data', None) # Stores result from analyze_company
init_state('competitors_data', None) # Stores result from identify_competitors
init_state('news_data', {}) # Dict: {comp_name: [articles]}
init_state('insights_data', None) # Stores result from generate_insights
init_state('research_status', {}) # Dict: {comp_name: "status"} (not_started, pending, completed, error)
init_state('research_results', {}) # Dict: {comp_name: "markdown_content"}
init_state('research_selection', {}) # Dict: {comp_name: bool}
init_state('chat_messages', []) # List of {"role": "user/assistant", "content": "..."}

# Loading flags for background tasks
init_state('_news_loading', False)
init_state('_insights_loading', False)
init_state('_research_running', False) # Flag to prevent multiple triggers

# Notification flags
init_state('_news_ready_toast', False)
init_state('_insights_ready_toast', False)
init_state('_research_ready_toast', {}) # Dict: {comp_name: True/False}
init_state('_rag_update_queued', False) # Flag to trigger RAG update

# --- Helper Functions ---

def display_toast_notifications():
    """Checks flags and displays toast notifications."""
    if st.session_state._news_ready_toast:
        st.toast("📰 Latest news is ready!", icon="📰")
        st.session_state._news_ready_toast = False

    if st.session_state._insights_ready_toast:
        st.toast("💡 Strategic insights generated!", icon="💡")
        st.session_state._insights_ready_toast = False

    for comp_name, ready in list(st.session_state._research_ready_toast.items()):
        if ready:
            status = st.session_state.research_status.get(comp_name, "unknown")
            if status == "completed":
                st.toast(f"🔍 Deep research for {comp_name} completed!", icon="✅")
            elif status == "error":
                st.toast(f"❌ Error during deep research for {comp_name}.", icon="⚠️")
            st.session_state._research_ready_toast[comp_name] = False # Reset flag

# --- Background Task Functions (using threading) ---

def run_in_background(target_func, args=()):
    """Helper to run a function in a background thread."""
    thread = threading.Thread(target=target_func, args=args)
    thread.start()
    # We don't join the thread here, it runs independently.

def background_fetch_news(company_id: str, competitor_ids: List[str]):
    """Fetches news for all competitors in the background."""
    st.session_state._news_loading = True
    try:
        competitors = asyncio.run(db.get_competitors_by_company(company_id)) # Need competitor names
        temp_news_data = {}
        tasks = []

        # Prepare async tasks for news service calls
        async def fetch_news_for_competitor(comp_name: str, comp_id: str):
            try:
                # Use the news service to get combined data
                articles = await news_service.get_competitor_news(comp_name)
                # Filter and format if necessary (ensure keys match what UI expects)
                formatted_articles = [
                    {
                        "title": a.get("title", "N/A"),
                        "source": a.get("source", "N/A"),
                        "url": a.get("url"),
                        "published_at": a.get("publishedAt", a.get("published_at", "N/A")), # Handle variation
                        "content": a.get("content", "N/A")
                    }
                    for a in articles
                ]
                temp_news_data[comp_name] = formatted_articles
                # Also store in DB via RAG service (or separate function if needed)
                # Example: await db.store_news_for_competitor(comp_id, formatted_articles)
            except Exception as e:
                st.error(f"Error fetching news for {comp_name}: {e}") # Show error in main thread via state? Risky. Log instead.
                print(f"Error fetching news for {comp_name}: {e}")
                temp_news_data[comp_name] = [] # Ensure key exists even on error

        # Create tasks
        for comp in competitors:
             if comp['id'] in competitor_ids: # Only fetch for relevant competitors if needed
                 tasks.append(fetch_news_for_competitor(comp['name'], comp['id']))

        # Run tasks concurrently
        if tasks:
            asyncio.run(asyncio.gather(*tasks))

        # Update session state (thread-safe assignment)
        st.session_state.news_data = temp_news_data
        st.session_state._news_ready_toast = True
        st.session_state._rag_update_queued = True # Queue RAG update

    except Exception as e:
        print(f"Error in background_fetch_news thread: {e}") # Log error
    finally:
        st.session_state._news_loading = False
        # Note: st.rerun() cannot be called directly from thread.
        # The UI will update on the next natural rerun cycle when it sees loading=False.

def background_generate_insights(company_id: str, company_name: str):
    """Generates insights in the background."""
    st.session_state._insights_loading = True
    try:
        # Ensure news data is available (it should have been fetched)
        news_for_insight = st.session_state.news_data
        competitors_for_insight = st.session_state.competitors_data # Assumes this is populated

        if not competitors_for_insight or not news_for_insight:
             print("Warning: Missing competitor or news data for insight generation.")
             # Handle this case - maybe show a warning in UI?
             st.session_state.insights_data = {"insights": []} # Set empty
             return

        # Prepare data for the service call
        insights_response = asyncio.run(gemini_service.generate_insights(
            company_name,
            competitors_for_insight,
            news_for_insight
        ))

        # Format insights to match desired structure if necessary
        # (The current prompt seems to return the desired structure)
        formatted_insights = insights_response # Assuming direct use is okay

        st.session_state.insights_data = formatted_insights
        st.session_state._insights_ready_toast = True
        st.session_state._rag_update_queued = True # Queue RAG update

    except Exception as e:
        print(f"Error in background_generate_insights thread: {e}") # Log error
        st.session_state.insights_data = {"insights": []} # Set empty on error
    finally:
        st.session_state._insights_loading = False
        # UI will update on next rerun.

def background_deep_research(competitor_name: str, competitor_desc: str, company_name: Optional[str]):
    """Runs deep research for one competitor in the background."""
    st.session_state.research_status[competitor_name] = "pending"
    research_data = None
    try:
        # Call the deep research function (which is async)
        research_result_dict = asyncio.run(gemini_service.deep_research_competitor(
            competitor_name,
            competitor_desc,
            company_name
        ))

        # Assuming the service returns a dict like {"markdown": "..."} or {"error": "..."}
        # Let's adjust based on the actual service implementation (it seems to return markdown string directly or an error markdown)
        markdown_content = research_result_dict # Assuming it's the markdown string

        if isinstance(markdown_content, str) and markdown_content.strip().startswith("## Error"):
             st.session_state.research_status[competitor_name] = "error"
             st.session_state.research_results[competitor_name] = markdown_content
             print(f"Error in deep research for {competitor_name}: Service returned error.")
        elif isinstance(markdown_content, str) and len(markdown_content) > 50: # Basic check for valid content
             st.session_state.research_status[competitor_name] = "completed"
             st.session_state.research_results[competitor_name] = markdown_content
             st.session_state._rag_update_queued = True # Queue RAG update
        else:
             st.session_state.research_status[competitor_name] = "error"
             st.session_state.research_results[competitor_name] = "## Error\nReceived invalid or empty content from research service."
             print(f"Error in deep research for {competitor_name}: Invalid content received.")

    except Exception as e:
        print(f"Error in background_deep_research thread for {competitor_name}: {e}") # Log error
        st.session_state.research_status[competitor_name] = "error"
        st.session_state.research_results[competitor_name] = f"## Error\nAn unexpected error occurred during research: {e}"
    finally:
        # Mark notification ready
        st.session_state._research_ready_toast[competitor_name] = True
        # Flag that research process finished (used to unlock button maybe)
        # Need a way to track how many are running if started concurrently
        # For simplicity, let's assume the main button handles the _research_running flag.

def background_update_rag(company_id: str):
    """Updates the RAG index in the background."""
    print(f"Background task: Updating RAG index for {company_id}")
    try:
        asyncio.run(rag_service.update_rag_index(company_id))
        print(f"Background task: RAG index update complete for {company_id}")
        # Optional: show a toast?
        # st.session_state._rag_update_toast = True # Need to add handling for this
    except Exception as e:
        print(f"Error in background_update_rag thread: {e}")
    finally:
        st.session_state._rag_update_queued = False # Reset the queue flag

# --- UI Rendering Functions ---

def display_company_details(company_data: Dict[str, Any]):
    st.markdown("### Company Overview", unsafe_allow_html=True)
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### About")
            st.markdown(company_data.get('description', 'N/A'))
        with col2:
            st.markdown("#### Industry")
            st.markdown(company_data.get('industry', 'N/A'))

        if 'welcome_message' in company_data:
            st.markdown(f"""
            <div style="margin-top: 1rem; padding: 1rem; background-color: #E0F2FE; border-radius: 8px; border: 1px solid #BAE6FD;">
                👋 {company_data['welcome_message']}
            </div>
            """, unsafe_allow_html=True)

def display_competitors(competitors: List[Dict[str, Any]]):
    st.markdown("### Competitive Landscape", unsafe_allow_html=True)
    if not competitors:
        st.info("No competitors identified yet or analysis still in progress.")
        return

    cols = st.columns(2) # Display in two columns
    col_idx = 0
    for competitor in competitors:
        with cols[col_idx % 2]:
            with st.container(): # No border needed if card class handles it
                 st.markdown(f"""
                 <div class="card competitor-card">
                     <h4>{competitor.get('name', 'N/A')}</h4>
                     <p>{competitor.get('description', 'No description available.')}</p>
                     <h5>💪 Strengths</h5>
                     <ul>{''.join([f"<li>{s}</li>" for s in competitor.get('strengths', [])]) or "<li>N/A</li>"}</ul>
                     <h5>⚠️ Weaknesses</h5>
                     <ul>{''.join([f"<li>{w}</li>" for w in competitor.get('weaknesses', [])]) or "<li>N/A</li>"}</ul>
                 </div>
                 """, unsafe_allow_html=True)
        col_idx += 1

def display_news(news_data: Dict[str, List[Dict[str, Any]]]):
    st.markdown("### Latest News & Developments", unsafe_allow_html=True)

    if not news_data:
        st.info("No news data available yet. Fetching may be in progress.")
        return

    # Optional: Add filters like date range or search here if desired
    # days_back = st.slider("Days to look back (visual filter - data already fetched)", 1, 90, 30)

    competitor_tabs = st.tabs(list(news_data.keys()))

    for i, comp_name in enumerate(news_data.keys()):
        with competitor_tabs[i]:
            articles = news_data[comp_name]
            if articles:
                st.markdown(f"#### {len(articles)} Articles for {comp_name}")
                for article in articles:
                     published_date = article.get('published_at', 'N/A')
                     # Try to format date nicely
                     try:
                         if published_date and published_date != 'N/A':
                              dt_obj = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
                              published_date = dt_obj.strftime('%Y-%m-%d %H:%M')
                     except ValueError:
                         pass # Keep original string if parsing fails

                     with st.container(): # No border needed if card class handles it
                         st.markdown(f"""
                         <div class="card news-card">
                             <h5>{article.get('title', 'No Title')}</h5>
                             <small>Source: {article.get('source', 'N/A')} | Published: {published_date}</small>
                             <p>{article.get('content', 'No content preview available.')[:300]}...</p>
                             {f'<a href="{article["url"]}" target="_blank">Read more</a>' if article.get("url") else ''}
                         </div>
                         """, unsafe_allow_html=True)
            else:
                st.info(f"No recent news or developments found for {comp_name}.")

def display_insights(insights_data: Dict[str, Any]):
    st.markdown("### Strategic Insights", unsafe_allow_html=True)
    if not insights_data or not insights_data.get('insights'):
        st.info("No insights generated yet or generation is in progress.")
        return

    # Group insights by type
    insights_by_type = {"opportunity": [], "threat": [], "trend": []}
    for insight in insights_data.get('insights', []):
        insight_type = insight.get('type', 'trend').lower() # Default to trend
        if insight_type in insights_by_type:
            insights_by_type[insight_type].append(insight)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("#### 🎯 Opportunities")
        if not insights_by_type['opportunity']: st.caption("None identified")
        for insight in insights_by_type['opportunity']:
             with st.container(): # No border needed if card class handles it
                 st.markdown(f"""
                 <div class="card insight-card insight-opportunity">
                     <h5>{insight.get('title', 'N/A')}</h5>
                     <p>{insight.get('description', 'N/A')}</p>
                     <small>Related: {', '.join(insight.get('related_competitors', ['N/A']))}</small>
                 </div>
                 """, unsafe_allow_html=True)
    with col2:
        st.markdown("#### ⚠️ Threats")
        if not insights_by_type['threat']: st.caption("None identified")
        for insight in insights_by_type['threat']:
             with st.container(): # No border needed if card class handles it
                 st.markdown(f"""
                 <div class="card insight-card insight-threat">
                     <h5>{insight.get('title', 'N/A')}</h5>
                     <p>{insight.get('description', 'N/A')}</p>
                     <small>Related: {', '.join(insight.get('related_competitors', ['N/A']))}</small>
                 </div>
                 """, unsafe_allow_html=True)
    with col3:
        st.markdown("#### 📈 Trends")
        if not insights_by_type['trend']: st.caption("None identified")
        for insight in insights_by_type['trend']:
             with st.container(): # No border needed if card class handles it
                 st.markdown(f"""
                 <div class="card insight-card insight-trend">
                     <h5>{insight.get('title', 'N/A')}</h5>
                     <p>{insight.get('description', 'N/A')}</p>
                     <small>Related: {', '.join(insight.get('related_competitors', ['N/A']))}</small>
                 </div>
                 """, unsafe_allow_html=True)

def display_deep_research(competitors: List[Dict[str, Any]], company_name: Optional[str]):
    st.markdown("### Deep Research Reports", unsafe_allow_html=True)

    if not competitors:
        st.warning("No competitors identified. Cannot start deep research.")
        return

    st.markdown("Select competitors and click 'Start Research' to generate detailed PDF reports.")

    selected_competitors_names = []
    # Display checkboxes and status
    st.markdown("#### Select & Monitor Research")
    with st.container(border=True):
        research_items_html = ""
        for competitor in competitors:
            comp_name = competitor['name']
            comp_id = competitor['id'] # Assuming ID is available
            is_selected = st.checkbox(
                f"Research {comp_name}",
                key=f"research_select_{comp_id}",
                value=st.session_state.research_selection.get(comp_name, False) # Persist checkbox state
            )
            st.session_state.research_selection[comp_name] = is_selected
            if is_selected:
                selected_competitors_names.append(comp_name)

            # Display Status & Download Button inline
            status = st.session_state.research_status.get(comp_name, "not_started")
            status_class = f"status-{status.replace('_', '')}" # e.g., status-notstarted
            status_text = status.replace("_", " ").title()

            col1, col2 = st.columns([3, 1]) # Columns for status/button alignment
            with col1:
                 st.markdown(f"<span class='status-badge {status_class}'>{status_text}</span>", unsafe_allow_html=True)
                 if status == "pending":
                     st.spinner("") # Small spinner next to pending status
            with col2:
                if status == "completed":
                    pdf_content = st.session_state.research_results.get(comp_name)
                    if pdf_content and isinstance(pdf_content, str) and not pdf_content.strip().startswith("## Error"):
                        try:
                            # Generate PDF on the fly for download
                            pdf_buffer = pdf_service.generate_single_report_pdf(
                                pdf_content,
                                f"{comp_name} - Competitive Analysis"
                            )
                            st.download_button(
                                label="⬇️ PDF",
                                data=pdf_buffer,
                                file_name=f"{comp_name}_Deep_Research.pdf",
                                mime="application/pdf",
                                key=f"download_{comp_id}",
                                help=f"Download {comp_name} report",
                                use_container_width=True
                            )
                        except Exception as pdf_e:
                            st.error(f"PDF Error: {pdf_e}", icon="📄")
                    elif pdf_content and isinstance(pdf_content, str): # It's an error markdown
                         st.error("Report Error", icon="⚠️")
                elif status == "error":
                     st.error("Failed", icon="❌")

            st.divider() # Separator between competitors


    if st.button("Start Deep Research", type="primary", disabled=not selected_competitors_names or st.session_state._research_running):
        if selected_competitors_names:
            st.session_state._research_running = True # Prevent multiple clicks
            count = 0
            for competitor in competitors:
                comp_name = competitor['name']
                if comp_name in selected_competitors_names:
                    # Only start if not already pending or completed
                    if st.session_state.research_status.get(comp_name) not in ["pending", "completed"]:
                        comp_desc = competitor.get('description')
                        print(f"Queueing background deep research for: {comp_name}")
                        run_in_background(
                            background_deep_research,
                            args=(comp_name, comp_desc, company_name)
                        )
                        count += 1
                    else:
                        st.write(f"Research for {comp_name} is already {st.session_state.research_status.get(comp_name)}.")

            if count > 0:
                st.success(f"Initiated deep research for {count} competitor(s). Monitor status above.")
            else:
                 st.warning("No new research tasks started. Selected competitors might already be processing or completed.")
            # Reset the running flag after a short delay to allow re-triggering if needed
            # This is a simplification; a better approach might track individual thread completion.
            time.sleep(2) # Give threads time to set status to pending
            st.session_state._research_running = False
            st.rerun() # Update UI immediately
        else:
            st.warning("Please select at least one competitor.")

# --- Main App Logic ---

st.title("🧠 Competitive Intelligence Agent")

# --- Company Input ---
with st.container():
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    col1, col2 = st.columns([3, 1])
    with col1:
        company_name_input = st.text_input(
            "Company to Analyze",
            placeholder="Enter company name (e.g., Microsoft, Apple, Tesla...)",
            label_visibility="collapsed",
            key="company_name_input_key" # Add key for potential updates
        )
    with col2:
        analyze_button = st.button("Analyze Company", type="primary", use_container_width=True)

    if analyze_button and company_name_input:
        st.session_state.company_name = company_name_input # Update canonical name
        # Reset states for new analysis
        st.session_state.company_data = None
        st.session_state.competitors_data = None
        st.session_state.news_data = {}
        st.session_state.insights_data = None
        st.session_state.research_status = {}
        st.session_state.research_results = {}
        st.session_state.research_selection = {}
        st.session_state.chat_messages = []
        st.session_state._news_loading = False
        st.session_state._insights_loading = False
        st.session_state._research_running = False
        st.session_state._rag_update_queued = False

        with st.spinner(f"Gathering intelligence on {st.session_state.company_name}... This may take a moment."):
            try:
                # --- Initial Synchronous Calls ---
                # 1. Analyze Company
                company_analysis = asyncio.run(gemini_service.analyze_company(st.session_state.company_name))
                st.session_state.company_data = company_analysis
                company_id = company_analysis.get('id', str(hash(st.session_state.company_name))) # Get ID or generate one

                # 2. Identify Competitors
                competitors_result = asyncio.run(gemini_service.identify_competitors(st.session_state.company_name))
                st.session_state.competitors_data = competitors_result
                competitor_list = competitors_result.get('competitors', [])
                competitor_ids = [c.get('id') for c in competitor_list if c.get('id')] # Assuming competitors have IDs

                # --- Trigger Background Tasks ---
                # 3. Fetch News (Background)
                if competitor_ids and BACKEND_AVAILABLE: # Check backend availability
                     print("Queueing background news fetch...")
                     run_in_background(background_fetch_news, args=(company_id, competitor_ids))
                     st.session_state._news_loading = True

                # 4. Generate Insights (Background - depends on competitors & news)
                # We trigger insights after news fetch completes (handled implicitly by UI checks)
                # OR trigger it here and let it wait if news isn't ready? Let's trigger later.

                # 5. Initial RAG Update (Background)
                if company_id and BACKEND_AVAILABLE:
                     print("Queueing initial RAG update...")
                     run_in_background(background_update_rag, args=(company_id,))

                # Rerun to reflect the initial data and start showing loading states
                st.rerun()

            except Exception as e:
                st.error(f"Analysis failed: {e}")
                # Reset states on failure
                st.session_state.company_data = None
                st.session_state.competitors_data = None

    elif analyze_button and not company_name_input:
        st.warning("Please enter a company name.")

    st.markdown('</div>', unsafe_allow_html=True)

# --- Display Main Content (Chat & Tabs) ---
if st.session_state.company_data and st.session_state.company_name:
    company_id = st.session_state.company_data.get('id', str(hash(st.session_state.company_name)))

    # --- RAG Chat Area ---
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    st.markdown(f"### Chat with AI about {st.session_state.company_name}")

    st.markdown('<div data-testid="chatScrollContainer">', unsafe_allow_html=True)
    # Display chat history
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    st.markdown('</div>', unsafe_allow_html=True)

    # Chat input
    if prompt := st.chat_input(f"Ask anything about {st.session_state.company_name}'s competitive landscape..."):
        # Add user message to history and display
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate and display AI response
        with st.chat_message("assistant"):
            with st.spinner("🧠 Thinking..."):
                try:
                    if BACKEND_AVAILABLE:
                        # Ensure RAG index is updated if needed (e.g., after research completes)
                        # The flag `_rag_update_queued` handles this trigger elsewhere
                        response = asyncio.run(rag_service.ask_question(prompt, company_id))
                    else:
                        response = "Backend services are unavailable."
                    st.markdown(response)
                    st.session_state.chat_messages.append({"role": "assistant", "content": response})
                    # Rerun needed to persist the full chat history correctly in some cases
                    # st.rerun() # Be careful with reruns inside loops/callbacks
                except Exception as e:
                    error_msg = f"An error occurred: {str(e)}"
                    st.error(error_msg)
                    st.session_state.chat_messages.append({"role": "assistant", "content": f"Error: Could not process request. {error_msg}"})
                    # st.rerun() # Rerun to show error message in history

    st.markdown('</div>', unsafe_allow_html=True) # Close chat-container

    # --- Data Tabs ---
    tab_titles = ["🏢 Company", "🎯 Competitors", "📰 News", "💡 Insights", "🔍 Deep Research"]
    tab1, tab2, tab3, tab4, tab5 = st.tabs(tab_titles)

    # Display toast notifications if any are pending
    display_toast_notifications()

    # Check if RAG update is queued and run it
    if st.session_state._rag_update_queued and BACKEND_AVAILABLE:
         run_in_background(background_update_rag, args=(company_id,))
         st.session_state._rag_update_queued = False # Mark as running/handled

    # --- Company Details Tab ---
    with tab1:
        display_company_details(st.session_state.company_data)

    # --- Competitors Tab ---
    with tab2:
        competitors = st.session_state.competitors_data.get('competitors', []) if st.session_state.competitors_data else []
        display_competitors(competitors)

    # --- News Tab ---
    with tab3:
        if st.session_state._news_loading:
            with st.spinner("Fetching latest news..."):
                st.empty() # Placeholder while spinner runs
                # Background task is already running, just wait visually
        else:
            # Trigger background fetch if data is empty and not loading
            if not st.session_state.news_data and not st.session_state._news_loading and st.session_state.competitors_data:
                 competitor_list = st.session_state.competitors_data.get('competitors', [])
                 competitor_ids = [c.get('id') for c in competitor_list if c.get('id')]
                 if competitor_ids and BACKEND_AVAILABLE:
                     print("Triggering news fetch from News Tab...")
                     run_in_background(background_fetch_news, args=(company_id, competitor_ids))
                     st.rerun() # Rerun to show the spinner
            elif st.session_state.news_data:
                 display_news(st.session_state.news_data)
            else:
                 st.info("News data is currently unavailable. Analysis might be in progress.")


    # --- Insights Tab ---
    with tab4:
        # Trigger insight generation if data is ready and insights aren't loaded/loading
        can_gen_insights = (st.session_state.competitors_data and st.session_state.news_data and
                            not st.session_state.insights_data and not st.session_state._insights_loading)

        if can_gen_insights and BACKEND_AVAILABLE:
            print("Triggering insights generation from Insights Tab...")
            run_in_background(background_generate_insights, args=(company_id, st.session_state.company_name))
            st.session_state._insights_loading = True
            st.rerun() # Show spinner

        if st.session_state._insights_loading:
             with st.spinner("Generating strategic insights..."):
                 st.empty()
        elif st.session_state.insights_data:
            display_insights(st.session_state.insights_data)
        else:
            st.info("Insights require competitor and news data. Please wait for them to load.")


    # --- Deep Research Tab ---
    with tab5:
        competitors = st.session_state.competitors_data.get('competitors', []) if st.session_state.competitors_data else []
        display_deep_research(competitors, st.session_state.company_name)

# --- Initial Welcome Message ---
else:
    st.markdown("""
    <div style="text-align: center; padding: 3rem 1rem;">
        <h2 style="color: #1E3A8A; font-weight: 600;">Welcome to the Competitive Intelligence Agent 🧠</h2>
        <p style="font-size: 1.1rem; color: #475569; max-width: 700px; margin: 1rem auto;">
            Enter a company name above to unlock powerful AI-driven insights:
        </p>
        <ul style="list-style: none; padding: 0; max-width: 500px; margin: 1.5rem auto; text-align: left; font-size: 1rem; color: #334155;">
            <li style="margin-bottom: 0.5rem;">✅ Analyze company details & industry</li>
            <li style="margin-bottom: 0.5rem;">🎯 Identify key competitors & analyze SWOT</li>
            <li style="margin-bottom: 0.5rem;">📰 Track competitor news & developments</li>
            <li style="margin-bottom: 0.5rem;">💡 Generate actionable strategic insights</li>
            <li style="margin-bottom: 0.5rem;">🔍 Conduct deep-dive research reports (PDF)</li>
            <li style="margin-bottom: 0.5rem;">💬 Chat with an AI assistant about the findings</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# --- Optional: Add a Footer ---
st.markdown("---")
st.markdown("<div style='text-align: center; font-size: 0.9rem; color: #64748B;'>Competitive Intelligence Agent v1.1</div>", unsafe_allow_html=True)