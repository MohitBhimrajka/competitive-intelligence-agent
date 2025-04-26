import React, { useState } from 'react';
import { 
  Box, 
  SimpleGrid, 
  Heading, 
  Text, 
  Badge, 
  Button,
  Flex,
  HStack,
  Icon,
  useDisclosure
} from '@chakra-ui/react';
import { 
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton
} from '@chakra-ui/modal';
import { useColorModeValue } from '@chakra-ui/color-mode';
import { FiAlertTriangle, FiInfo, FiCalendar, FiTag } from 'react-icons/fi';
import AnimatedCard from '../ui/AnimatedCard';
import { Insight } from '../../state/store';

// InsightCard component
const InsightCard: React.FC<{ 
  insight: Insight; 
  onViewDetails: () => void;
}> = ({ insight, onViewDetails }) => {
  const cardBg = useColorModeValue('white', 'gray.800');
  
  // Determine severity color and icon
  const severityColor = 
    insight.severity === 'high' ? 'red.500' :
    insight.severity === 'medium' ? 'orange.400' :
    'green.500';
  
  const severityIcon = insight.severity === 'high' ? FiAlertTriangle : FiInfo;
  
  // Determine category badge color
  const categoryColor = 
    insight.category === 'market' ? 'blue' :
    insight.category === 'competitor' ? 'purple' :
    insight.category === 'product' ? 'green' :
    insight.category === 'strategy' ? 'orange' :
    'gray';

  return (
    <Box
      bg={cardBg}
      borderRadius="lg"
      boxShadow="md"
      p={5}
      height="100%"
      cursor="pointer"
      transition="transform 0.2s"
      _hover={{ transform: 'translateY(-2px)' }}
      onClick={onViewDetails}
      borderLeftWidth="4px"
      borderLeftColor={severityColor}
    >
      <Flex mb={3} alignItems="center" justifyContent="space-between">
        <Heading size="md" style={{ display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>{insight.title}</Heading>
        <Icon as={severityIcon} color={severityColor} boxSize={5} />
      </Flex>
      
      <HStack gap={2} mb={3}>
        <Badge colorScheme={categoryColor}>
          {insight.category.charAt(0).toUpperCase() + insight.category.slice(1)}
        </Badge>
        <Text fontSize="sm" color="gray.500">
          {new Date(insight.date).toLocaleDateString()}
        </Text>
      </HStack>
      
      <Text fontSize="sm" style={{ display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
        {insight.description}
      </Text>
    </Box>
  );
};

// Insight detail modal component
const InsightDetailModal: React.FC<{
  insight: Insight | null;
  isOpen: boolean;
  onClose: () => void;
}> = ({ insight, isOpen, onClose }) => {
  if (!insight) return null;
  
  // Determine severity color and text
  const severityColor = 
    insight.severity === 'high' ? 'red.500' :
    insight.severity === 'medium' ? 'orange.400' :
    'green.500';
  
  const severityText = 
    insight.severity === 'high' ? 'High' :
    insight.severity === 'medium' ? 'Medium' :
    'Low';
  
  // Determine category badge color
  const categoryColor = 
    insight.category === 'market' ? 'blue' :
    insight.category === 'competitor' ? 'purple' :
    insight.category === 'product' ? 'green' :
    insight.category === 'strategy' ? 'orange' :
    'gray';
  
  return (
    <Modal isOpen={isOpen} onClose={onClose} size="xl">
      <ModalOverlay backdropFilter="blur(2px)" />
      <ModalContent>
        <ModalHeader borderLeftWidth="4px" borderLeftColor={severityColor}>
          {insight.title}
        </ModalHeader>
        <ModalCloseButton />
        
        <ModalBody>
          <HStack mb={4} gap={4}>
            <Flex align="center">
              <Icon as={FiTag} mr={1} />
              <Badge colorScheme={categoryColor}>
                {insight.category.charAt(0).toUpperCase() + insight.category.slice(1)}
              </Badge>
            </Flex>
            
            <Flex align="center">
              <Icon as={FiAlertTriangle} mr={1} color={severityColor} />
              <Text fontSize="sm" color={severityColor} fontWeight="bold">
                {severityText} Severity
              </Text>
            </Flex>
            
            <Flex align="center">
              <Icon as={FiCalendar} mr={1} />
              <Text fontSize="sm">
                {new Date(insight.date).toLocaleDateString()}
              </Text>
            </Flex>
          </HStack>
          
          <Text mb={6}>{insight.description}</Text>
          
          {/* Related companies section */}
          {insight.relatedCompanyIds && insight.relatedCompanyIds.length > 0 && (
            <Box mb={6}>
              <Heading size="sm" mb={2}>Related Companies</Heading>
              <HStack gap={2}>
                {insight.relatedCompanyIds.map(id => (
                  <Badge key={id} colorScheme="teal">{id}</Badge>
                ))}
              </HStack>
            </Box>
          )}
          
          {/* Additional analysis would go here */}
          <Box mb={4}>
            <Heading size="sm" mb={2}>Detailed Analysis</Heading>
            <Text>
              In-depth analysis of this insight and its implications will appear here.
              This will include potential impact, recommended actions, and strategic considerations.
            </Text>
          </Box>
        </ModalBody>
        
        <ModalFooter>
          <Button colorScheme="blue" mr={3} onClick={onClose}>
            Close
          </Button>
          <Button variant="ghost">Generate Report</Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

// Main component
const InsightsSectionAnimated: React.FC<{
  insights: Insight[];
  title?: string;
}> = ({ 
  insights, 
  title = "Market Insights"
}) => {
  const [selectedInsight, setSelectedInsight] = useState<Insight | null>(null);
  const { open: isOpen, onOpen, onClose } = useDisclosure();
  
  const handleViewDetails = (insight: Insight) => {
    setSelectedInsight(insight);
    onOpen();
  };
  
  return (
    <Box>
      <Heading mb={4} size="lg">{title}</Heading>
      
      {insights.length > 0 ? (
        <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} gap={6}>
          {insights.map((insight, index) => (
            <AnimatedCard key={insight.id} delay={0.1 * index}>
              <InsightCard 
                insight={insight} 
                onViewDetails={() => handleViewDetails(insight)} 
              />
            </AnimatedCard>
          ))}
        </SimpleGrid>
      ) : (
        <Box 
          p={5} 
          bg={useColorModeValue('white', 'gray.800')} 
          borderRadius="lg"
          textAlign="center"
        >
          <Text>No insights data available</Text>
        </Box>
      )}
      
      <InsightDetailModal 
        insight={selectedInsight} 
        isOpen={isOpen} 
        onClose={onClose} 
      />
    </Box>
  );
};

export default InsightsSectionAnimated; 