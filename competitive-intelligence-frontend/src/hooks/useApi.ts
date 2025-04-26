import axios, { AxiosInstance } from 'axios';

/**
 * Custom hook that provides an axios instance configured with baseURL from environment variables
 */
export const useApi = (): AxiosInstance => {
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:3000/api';
  
  const api = axios.create({
    baseURL: apiUrl,
    headers: {
      'Content-Type': 'application/json',
    },
  });
  
  // Add request interceptor for authentication if needed
  api.interceptors.request.use((config) => {
    // You can add auth token here if needed
    // const token = localStorage.getItem('token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  });
  
  // Add response interceptor for error handling
  api.interceptors.response.use(
    (response) => response,
    (error) => {
      // Global error handling
      console.error('API Error:', error);
      return Promise.reject(error);
    }
  );
  
  return api;
};

export default useApi; 