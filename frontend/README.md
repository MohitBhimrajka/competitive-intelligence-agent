# Competitive Intelligence Agent Frontend

This is the frontend for the Competitive Intelligence Agent application. It's built with React, TypeScript, and TailwindCSS.

## Key Components

### 1. Landing Page
- Company name input form
- Brief description of the application
- Call-to-action button to start analysis

### 2. Loading Page
- Animated loading indicator
- Real-time updates on the analysis progress
- Displays friendly message based on the user's company

### 3. Dashboard
- Overview of the company and its competitors
- Interactive competitor cards with strengths and weaknesses
- News articles about competitors
- AI-generated insights

### 4. Competitor Details
- Detailed view of each competitor
- Comprehensive news section
- Strengths and weaknesses analysis
- Related insights

### 5. News Section
- Latest news articles about competitors
- Article preview with source and date
- External links to full articles

### 6. Insights Section
- AI-generated strategic insights
- Categorized by opportunity, threat, or trend
- Related competitors for each insight

## File Structure

```
src/
├── api/               # API client for backend communication
├── assets/            # Static assets (images, icons)
├── components/        # Reusable UI components
│   ├── layout/        # Layout components
│   ├── common/        # Common UI elements
│   ├── dashboard/     # Dashboard-specific components
│   ├── competitors/   # Competitor-related components
│   └── insights/      # Insight-related components
├── contexts/          # React contexts for state management
├── hooks/             # Custom React hooks
├── lib/               # Utility libraries and helpers
├── pages/             # Main application pages
│   ├── LandingPage.tsx
│   ├── LoadingPage.tsx
│   ├── DashboardPage.tsx
│   └── CompetitorPage.tsx
├── types/             # TypeScript type definitions
└── utils/             # Utility functions
```

## API Integration

The frontend communicates with the backend through these API endpoints:

1. **Company Analysis**
   - `POST /api/company` - Submit company name and initiate analysis
   - `GET /api/company/{company_id}` - Get company details

2. **Competitor News**
   - `GET /api/news/competitor/{competitor_id}` - Get news for a specific competitor
   - `GET /api/news/company/{company_id}` - Get news for all competitors of a company

3. **Competitive Insights**
   - `GET /api/insights/company/{company_id}` - Get AI-generated insights for a company
   - `POST /api/insights/company/{company_id}/refresh` - Refresh insights

## Development

To start development:

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The application will be available at http://localhost:5173
