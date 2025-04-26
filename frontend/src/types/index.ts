// Company types
export interface Company {
  id: string;
  name: string;
  description: string | null;
  industry: string | null;
}

export interface CompanyResponse {
  id: string;
  name: string;
  description: string | null;
  industry: string | null;
  welcome_message: string;
}

// Competitor types
export interface Competitor {
  id: string;
  name: string;
  company_id: string;
  description: string | null;
  strengths: string[];
  weaknesses: string[];
}

export interface CompetitorsResponse {
  company_id: string;
  company_name: string;
  competitors: Competitor[];
}

// News types
export interface NewsArticle {
  title: string;
  source: string;
  url: string;
  published_at: string;
  content: string;
}

export interface CompetitorNewsResponse {
  competitor_id: string;
  competitor_name: string;
  articles: NewsArticle[];
}

export interface CompanyNewsResponse {
  [competitorName: string]: NewsArticle[];
}

// Insight types
export interface Insight {
  id: string;
  company_id: string;
  competitor_id: string | null;
  content: string;
  source: string;
}

export interface CompanyInsightsResponse {
  company_id: string;
  company_name: string;
  insights: Insight[];
}

export interface Document {
  id: number;
  competitor_id: number;
  title: string;
  file_path: string;
  document_type: string;
  created_at: string;
  processed: boolean;
}

export interface AnalysisResult {
  query: string;
  answer: string;
  sources: string[];
  timestamp: string;
}

export interface Notification {
  id: number;
  competitor_id: number;
  type: string;
  content: string;
  timestamp: string;
  sent: boolean;
}

export interface NotificationConfig {
  email: string;
  frequency: 'daily' | 'weekly';
  competitor_ids: number[];
}

export interface Trend {
  metric: string;
  trend: string;
  period: string;
  details: string;
}

export interface CompetitorInsights {
  competitor_id: number;
  insights: Insight[];
}

export interface CompetitorTrends {
  competitor_id: number;
  trends: Trend[];
} 