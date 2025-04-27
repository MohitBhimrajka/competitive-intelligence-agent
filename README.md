# Competitive Intelligence Agent

A powerful AI-powered competitive intelligence platform that automates competitor monitoring and analysis.

## Features

- Company analysis using Google Gemini API
- Automatic competitor identification
- Real-time news gathering about competitors
- AI-powered competitive insights generation
- Interactive dashboards with competitor analysis
- User-friendly interface

## New Features

### Deep Competitor Research
Generate comprehensive, detailed research reports about competitors using a powerful AI model.

- **Trigger research**: Send a POST request to `/api/competitor/{competitor_id}/deep-research`
- **Check status**: The competitors list endpoint will include `deep_research_status` (not_started, pending, completed, error)
- **View report**: Access the markdown content from the competitors list endpoint in the `deep_research_markdown` field
- **Download as PDF**: GET `/api/competitor/{competitor_id}/deep-research/download` returns a downloadable PDF

### RAG Chat Interface
Ask questions about your competitors and get answers based on all available data.

- **Send queries**: POST to `/api/chat/{company_id}` with a JSON body containing a `query` field
- **Example**: `{ "query": "What are the strengths of Competitor X?" }`
- **RAG-powered**: Uses embeddings and semantic search to find relevant information across all company data, deep research reports, news, and insights

### Streamlit Frontend (New!)
A simpler, Python-based frontend alternative using Streamlit.

- **Quick setup**: Fewer dependencies and faster to deploy
- **All features**: Supports the same functionality as the React frontend
- **Simplified UI**: Clean, functional interface with tabbed navigation

## Tech Stack

### Backend
- Python 3.11 or higher
- FastAPI
- LangChain
- Google Gemini API
- News API

### Frontend Options

#### Streamlit Frontend (Alternative)
- Streamlit
- Pandas
- Python Requests

## Installation

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Set up your Google API key with a `.env` file:
```
GOOGLE_API_KEY=your_api_key_here
NEWS_API_KEY=your_news_api_key_here
```

3. Run the application:
```bash
cd backend
python main.py
```

The server will be available at http://localhost:8000.

## API Usage

1. Create/analyze a company:
   - POST `/api/company` with body `{"name": "Apple"}`
   - Returns a company ID and kicks off background processing

2. Monitor results:
   - GET `/api/company/{company_id}` - Company details
   - GET `/api/company/{company_id}/competitors` - Competitor analysis
   - GET `/api/news/company/{company_id}` - News articles

3. Use new features:
   - For any competitor, trigger deep research with POST `/api/competitor/{competitor_id}/deep-research`
   - Ask questions with POST `/api/chat/{company_id}` and body `{"query": "What are the main competitors of this company?"}`

## System Architecture

- **FastAPI Backend**: Main API application with routers for various features
- **In-Memory Database**: For demo purposes, data is stored in-memory (can be replaced with proper database)
- **Google Gemini Models**: Powers analysis, deep research (Pro model), and chat functionality
- **RAG System**: Enables querying across all collected data using semantic search

## Architecture

The application follows this workflow:
1. User enters their company name on the landing page
2. Backend analyzes the company using Gemini API
3. Competitors are automatically identified
4. News about competitors is gathered through News API
5. AI generates insights based on competitor analysis and news
6. All information is displayed on a dashboard

## Required API Keys

To run this application, you will need to obtain the following API keys:

1. **Google Gemini API Key**
   - Go to [Google AI Studio](https://ai.google.dev/)
   - Sign up or sign in to your Google account
   - Create a new API key

2. **News API Key**
   - Go to [News API](https://newsapi.org/)
   - Sign up for a free API key
   - Copy your API key from the dashboard

## Setup

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt

# Create a .env file with:
GOOGLE_API_KEY=your-google-api-key
NEWS_API_KEY=your-news-api-key

# Start the server
python -m uvicorn main:app --reload
# Or use the provided start script
chmod +x start.sh
./start.sh
```

### Frontend Setup Options

#### Option 1: React Frontend
```bash
cd frontend
npm install

# Create a .env file with:
VITE_API_URL=http://localhost:8000

# Start the development server
npm run dev
```

#### Option 2: Streamlit Frontend (New!)
```bash
cd frontend_streamlit
pip install -r requirements.txt

# Start the Streamlit app
streamlit run app.py
```

The Streamlit interface will be available at http://localhost:8501.

## API Endpoints

### Company Endpoints
- `POST /api/company` - Submit company name and initiate analysis
- `GET /api/company/{company_id}` - Get company details
- `GET /api/company/{company_id}/competitors` - Get identified competitors for a company

### News Endpoints
- `GET /api/news/competitor/{competitor_id}` - Get news for a specific competitor
- `GET /api/news/company/{company_id}` - Get news for all competitors of a company

### Insights Endpoints
- `GET /api/insights/company/{company_id}` - Get AI-generated insights for a company
- `POST /api/insights/company/{company_id}/refresh` - Refresh insights

## Troubleshooting

### API Key Issues
- If you get "API key not found" errors, make sure your .env file is in the correct location and contains the right API keys
- For Gemini API issues, verify your API key is active and has the necessary permissions

### Timeout Issues
- If insights generation takes too long, it might be due to API rate limits. Try again after a few minutes.

## License

MIT 