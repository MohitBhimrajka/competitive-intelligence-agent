import React, { useState } from 'react';
import { 
  Box, 
  SimpleGrid, 
  Heading, 
  Text, 
  Badge, 
  Button,
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
import AnimatedCard from '../ui/AnimatedCard';
import { Competitor } from '../../state/store';

// CompetitorCard component
const CompetitorCard: React.FC<{ 
  competitor: Competitor; 
  onViewDetails: () => void;
}> = ({ competitor, onViewDetails }) => {
  const cardBg = useColorModeValue('white', 'gray.800');
  const strengthColor = 
    competitor.relationshipStrength && competitor.relationshipStrength > 70 ? 'red.500' :
    competitor.relationshipStrength && competitor.relationshipStrength > 40 ? 'orange.500' : 
    'green.500';

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
    >
      <Heading size="md" mb={2}>{competitor.name}</Heading>
      <Badge colorScheme="blue" mb={3}>
        {competitor.industry}
      </Badge>
      
      {competitor.relationshipStrength && (
        <Box mt={3}>
          <Text fontSize="sm" mb={1}>Competition Strength</Text>
          <Box 
            height="4px" 
            width="100%" 
            bg="gray.200" 
            borderRadius="full"
          >
            <Box 
              height="100%" 
              width={`${competitor.relationshipStrength}%`} 
              bg={strengthColor} 
              borderRadius="full"
            />
          </Box>
          <Text fontSize="xs" mt={1} textAlign="right">
            {competitor.relationshipStrength}%
          </Text>
        </Box>
      )}
      
      {competitor.description && (
        <Text fontSize="sm" mt={3} style={{ display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
          {competitor.description}
        </Text>
      )}
    </Box>
  );
};

// Deep research modal component
const DeepResearchViewerModal: React.FC<{
  competitor: Competitor | null;
  isOpen: boolean;
  onClose: () => void;
}> = ({ competitor, isOpen, onClose }) => {
  if (!competitor) return null;
  
  return (
    <Modal isOpen={isOpen} onClose={onClose} size="xl">
      <ModalOverlay backdropFilter="blur(2px)" />
      <ModalContent>
        <ModalHeader>
          {competitor.name}
          <Badge colorScheme="blue" ml={2}>
            {competitor.industry}
          </Badge>
        </ModalHeader>
        <ModalCloseButton />
        
        <ModalBody>
          {competitor.description ? (
            <Text mb={4}>{competitor.description}</Text>
          ) : (
            <Text mb={4} fontStyle="italic">No detailed description available.</Text>
          )}
          
          {/* Additional sections would go here - financial data, key products, etc. */}
          <Box mb={4}>
            <Heading size="sm" mb={2}>Key Information</Heading>
            <SimpleGrid columns={2} gap={4}>
              {competitor.website && (
                <Box>
                  <Text fontWeight="bold" fontSize="sm">Website</Text>
                  <Text fontSize="sm">{competitor.website}</Text>
                </Box>
              )}
              {/* Add more fields as needed */}
              <Box>
                <Text fontWeight="bold" fontSize="sm">Competition Level</Text>
                <Text 
                  fontSize="sm" 
                  color={
                    competitor.relationshipStrength && competitor.relationshipStrength > 70 ? 'red.500' :
                    competitor.relationshipStrength && competitor.relationshipStrength > 40 ? 'orange.500' : 
                    'green.500'
                  }
                >
                  {competitor.relationshipStrength ? `${competitor.relationshipStrength}%` : 'Unknown'}
                </Text>
              </Box>
            </SimpleGrid>
          </Box>
          
          <Box>
            <Heading size="sm" mb={2}>Competitive Analysis</Heading>
            <Text>
              Detailed competitive analysis coming soon. This will include market positioning,
              SWOT analysis, and strategic recommendations.
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
const CompetitorSectionAnimated: React.FC<{
  competitors: Competitor[];
  title?: string;
}> = ({ 
  competitors, 
  title = "Competitors"
}) => {
  const [selectedCompetitor, setSelectedCompetitor] = useState<Competitor | null>(null);
  const { open: isOpen, onOpen, onClose } = useDisclosure();
  
  const handleViewDetails = (competitor: Competitor) => {
    setSelectedCompetitor(competitor);
    onOpen();
  };
  
  return (
    <Box>
      <Heading mb={4} size="lg">{title}</Heading>
      
      {competitors.length > 0 ? (
        <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} gap={6}>
          {competitors.map((competitor, index) => (
            <AnimatedCard key={competitor.id} delay={0.1 * index}>
              <CompetitorCard 
                competitor={competitor} 
                onViewDetails={() => handleViewDetails(competitor)} 
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
          <Text>No competitor data available</Text>
        </Box>
      )}
      
      <DeepResearchViewerModal 
        competitor={selectedCompetitor} 
        isOpen={isOpen} 
        onClose={onClose} 
      />
    </Box>
  );
};

export default CompetitorSectionAnimated; 