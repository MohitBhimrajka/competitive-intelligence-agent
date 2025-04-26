import { useEffect, useState } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { getCompanyDetails, getCompanyCompetitors, getCompanyInsights } from '../api/client';
import { CompanyResponse, CompetitorsResponse, CompanyInsightsResponse } from '../types';

const LoadingPage = () => {
  const { companyId } = useParams<{ companyId: string }>();
  const location = useLocation();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('Analyzing your company...');
  const [companyData, setCompanyData] = useState<CompanyResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // If we have state from navigation, use it directly
  useEffect(() => {
    if (location.state && location.state.companyName) {
      setCompanyData(location.state as CompanyResponse);
    } else if (companyId) {
      // Otherwise fetch from API
      getCompanyDetails(companyId)
        .then(data => {
          setCompanyData(data);
        })
        .catch(() => {
          setError('Unable to load company information. Please try again.');
        });
    } else {
      setError('Company ID is missing. Please go back and try again.');
    }
  }, [companyId, location]);

  // Simulate loading progress and check for data completion
  useEffect(() => {
    if (!companyId || error) return;

    let competitorsLoaded = false;
    let insightsLoaded = false;
    let timer: ReturnType<typeof setTimeout>;
    
    const checkDataReady = async () => {
      try {
        // Check if competitors are ready
        if (!competitorsLoaded) {
          try {
            await getCompanyCompetitors(companyId);
            competitorsLoaded = true;
            setStatus('Gathering news about competitors...');
            setProgress(50);
          } catch (error) {
            // If competitors are not ready yet, we'll try again
          }
        }
        
        // Once competitors are loaded, check for insights
        if (competitorsLoaded && !insightsLoaded) {
          try {
            await getCompanyInsights(companyId);
            insightsLoaded = true;
            setStatus('Analyzing competitive landscape...');
            setProgress(90);
          } catch (error) {
            // If insights are not ready yet, we'll try again
          }
        }
        
        // If all data is ready, complete loading
        if (competitorsLoaded && insightsLoaded) {
          setProgress(100);
          setStatus('Analysis complete!');
          // Navigate to dashboard after a brief delay
          setTimeout(() => {
            navigate(`/dashboard/${companyId}`);
          }, 1500);
          return true;
        }
        
        return false;
      } catch (error) {
        console.error('Error checking data:', error);
        return false;
      }
    };
    
    const incrementProgress = async () => {
      const isComplete = await checkDataReady();
      
      if (!isComplete) {
        // Only increment progress up to certain points based on stage
        if (!competitorsLoaded && progress < 40) {
          setProgress(prev => Math.min(prev + 0.5, 40));
        } else if (competitorsLoaded && !insightsLoaded && progress < 85) {
          setProgress(prev => Math.min(prev + 0.3, 85));
        }
        
        timer = setTimeout(incrementProgress, 500);
      } else {
        clearTimeout(timer);
      }
    };
    
    // Start the progress simulation
    timer = setTimeout(incrementProgress, 500);
    
    return () => {
      clearTimeout(timer);
    };
  }, [companyId, error, navigate]);

  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-4 bg-gray-50">
        <div className="w-full max-w-md p-8 bg-white rounded-lg shadow-lg text-center">
          <div className="text-red-500 text-xl mb-4">Error</div>
          <p className="text-gray-700 mb-6">{error}</p>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 bg-gradient-to-b from-blue-50 to-white">
      <div className="w-full max-w-md p-8 bg-white rounded-lg shadow-lg text-center">
        <h1 className="text-2xl font-bold text-gray-800 mb-6">
          Competitive Intelligence
        </h1>
        
        {companyData && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-blue-600 mb-2">
              {companyData.name}
            </h2>
            <p className="text-gray-600">{companyData.welcome_message}</p>
          </div>
        )}
        
        <div className="mb-6">
          <div className="w-full bg-gray-200 rounded-full h-3 mb-2">
            <div 
              className="bg-blue-600 h-3 rounded-full transition-all duration-300 ease-out"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <p className="text-sm text-gray-600">{status}</p>
        </div>
        
        {/* Loading animation */}
        <div className="flex justify-center mb-4">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
        
        <p className="text-gray-500 text-sm">
          This may take a minute as we gather and analyze the latest data about your competitors.
        </p>
      </div>
    </div>
  );
};

export default LoadingPage; 