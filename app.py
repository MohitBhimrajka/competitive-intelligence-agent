import streamlit as st
import streamlit_lottie as st_lottie
import streamlit_option_menu as st_menu
import streamlit_card as st_card
import streamlit_tags as st_tags
import plotly.graph_objects as go
import requests
import json
import asyncio
import time
from datetime import datetime
import os
from dotenv import load_dotenv
from backend.services.gemini_service import GeminiService
from backend.services.database import db
from backend.services.news_service import NewsService
from backend.services.pdf_service import PDFService
from backend.services.rag_service import rag_service

# Load environment variables
load_dotenv()

# Initialize services
gemini_service = GeminiService()
news_service = NewsService()
pdf_service = PDFService()

# Set page config
st.set_page_config(
    page_title="Competitive Intelligence Agent",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 0rem 0rem;
    }
    .stApp {
        background-color: #f5f7f9;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0066cc;
        color: white;
    }
    .company-card {
        padding: 20px;
        border-radius: 10px;
        background-color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .competitor-card {
        padding: 15px;
        border-radius: 8px;
        background-color: white;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    .news-card {
        padding: 12px;
        border-radius: 6px;
        background-color: white;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        margin-bottom: 10px;
    }
    .insight-card {
        padding: 15px;
        border-radius: 8px;
        background-color: white;
        border-left: 4px solid;
        margin-bottom: 15px;
    }
    .insight-opportunity {
        border-left-color: #28a745;
    }
    .insight-threat {
        border-left-color: #dc3545;
    }
    .insight-trend {
        border-left-color: #17a2b8;
    }
    .welcome-message {
        font-size: 1.2em;
        padding: 20px;
        border-radius: 10px;
        background-color: #e8f4ff;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'company_data' not in st.session_state:
    st.session_state.company_data = None
if 'competitors_data' not in st.session_state:
    st.session_state.competitors_data = None
if 'news_data' not in st.session_state:
    st.session_state.news_data = {}
if 'insights_data' not in st.session_state:
    st.session_state.insights_data = None
if 'research_status' not in st.session_state:
    st.session_state.research_status = {}
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 0

# Load Lottie animation
def load_lottie_url(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# Load animations
lottie_search = load_lottie_url('https://assets5.lottiefiles.com/packages/lf20_bXRG9q.json')
lottie_analysis = load_lottie_url('https://assets3.lottiefiles.com/packages/lf20_49rdyysj.json')

# Main app layout
st.title("🎯 Competitive Intelligence Agent")

# Company input section
with st.container():
    col1, col2 = st.columns([2, 1])
    with col1:
        company_name = st.text_input(
            "Enter Company Name",
            placeholder="e.g., Microsoft, Apple, Tesla...",
            help="Enter the name of the company you want to analyze"
        )
    with col2:
        if st.button("Analyze", type="primary", use_container_width=True):
            if company_name:
                with st.spinner("Analyzing company..."):
                    # Get company details
                    company_analysis = asyncio.run(gemini_service.analyze_company(company_name))
                    st.session_state.company_data = company_analysis
                    
                    # Get competitors
                    competitors_data = asyncio.run(gemini_service.identify_competitors(company_name))
                    st.session_state.competitors_data = competitors_data
                    
                    # Reset other data
                    st.session_state.news_data = {}
                    st.session_state.insights_data = None
                    st.session_state.research_status = {}
                    st.session_state.active_tab = 1  # Move to company details tab
                st.rerun()
            else:
                st.warning("Please enter a company name")

# Main content tabs
if st.session_state.company_data:
    tabs = st.tabs([
        "🏢 Company Details",
        "🎯 Competitors",
        "📰 News",
        "💡 Insights",
        "🔍 Deep Research",
        "💬 Chat"
    ])

    # Company Details Tab
    with tabs[0]:
        st.markdown(f"### {company_name}")
        with st.container():
            # Welcome message
            st.markdown(
                f"""<div class="welcome-message">
                    {st.session_state.company_data.get('welcome_message', 'Welcome!')}
                </div>""",
                unsafe_allow_html=True
            )
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### About")
                st.markdown(st.session_state.company_data.get('description', ''))
            with col2:
                st.markdown("#### Industry")
                st.markdown(st.session_state.company_data.get('industry', ''))

    # Competitors Tab
    with tabs[1]:
        if st.session_state.competitors_data:
            st.markdown("### Competitive Landscape")
            competitors = st.session_state.competitors_data.get('competitors', [])
            
            for competitor in competitors:
                with st.container():
                    st.markdown(
                        f"""<div class="competitor-card">
                            <h4>{competitor['name']}</h4>
                            <p>{competitor['description']}</p>
                            <h5>💪 Strengths</h5>
                            <ul>{''.join([f"<li>{s}</li>" for s in competitor['strengths']])}</ul>
                            <h5>⚠️ Weaknesses</h5>
                            <ul>{''.join([f"<li>{w}</li>" for w in competitor['weaknesses']])}</ul>
                        </div>""",
                        unsafe_allow_html=True
                    )

    # News Tab
    with tabs[2]:
        if st.session_state.competitors_data:
            st.markdown("### Latest News")
            competitors = st.session_state.competitors_data.get('competitors', [])
            
            # News filters
            days_back = st.slider("Days to look back", 1, 90, 30)
            
            for competitor in competitors:
                competitor_name = competitor['name']
                if competitor_name not in st.session_state.news_data:
                    with st.spinner(f"Fetching news for {competitor_name}..."):
                        news = asyncio.run(news_service.get_competitor_news(competitor_name, days_back))
                        st.session_state.news_data[competitor_name] = news
                
                st.markdown(f"#### 📰 {competitor_name}")
                news_items = st.session_state.news_data.get(competitor_name, [])
                
                if news_items:
                    for article in news_items:
                        with st.container():
                            st.markdown(
                                f"""<div class="news-card">
                                    <h5>{article['title']}</h5>
                                    <p><small>Source: {article['source']} | {article.get('publishedAt', 'N/A')}</small></p>
                                    <p>{article['content'][:200]}...</p>
                                    {f'<a href="{article["url"]}" target="_blank">Read more</a>' if article.get('url') else ''}
                                </div>""",
                                unsafe_allow_html=True
                            )
                else:
                    st.info(f"No recent news found for {competitor_name}")

    # Insights Tab
    with tabs[3]:
        if st.session_state.competitors_data and st.session_state.news_data:
            if not st.session_state.insights_data:
                with st.spinner("Generating insights..."):
                    # Prepare news context
                    news_data = {}
                    for comp_name, articles in st.session_state.news_data.items():
                        news_data[comp_name] = articles[:3]  # Use top 3 articles per competitor
                    
                    insights = asyncio.run(gemini_service.generate_insights(
                        company_name,
                        st.session_state.competitors_data,
                        news_data
                    ))
                    st.session_state.insights_data = insights

            if st.session_state.insights_data:
                st.markdown("### Strategic Insights")
                
                # Group insights by type
                insights_by_type = {
                    "opportunity": [],
                    "threat": [],
                    "trend": []
                }
                
                for insight in st.session_state.insights_data.get('insights', []):
                    insights_by_type[insight['type']].append(insight)
                
                # Display insights by type
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("#### 🎯 Opportunities")
                    for insight in insights_by_type['opportunity']:
                        st.markdown(
                            f"""<div class="insight-card insight-opportunity">
                                <h5>{insight['title']}</h5>
                                <p>{insight['description']}</p>
                                <p><small>Related: {', '.join(insight['related_competitors'])}</small></p>
                            </div>""",
                            unsafe_allow_html=True
                        )
                
                with col2:
                    st.markdown("#### ⚠️ Threats")
                    for insight in insights_by_type['threat']:
                        st.markdown(
                            f"""<div class="insight-card insight-threat">
                                <h5>{insight['title']}</h5>
                                <p>{insight['description']}</p>
                                <p><small>Related: {', '.join(insight['related_competitors'])}</small></p>
                            </div>""",
                            unsafe_allow_html=True
                        )
                
                with col3:
                    st.markdown("#### 📈 Trends")
                    for insight in insights_by_type['trend']:
                        st.markdown(
                            f"""<div class="insight-card insight-trend">
                                <h5>{insight['title']}</h5>
                                <p>{insight['description']}</p>
                                <p><small>Related: {', '.join(insight['related_competitors'])}</small></p>
                            </div>""",
                            unsafe_allow_html=True
                        )

    # Deep Research Tab
    with tabs[4]:
        if st.session_state.competitors_data:
            st.markdown("### Deep Research")
            
            competitors = st.session_state.competitors_data.get('competitors', [])
            selected_competitors = st.multiselect(
                "Select competitors for deep research",
                options=[comp['name'] for comp in competitors],
                format_func=lambda x: x
            )
            
            if selected_competitors:
                if st.button("Start Deep Research", type="primary"):
                    for comp_name in selected_competitors:
                        if comp_name not in st.session_state.research_status:
                            st.session_state.research_status[comp_name] = "pending"
                            
                            # Get competitor description
                            comp_desc = next(
                                (c['description'] for c in competitors if c['name'] == comp_name),
                                None
                            )
                            
                            # Start research in background
                            with st.spinner(f"Researching {comp_name}..."):
                                research_data = asyncio.run(
                                    gemini_service.deep_research_competitor(
                                        comp_name,
                                        comp_desc,
                                        company_name
                                    )
                                )
                                if research_data:
                                    st.session_state.research_status[comp_name] = "completed"
                                    
                                    # Generate PDF
                                    pdf_buffer = pdf_service.generate_single_report_pdf(
                                        research_data.get('markdown', ''),
                                        f"{comp_name} - Competitive Analysis"
                                    )
                                    
                                    # Display download button
                                    st.download_button(
                                        f"Download {comp_name} Report",
                                        pdf_buffer,
                                        file_name=f"{comp_name}_analysis.pdf",
                                        mime="application/pdf"
                                    )
                                else:
                                    st.session_state.research_status[comp_name] = "error"
            
            # Display research status
            if st.session_state.research_status:
                st.markdown("#### Research Status")
                for comp_name, status in st.session_state.research_status.items():
                    status_color = {
                        "pending": "🟡",
                        "completed": "🟢",
                        "error": "🔴"
                    }.get(status, "⚪")
                    st.markdown(f"{status_color} {comp_name}: {status.title()}")

    # Chat Tab
    with tabs[5]:
        st.markdown("### Chat with AI Assistant")
        
        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat input
        if prompt := st.chat_input("Ask about the competitive landscape..."):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generate AI response using RAG
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        # First, ensure the RAG index is up to date
                        company_id = st.session_state.company_data.get('id')
                        if company_id:
                            # Create async function for chat processing
                            async def process_chat():
                                # Update/create RAG index if needed
                                await rag_service.update_rag_index(company_id)
                                
                                # Get response using RAG
                                response = await rag_service.ask_question(prompt, company_id)
                                return response
                            
                            # Execute async function
                            response = asyncio.run(process_chat())
                            st.markdown(response)
                            
                            # Add assistant response to chat history
                            st.session_state.messages.append(
                                {"role": "assistant", "content": response}
                            )
                        else:
                            st.error("Please analyze a company first before using the chat feature.")
                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")

else:
    # Display welcome message when no company is selected
    st.markdown("""
    ### Welcome to Competitive Intelligence Agent! 🎯
    
    Get started by entering a company name above to:
    - 🏢 Analyze company details
    - 🎯 Identify key competitors
    - 📰 Track competitor news
    - 💡 Generate strategic insights
    - 🔍 Conduct deep research
    - 💬 Chat with AI assistant
    """)