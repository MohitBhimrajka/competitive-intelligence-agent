import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import LandingPage from './pages/LandingPage';
import LoadingPage from './pages/LoadingPage';
// These would be implemented for a full application:
// import DashboardPage from './pages/DashboardPage';
// import CompetitorPage from './pages/CompetitorPage';

// Create a React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/loading/:companyId" element={<LoadingPage />} />
          
          {/* Dashboard routes - would be implemented for a full application */}
          <Route path="/dashboard/:companyId" element={<div className="p-8">Dashboard would show here with competitor data and insights</div>} />
          <Route path="/competitors/:competitorId" element={<div className="p-8">Competitor details would show here</div>} />
          
          {/* Fallback route */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
