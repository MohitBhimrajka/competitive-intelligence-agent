import React, { useEffect, Suspense, lazy } from 'react';
import { useParams } from 'react-router-dom';
import { 
  Box, 
  Grid, 
  Heading, 
  Text, 
  Spinner, 
  Center
} from '@chakra-ui/react';
import { motion } from 'framer-motion';
import { useColorModeValue } from '@chakra-ui/color-mode';

import DashboardLayout from '../components/layout/DashboardLayout';
import AnimatedCard from '../components/ui/AnimatedCard';
import { useAppDispatch, useAppSelector } from '../state/store';
import { fetchCompanyData } from '../state/store';
import { RootState } from '../state/store';

// Lazy-load the 3D visualization component
const DataVisualization3D = lazy(() => import('../components/viz/DataVisualization3D'));

interface Competitor {
  id: string;
  name: string;
  industry: string;
  relationshipStrength?: number;
}

// Placeholder section components (replace with actual components)
const CompetitorSectionAnimated = ({ competitors }: { competitors: Competitor[] }) => (
  <AnimatedCard delay={0.1}>
    <Box
      bg={useColorModeValue('white', 'gray.800')}
      p={6}
      borderRadius="lg"
      boxShadow="md"
      mb={6}
    >
      <Heading size="md" mb={4}>Competitors</Heading>
      {competitors.length > 0 ? (
        <Box>
          {competitors.map((competitor, index) => (
            <Box key={index} p={3} borderWidth="1px" borderRadius="md" mb={2}>
              <Text fontWeight="bold">{competitor.name}</Text>
              <Text fontSize="sm">{competitor.industry}</Text>
            </Box>
          ))}
        </Box>
      ) : (
        <Text>No competitor data available</Text>
      )}
    </Box>
  </AnimatedCard>
);

const NewsSectionAnimated = ({ news }: { news: any[] }) => (
  <AnimatedCard delay={0.2}>
    <Box
      bg={useColorModeValue('white', 'gray.800')}
      p={6}
      borderRadius="lg"
      boxShadow="md"
      mb={6}
    >
      <Heading size="md" mb={4}>Latest News</Heading>
      {news.length > 0 ? (
        <Box>
          {news.map((item, index) => (
            <Box key={index} p={3} borderWidth="1px" borderRadius="md" mb={2}>
              <Text fontWeight="bold">{item.title}</Text>
              <Text fontSize="sm">{item.source} • {new Date(item.date).toLocaleDateString()}</Text>
              <Text mt={2}>{item.summary}</Text>
            </Box>
          ))}
        </Box>
      ) : (
        <Text>No news data available</Text>
      )}
    </Box>
  </AnimatedCard>
);

const InsightsSectionAnimated = ({ insights }: { insights: any[] }) => (
  <AnimatedCard delay={0.3}>
    <Box
      bg={useColorModeValue('white', 'gray.800')}
      p={6}
      borderRadius="lg"
      boxShadow="md"
      mb={6}
    >
      <Heading size="md" mb={4}>Market Insights</Heading>
      {insights.length > 0 ? (
        <Box>
          {insights.map((insight, index) => (
            <Box 
              key={index} 
              p={3} 
              borderWidth="1px" 
              borderRadius="md" 
              mb={2}
              borderLeftWidth="4px"
              borderLeftColor={
                insight.severity === 'high' ? 'red.400' :
                insight.severity === 'medium' ? 'yellow.400' : 'green.400'
              }
            >
              <Text fontWeight="bold">{insight.title}</Text>
              <Text fontSize="sm">
                {insight.category.charAt(0).toUpperCase() + insight.category.slice(1)} • 
                {new Date(insight.date).toLocaleDateString()}
              </Text>
              <Text mt={2}>{insight.description}</Text>
            </Box>
          ))}
        </Box>
      ) : (
        <Text>No insights data available</Text>
      )}
    </Box>
  </AnimatedCard>
);

