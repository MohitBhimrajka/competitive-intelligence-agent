import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Box, Flex, Text, VStack } from '@chakra-ui/react';
import { motion } from 'framer-motion';
import ThreeCanvas from '../three/ThreeCanvas';
import SceneSetup3D from '../three/SceneSetup3D';
import RotatingLogo3D from '../three/RotatingLogo3D';
import ParticleBackground3D from '../three/ParticleBackground3D';
import { useAppDispatch } from '../state/store';
import { fetchCompanyData } from '../state/store';

interface AnimatedLoadingPageProps {
  initialProgress?: number;
  loadingTime?: number;
  autoNavigate?: boolean;
}

const AnimatedLoadingPage: React.FC<AnimatedLoadingPageProps> = ({
  initialProgress = 0,
  loadingTime = 5000, // 5 seconds by default
  autoNavigate = true
}) => {
  const [progress, setProgress] = useState(initialProgress);
  const navigate = useNavigate();
  const { companyId = '' } = useParams<{ companyId: string }>();
  const dispatch = useAppDispatch();

  // Handle the loading animation
  useEffect(() => {
    let animationFrame: number;
    let startTime: number;
    
    const animate = (timestamp: number) => {
      if (!startTime) startTime = timestamp;
      
      const elapsedTime = timestamp - startTime;
      const nextProgress = Math.min(100, (elapsedTime / loadingTime) * 100);
      
      setProgress(Math.floor(nextProgress));
      
      if (nextProgress < 100) {
        animationFrame = requestAnimationFrame(animate);
      } else if (autoNavigate) {
        // When loading completes, navigate to dashboard
        setTimeout(() => {
          navigate(`/dashboard/${companyId}`);
        }, 500); // Small delay for visual completion
      }
    };
    
    // Start the animation
    animationFrame = requestAnimationFrame(animate);
    
    // Simulate data loading
    if (companyId) {
      dispatch(fetchCompanyData(companyId));
    }
    
    // Cleanup animation on unmount
    return () => {
      cancelAnimationFrame(animationFrame);
    };
  }, [companyId, loadingTime, navigate, autoNavigate, dispatch]);

  // Text animation variants
  const textVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: {
        duration: 0.5
      }
    }
  };

  // Dots animation to create "Analyzing..." effect
  const dotsVariants = {
    animate: {
      opacity: [0, 1, 0],
      transition: {
        duration: 1.5,
        repeat: Infinity,
        repeatType: "loop" as const
      }
    }
  };

  return (
    <Flex 
      direction="column" 
      align="center" 
      justify="center" 
      minH="100vh"
      position="relative"
      overflow="hidden"
    >
      {/* 3D Scene */}
      <Box 
        position="absolute" 
        top={0} 
        left={0} 
        right={0} 
        bottom={0} 
        zIndex={0}
      >
        <ThreeCanvas>
          <SceneSetup3D>
            <RotatingLogo3D scale={0.8} position={[0, 0.5, 0]} />
            <ParticleBackground3D count={1500} color="#4FD1C5" />
          </SceneSetup3D>
        </ThreeCanvas>
      </Box>
      
      {/* Content */}
      <VStack 
        spacing={6} 
        zIndex={1} 
        position="relative"
        bg="blackAlpha.700"
        p={8}
        borderRadius="xl"
        className="glass"
        maxW="450px"
        textAlign="center"
      >
        <motion.div
          initial="hidden"
          animate="visible"
          variants={textVariants}
        >
          <Text 
            fontSize="3xl" 
            fontWeight="bold" 
            color="white"
          >
            Analyzing
            <motion.span
              variants={dotsVariants}
              animate="animate"
            >
              ...
            </motion.span>
          </Text>
        </motion.div>
        
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.3 }}
          style={{
            height: '8px',
            background: 'linear-gradient(90deg, #4FD1C5 0%, #63B3ED 100%)',
            borderRadius: '4px',
            alignSelf: 'stretch'
          }}
        />
        
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          <Text fontSize="xl" color="whiteAlpha.900">
            {progress}%
          </Text>
        </motion.div>
      </VStack>
    </Flex>
  );
};

export default AnimatedLoadingPage; 