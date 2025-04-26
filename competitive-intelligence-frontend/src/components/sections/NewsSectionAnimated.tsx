import React, { useState } from 'react';
import { 
  Box, 
  SimpleGrid, 
  Heading, 
  Text, 
  Badge, 
  Button,
  Link,
  HStack,
  VStack,
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
import { FiExternalLink, FiCalendar, FiFileText } from 'react-icons/fi';
import AnimatedCard from '../ui/AnimatedCard';
import { NewsItem } from '../../state/store';

// NewsCard component
const NewsCard: React.FC<{ 
  newsItem: NewsItem; 
  onViewDetails: () => void;
}> = ({ newsItem, onViewDetails }) => {
  const cardBg = useColorModeValue('white', 'gray.800');
  const sentimentColor = 
    newsItem.sentiment === 'positive' ? 'green.500' :
    newsItem.sentiment === 'negative' ? 'red.500' : 
    'gray.500';

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
      position="relative"
      overflow="hidden"
    >
      {/* Sentiment indicator */}
      {newsItem.sentiment && (
        <Box 
          position="absolute" 
          top={0} 
          right={0} 
          width="8px" 
          height="100%" 
          bg={sentimentColor}
        />
      )}
      
      <VStack align="stretch" gap={3}>
        <Heading size="md" style={{ display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>{newsItem.title}</Heading>
        
        <HStack fontSize="sm" color="gray.500">
          <Icon as={FiCalendar} />
          <Text>{new Date(newsItem.date).toLocaleDateString()}</Text>
        </HStack>
        
        <Badge alignSelf="flex-start" colorScheme="blue">
          {newsItem.source}
        </Badge>
        
        <Text fontSize="sm" style={{ display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
          {newsItem.summary}
        </Text>
      </VStack>
    </Box>
  );
};

// News detail modal component
const NewsDetailModal: React.FC<{
  newsItem: NewsItem | null;
  isOpen: boolean;
  onClose: () => void;
}> = ({ newsItem, isOpen, onClose }) => {
  if (!newsItem) return null;
  
  const sentimentColor = 
    newsItem.sentiment === 'positive' ? 'green.500' :
    newsItem.sentiment === 'negative' ? 'red.500' : 
    'blue.500';
  
  const sentimentText = 
    newsItem.sentiment === 'positive' ? 'Positive' :
    newsItem.sentiment === 'negative' ? 'Negative' : 
    'Neutral';
  
  return (
    <Modal isOpen={isOpen} onClose={onClose} size="xl">
      <ModalOverlay backdropFilter="blur(2px)" />
      <ModalContent>
        <ModalHeader>
          {newsItem.title}
        </ModalHeader>
        <ModalCloseButton />
        
        <ModalBody>
          <HStack mb={4} gap={4}>
            <Badge colorScheme="blue">{newsItem.source}</Badge>
            <Text fontSize="sm">{new Date(newsItem.date).toLocaleDateString()}</Text>
            <Badge colorScheme={
              newsItem.sentiment === 'positive' ? 'green' :
              newsItem.sentiment === 'negative' ? 'red' : 
              'gray'
            }>
              {sentimentText}
            </Badge>
          </HStack>
          
          <Text mb={6}>{newsItem.summary}</Text>
          
          {/* Company mentions */}
          {newsItem.companyIds && newsItem.companyIds.length > 0 && (
            <Box mb={6}>
              <Heading size="sm" mb={2}>Mentioned Companies</Heading>
              <HStack gap={2}>
                {newsItem.companyIds.map(id => (
                  <Badge key={id} colorScheme="teal">{id}</Badge>
                ))}
              </HStack>
            </Box>
          )}
          
          {/* Additional analysis would go here */}
          <Box mb={4}>
            <Heading size="sm" mb={2}>Key Insights</Heading>
            <Text>
              AI-generated insights from this news story will appear here.
            </Text>
          </Box>
        </ModalBody>
        
        <ModalFooter>
          <Link href={newsItem.url} target="_blank" rel="noopener noreferrer">
            <Button
              colorScheme="blue"
              mr={3}
            >
              Read Full Article <Icon as={FiExternalLink} ml={2} />
            </Button>
          </Link>
          <Button variant="ghost" onClick={onClose}>
            Close
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

// Main component
const NewsSectionAnimated: React.FC<{
  news: NewsItem[];
  title?: string;
}> = ({ 
  news, 
  title = "Latest News"
}) => {
  const [selectedNews, setSelectedNews] = useState<NewsItem | null>(null);
  const { open: isOpen, onOpen, onClose } = useDisclosure();
  
  const handleViewDetails = (newsItem: NewsItem) => {
    setSelectedNews(newsItem);
    onOpen();
  };
  
  return (
    <Box>
      <Heading mb={4} size="lg">{title}</Heading>
      
      {news.length > 0 ? (
        <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} gap={6}>
          {news.map((newsItem, index) => (
            <AnimatedCard key={newsItem.id} delay={0.1 * index}>
              <NewsCard 
                newsItem={newsItem} 
                onViewDetails={() => handleViewDetails(newsItem)} 
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
          <Text>No news data available</Text>
        </Box>
      )}
      
      <NewsDetailModal 
        newsItem={selectedNews} 
        isOpen={isOpen} 
        onClose={onClose} 
      />
    </Box>
  );
};

export default NewsSectionAnimated; 