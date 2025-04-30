# Competitive Intelligence Agent - Streamlit App

A modern Streamlit interface for the Competitive Intelligence Agent backend that provides comprehensive analysis of companies and their competitive landscape.

## Features

- **Company Analysis**: Enter any company name to initiate a comprehensive analysis of its competitive landscape.
- **Competitor Identification**: Automatically identifies and analyzes key competitors.
- **News Monitoring**: Collects and displays relevant news articles about the company and its competitors.
- **Strategic Insights**: Generates AI-powered insights about market position and competitive advantages.
- **Deep Research**: Request detailed research reports on specific competitors.
- **RAG-Powered Chat**: Ask natural language questions about the company and its competitors.

## Screenshots

![Dashboard Overview](screenshots/dashboard.png)
![Competitor Analysis](screenshots/competitors.png)
![Deep Research](screenshots/deep_research.png)

## Prerequisites

- Python 3.8+
- Streamlit
- Running Competitive Intelligence Agent backend API
- Internet connection

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/competitive-intelligence-agent.git
   cd competitive-intelligence-agent
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Make sure the backend API is running:
   ```
cd backend
python -m uvicorn main:app --reload
   ```

4. Run the Streamlit app:
   ```
streamlit run app.py
```

## Usage

1. Open the app in your browser (typically http://localhost:8501).
2. Enter a company name in the input field (e.g., "Tesla", "Airbnb", "Netflix").
3. Click "Analyze" to initiate the competitive intelligence analysis.
4. Wait for the analysis to complete (this may take a few moments).
5. Explore the different tabs to view:
   - Overview dashboard with key metrics
   - Detailed competitor profiles with strengths and weaknesses
   - News monitoring for relevant articles
   - AI-generated strategic insights
   - Deep research reports on competitors
   - Interactive chat for asking questions about the data

## Configuration

The app connects to the backend API at `http://localhost:8000` by default. If your backend is running on a different address, modify the `API_BASE_URL` variable in `app.py`.

## How It Works

1. **Data Collection**: The app communicates with the backend API to trigger data collection and analysis for the specified company.
2. **Real-Time Updates**: The app polls the API for updates as analysis progresses through different stages.
3. **Interactive Display**: Once data is collected, it is presented in an interactive dashboard with visualizations and filtering options.
4. **RAG Chat**: The app uses a Retrieval-Augmented Generation system to answer questions based on the collected competitive intelligence data.

## Deep Research Feature

The Deep Research feature allows you to generate comprehensive reports on specific competitors:

1. Navigate to the "Deep Research" tab
2. Select one or more competitors from the dropdown
3. Click "Start Deep Research" to initiate the process
4. Once complete, you can:
   - View the research directly in the app
   - Download individual PDF reports
   - Download a combined PDF report for multiple competitors

## Troubleshooting

- **API Connection Error**: Make sure the backend API is running at the correct address.
- **Slow Analysis**: The initial analysis involves multiple API calls and data processing. Wait for all stages to complete.
- **Empty Results**: If certain sections show no data, try refreshing using the "Refresh Data" button.

## Deploying on Render

This application is configured for easy deployment on Render.com using the included `render.yaml` file which sets up both the backend API and Streamlit frontend.

### Prerequisites for Deployment

1. A [Render account](https://render.com)
2. Your repository pushed to GitHub
3. API keys for services (see Environment Variables below)

### Deployment Steps

1. Push your code to GitHub:
   ```
   git add .
   git commit -m "Prepare for Render deployment"
   git push
   ```

2. In Render dashboard, click "New" and select "Blueprint"

3. Connect your GitHub repository

4. Render will automatically detect the `render.yaml` file and configure the services

5. Review the configuration and click "Apply"

6. Add all required environment variables (described below) in the Render dashboard

7. Wait for both services to deploy (this may take a few minutes)

8. Once deployed, your application will be available at the Render-provided URLs

### Environment Variables

The following environment variables should be set in the Render dashboard:

#### Supervity API Credentials
The application uses Supervity for email reports and document processing.

- `SUPERVITY_API_TOKEN`: Your Supervity API token
- `SUPERVITY_API_ORG`: Your Supervity organization ID
- `SUPERVITY_AGENT_ID`: Your Supervity agent ID
- `SUPERVITY_SKILL_ID`: Your Supervity skill ID
- `SUPERVITY_EMAIL_AGENT_ID`: Agent ID for email functionality
- `SUPERVITY_EMAIL_SKILL_ID`: Skill ID for email functionality

#### Google Services
The application uses Google services for AI, Drive integration, and more.

- `GOOGLE_API_KEY`: Your Google API key for Gemini AI models
- `GOOGLE_SERVICE_ACCOUNT_KEY`: JSON credentials for Google Drive service
- `GOOGLE_DRIVE_FOLDER_ID`: (Optional) Folder ID in Google Drive to save reports

#### News API
- `NEWS_API_KEY`: API key from newsapi.org for fetching company news

See `env.example` for a complete list of available environment variables.

## License

[MIT License](LICENSE) 