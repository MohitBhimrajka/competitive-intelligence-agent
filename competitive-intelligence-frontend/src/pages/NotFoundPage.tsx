import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { 
  Box, 
  Flex, 
  Heading, 
  Text, 
  Button, 
  VStack
} from '@chakra-ui/react';
import { useColorModeValue } from '@chakra-ui/color-mode';
import { motion } from 'framer-motion';
import { FiArrowLeft, FiHome } from 'react-icons/fi';

import ThreeCanvas from '../three/ThreeCanvas';
import SceneSetup3D from '../three/SceneSetup3D';
import ParticleBackground3D from '../three/ParticleBackground3D';
import AnimatedCard from '../components/ui/AnimatedCard';
import HoverEffectButton from '../components/ui/HoverEffectButton';
import usePerformanceGuard from '../hooks/usePerformanceGuard';

const NotFoundPage: React.FC = () => {
  const bgGradient = useColorModeValue(
    'linear(to-r, red.50, purple.50)',
    'linear(to-r, gray.900, purple.900)'
  );
  
  const particleColor = useColorModeValue('#6B46C1', '#D53F8C');
  const { allowHeavy } = usePerformanceGuard();
  
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

  return (
    <Box
      position="relative"
      minH="100vh"
      bgGradient={bgGradient}
      overflow="hidden"
    >
      {/* 3D Canvas Background */}
      {allowHeavy && (
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
              <ParticleBackground3D 
                count={1000} 
                color={particleColor} 
                radius={2.5}
                size={0.015}
                rotationSpeed={0.0003}
              />
            </SceneSetup3D>
          </ThreeCanvas>
        </Box>
      )}
      
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
        <AnimatedCard delay={0.2}>
          <VStack 
            gap={6} 
            bg={useColorModeValue('whiteAlpha.800', 'blackAlpha.700')}
            backdropFilter="blur(10px)"
            p={8}
            borderRadius="xl"
            maxW="450px"
            textAlign="center"
          >
            <motion.div
              initial="hidden"
              animate="visible"
              variants={textVariants}
            >
              <Heading 
                as="h1" 
                size="4xl" 
                bgGradient="linear(to-r, purple.400, pink.500)" 
                bgClip="text"
                mb={2}
              >
                404
              </Heading>
              
              <Heading size="lg" mb={4}>
                Page Not Found
              </Heading>
              
              <Text 
                color={useColorModeValue('gray.600', 'gray.300')}
                mb={6}
              >
                The page you're looking for doesn't exist or has been moved.
              </Text>
            </motion.div>
            
            <RouterLink to="/" style={{ width: '100%' }}>
              <HoverEffectButton
                variant="primary"
                className="w-full text-lg"
              >
                Go Home
              </HoverEffectButton>
            </RouterLink>
          </VStack>
        </AnimatedCard>
      </Flex>
    </Box>
  );
};

export default NotFoundPage; 