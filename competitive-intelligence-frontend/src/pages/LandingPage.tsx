import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Box, 
  Flex, 
  Heading, 
  Text, 
  Input, 
  Button, 
  VStack
} from '@chakra-ui/react';
import { motion } from 'framer-motion';
import { FormControl, FormLabel, FormErrorMessage } from '@chakra-ui/form-control';
import { useColorModeValue } from '@chakra-ui/color-mode';

import ThreeCanvas from '../three/ThreeCanvas';
import SceneSetup3D from '../three/SceneSetup3D';
import ParticleBackground3D from '../three/ParticleBackground3D';
import GlassmorphicContainer from '../components/ui/GlassmorphicContainer';
import HoverEffectButton from '../components/ui/HoverEffectButton';
import AnimatedCard from '../components/ui/AnimatedCard';
import { useAppDispatch } from '../state/store';
import { setCompanyId } from '../state/store';

// LandingHero3D component for the hero section
const LandingHero3D: React.FC = () => {
  return (
    <>
      <SceneSetup3D>
        <ParticleBackground3D 
          count={2000} 
          color={useColorModeValue('#3182CE', '#4FD1C5')} 
          radius={2}
        />
      </SceneSetup3D>
    </>
  );
};

// CompanyInputForm component
const CompanyInputForm: React.FC = () => {
  const [company, setCompany] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const dispatch = useAppDispatch();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Basic validation
    if (!company.trim()) {
      setError('Please enter a company name');
      return;
    }
    
    // Clear any errors
    setError('');
    
    // Set the company ID in the store
    const formattedCompanyId = encodeURIComponent(company.trim().toLowerCase());
    dispatch(setCompanyId(formattedCompanyId));
    
    // Navigate to the loading page
    navigate(`/loading/${formattedCompanyId}`);
  };

  return (
    <form onSubmit={handleSubmit}>
      <VStack gap={6} align="stretch">
        <FormControl isInvalid={!!error}>
          <FormLabel>Enter a company name</FormLabel>
          <Input
            placeholder="e.g. Tesla, Apple, Microsoft"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            size="lg"
            bg={useColorModeValue('white', 'gray.800')}
            _focus={{ borderColor: 'teal.400' }}
          />
          {error && <FormErrorMessage>{error}</FormErrorMessage>}
        </FormControl>
        
        <HoverEffectButton
          type="submit"
          variant="primary"
          className="text-lg py-6"
        >
          Analyze Competitive Landscape
        </HoverEffectButton>
      </VStack>
    </form>
  );
};

// Main LandingPage component
const LandingPage: React.FC = () => {
  const bgGradient = useColorModeValue(
    'linear(to-r, blue.50, teal.50)',
    'linear(to-r, gray.900, blue.900)'
  );

  return (
    <Box
      position="relative"
      minH="100vh"
      bgGradient={bgGradient}
      overflow="hidden"
    >
      {/* 3D Canvas Background */}
      <Box
        position="absolute"
        top={0}
        left={0}
        right={0}
        bottom={0}
        zIndex={0}
      >
        <ThreeCanvas>
          <LandingHero3D />
        </ThreeCanvas>
      </Box>
      
      {/* Content */}
      <Flex
        direction="column"
        align="center"
        justify="center"
        minH="100vh"
        position="relative"
        zIndex={1}
        p={4}
      >
        <VStack gap={12} maxW="1000px" textAlign="center">
          {/* Hero Text */}
          <AnimatedCard delay={0.2}>
            <Heading 
              as="h1" 
              size="2xl" 
              bgGradient="linear(to-r, teal.400, blue.500)" 
              bgClip="text"
              mb={4}
            >
              Competitive Intelligence Platform
            </Heading>
            <Text 
              fontSize="xl" 
              color={useColorModeValue('gray.600', 'gray.300')}
              maxW="800px"
            >
              Analyze market positioning, competitor strategies, and industry insights
              with our AI-powered intelligence platform.
            </Text>
          </AnimatedCard>
          
          {/* Form Container */}
          <AnimatedCard delay={0.4}>
            <GlassmorphicContainer maxW="500px" w="100%">
              <CompanyInputForm />
            </GlassmorphicContainer>
          </AnimatedCard>
          
          {/* Features */}
          <AnimatedCard delay={0.6}>
            <Flex 
              wrap="wrap" 
              justify="center" 
              gap={6}
            >
              {['Real-time Analysis', 'Market Insights', 'Competitor Tracking'].map((feature, i) => (
                <Box 
                  key={i} 
                  bg={useColorModeValue('white', 'gray.800')} 
                  p={4} 
                  borderRadius="md"
                  boxShadow="md"
                  textAlign="center"
                  minW="200px"
                >
                  <Text fontWeight="bold">{feature}</Text>
                </Box>
              ))}
            </Flex>
          </AnimatedCard>
        </VStack>
      </Flex>
    </Box>
  );
};

export default LandingPage; 