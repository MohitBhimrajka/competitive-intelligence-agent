import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { analyzeCompany } from '../api/client';

const LandingPage = () => {
  const [companyName, setCompanyName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!companyName.trim()) {
      setError('Please enter your company name');
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await analyzeCompany(companyName);
      // Navigate to loading page with company ID
      navigate(`/loading/${response.id}`, { 
        state: { 
          companyName: response.name,
          companyId: response.id,
          welcomeMessage: response.welcome_message
        } 
      });
    } catch (err) {
      console.error('Error analyzing company:', err);
      setError('Failed to analyze company. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white flex flex-col items-center justify-center p-4">
      <div className="max-w-3xl w-full bg-white rounded-xl shadow-lg p-8 md:p-12">
        <h1 className="text-3xl md:text-4xl font-bold text-blue-800 mb-4 text-center">
          Competitive Intelligence Agent
        </h1>
        
        <p className="text-gray-600 mb-8 text-center">
          Get AI-powered insights about your competitors in seconds. We'll analyze your market, 
          identify key competitors, gather the latest news, and provide strategic insights.
        </p>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <label htmlFor="companyName" className="block text-sm font-medium text-gray-700">
              Your Company Name
            </label>
            <input
              type="text"
              id="companyName"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="Enter your company name"
              className="w-full px-4 py-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isLoading}
            />
            {error && <p className="text-red-500 text-sm">{error}</p>}
          </div>
          
          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-md transition duration-200 disabled:bg-blue-400"
          >
            {isLoading ? 'Analyzing...' : 'Get Competitive Analysis'}
          </button>
        </form>
        
        <div className="mt-10 pt-6 border-t border-gray-200">
          <p className="text-sm text-gray-500 text-center">
            We use Google Gemini AI and News API to gather and analyze information about your competitors.
            All data is processed securely.
          </p>
        </div>
      </div>
    </div>
  );
};

export default LandingPage; 