const ChatSection = () => (
  <AnimatedCard delay={0.4}>
    <Box
      bg={useColorModeValue('white', 'gray.800')}
      p={6}
      borderRadius="lg"
      boxShadow="md"
    >
      <Heading size="md" mb={4}>AI Assistant</Heading>
      <Text>Ask questions about the competitive landscape...</Text>
      
      {/* Placeholder for chat interface */}
      <Box 
        mt={4}
        p={4}
        borderWidth="1px"
        borderRadius="md"
        minHeight="200px"
        display="flex"
        alignItems="center"
        justifyContent="center"
      >
        <Text color="gray.500">Chat interface coming soon</Text>
      </Box>
    </Box>
  </AnimatedCard>
);

const CompanyDashboardPage = () => {
  const { companyId = '' } = useParams<{ companyId: string }>();
  const dispatch = useAppDispatch();
  
  // Get company data from the store
  const { 
    companyDetails, 
    competitors, 
    news, 
    insights, 
    loading,
    error 
  } = useAppSelector((state: RootState) => state.app);
  
  // Fetch company data when the component mounts
  useEffect(() => {
    if (companyId) {
      dispatch(fetchCompanyData(companyId));
    }
  }, [companyId, dispatch]);
  
  // Show loading state if any data is loading
  const isLoading = loading.companyDetails || loading.competitors || loading.news || loading.insights;
  
  if (error) {
    return (
      <DashboardLayout title="Error">
        <Center height="50vh">
          <Box textAlign="center">
            <Heading size="md" color="red.500" mb={4}>Error Loading Data</Heading>
            <Text>{error}</Text>
          </Box>
        </Center>
      </DashboardLayout>
    );
  }
  
  if (isLoading || !companyDetails) {
    return (
      <DashboardLayout title="Loading...">
        <Center height="50vh">
          <Spinner size="xl" color="teal.500" />
        </Center>
      </DashboardLayout>
    );
  }
  
  return (
    <DashboardLayout title={companyDetails.name}>
      {/* Dashboard content */}
      <Grid
        templateColumns={{ base: "1fr", lg: "1fr 1fr" }}
        gap={6}
      >
        {/* Company Overview Section */}
        <Box gridColumn={{ base: "1", lg: "1 / -1" }}>
          <AnimatedCard>
            <Box
              bg={useColorModeValue('white', 'gray.800')}
              p={6}
              borderRadius="lg"
              boxShadow="md"
              mb={6}
            >
              <Heading mb={4}>{companyDetails.name}</Heading>
              <Text fontSize="lg" mb={2}>{companyDetails.industry}</Text>
              <Text>{companyDetails.description}</Text>
              
              {/* 3D Visualization with Suspense */}
              <Box height="300px" mt={6}>
                <Suspense fallback={
                  <Center height="100%">
                    <Spinner size="lg" color="teal.500" />
                  </Center>
                }>
                  <DataVisualization3D 
                    data={[
                      { id: '1', label: companyDetails.name, value: 1, color: 'teal.500' },
                      ...competitors.map((comp: Competitor, index: number) => ({
                        id: comp.id,
                        label: comp.name,
                        value: comp.relationshipStrength || 0.5,
                        color: index % 2 === 0 ? 'blue.500' : 'purple.500'
                      }))
                    ]}
                    title="Competitive Landscape"
                  />
                </Suspense>
              </Box>
            </Box>
          </AnimatedCard>
        </Box>
        
        {/* Competitors Section - Left Column */}
        <Box>
          <CompetitorSectionAnimated competitors={competitors} />
          <InsightsSectionAnimated insights={insights} />
        </Box>
        
        {/* News & Chat Section - Right Column */}
        <Box>
          <NewsSectionAnimated news={news} />
          <ChatSection />
        </Box>
      </Grid>
    </DashboardLayout>
  );
};

export default CompanyDashboardPage; 