import axios from 'axios';
import type { 
  CompanyResponse, 
  CompetitorsResponse, 
  CompetitorNewsResponse, 
  CompanyNewsResponse, 
  CompanyInsightsResponse 
} from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Company API calls
export const analyzeCompany = async (companyName: string): Promise<CompanyResponse> => {
  const response = await apiClient.post('/api/company', { name: companyName });
  return response.data;
};

export const getCompanyDetails = async (companyId: string): Promise<CompanyResponse> => {
  const response = await apiClient.get(`/api/company/${companyId}`);
  return response.data;
};

// Competitors API calls - Note: In our backend this is handled by the company router
export const getCompanyCompetitors = async (companyId: string): Promise<CompetitorsResponse> => {
  // This endpoint doesn't exist in our backend yet, for now we can mock it
  // In a full implementation, we would need to add this endpoint
  // For now, this will likely fail and be handled by the error logic in LoadingPage
  const response = await apiClient.get(`/api/company/${companyId}/competitors`);
  return response.data;
};

// News API calls
export const getCompetitorNews = async (competitorId: string): Promise<CompetitorNewsResponse> => {
  const response = await apiClient.get(`/api/news/competitor/${competitorId}`);
  return response.data;
};

export const getCompanyCompetitorsNews = async (companyId: string): Promise<CompanyNewsResponse> => {
  const response = await apiClient.get(`/api/news/company/${companyId}`);
  return response.data;
};

// Insights API calls
export const getCompanyInsights = async (companyId: string): Promise<CompanyInsightsResponse> => {
  const response = await apiClient.get(`/api/insights/company/${companyId}`);
  return response.data;
};

export const refreshCompanyInsights = async (companyId: string): Promise<CompanyInsightsResponse> => {
  const response = await apiClient.post(`/api/insights/company/${companyId}/refresh`);
  return response.data;
};

// Add request interceptor for authentication if needed
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
); 