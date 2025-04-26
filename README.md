# Competitive Intelligence Agent

A powerful AI-powered competitive intelligence platform that automates competitor monitoring and analysis.

## Features

- Company analysis using Google Gemini API
- Automatic competitor identification
- Real-time news gathering about competitors
- AI-powered competitive insights generation
- Interactive dashboards with competitor analysis
- User-friendly interface

## Tech Stack

### Backend
- FastAPI
- Google Gemini API for AI processing
- News API for competitor news
- Python 3.9+
- In-memory database (can be upgraded to PostgreSQL)

### Frontend
- TypeScript
- Vite
- React
- TailwindCSS

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

### Frontend Setup
```bash
cd frontend
npm install

# Create a .env file with:
VITE_API_URL=http://localhost:8000

# Start the development server
npm run dev
```

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