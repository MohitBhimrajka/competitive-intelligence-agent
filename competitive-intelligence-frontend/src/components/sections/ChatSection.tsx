import React, { useState, useRef, useEffect } from 'react';
import { 
  Box, 
  HStack, 
  Input, 
  Button, 
  Text, 
  Flex, 
  Heading, 
  Icon
} from '@chakra-ui/react';
import { VStack, Divider } from '@chakra-ui/layout';
import { Avatar } from '@chakra-ui/avatar';
import { useColorModeValue } from '@chakra-ui/color-mode';
import { FiSend, FiUser, FiCpu, FiCornerDownRight } from 'react-icons/fi';
import AnimatedCard from '../ui/AnimatedCard';
import HoverEffectButton from '../ui/HoverEffectButton';

type MessageType = 'user' | 'assistant';

interface ChatMessage {
  id: string;
  type: MessageType;
  text: string;
  timestamp: Date;
}

interface ChatSectionProps {
  companyId?: string;
  title?: string;
}

const ChatSection: React.FC<ChatSectionProps> = ({ 
  companyId = '',
  title = "AI Assistant"
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      type: 'assistant',
      text: `Hi there! I'm your competitive intelligence assistant. How can I help you understand the market landscape for ${companyId || 'your company'}?`,
      timestamp: new Date()
    }
  ]);
  
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Auto-scroll to bottom of chat
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);
  
  // Sample questions to help users get started
  const sampleQuestions = [
    "Who are our main competitors?",
    "What are recent market trends?",
    "Summarize recent news about competitors",
    "What strategic opportunities should we consider?"
  ];
  
  const handleSendMessage = () => {
    if (!inputValue.trim()) return;
    
    // Add user message
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      text: inputValue,
      timestamp: new Date()
    };
    
    setMessages(prevMessages => [...prevMessages, userMessage]);
    setInputValue('');
    setIsLoading(true);
    
    // Simulate AI response
    setTimeout(() => {
      const botMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        text: generateDummyResponse(inputValue, companyId),
        timestamp: new Date()
      };
      
      setMessages(prevMessages => [...prevMessages, botMessage]);
      setIsLoading(false);
    }, 1500);
  };
  
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };
  
  // Quick reply function
  const handleQuickReply = (question: string) => {
    setInputValue(question);
    // Focus on input after setting value
    (document.querySelector('#chat-input') as HTMLInputElement)?.focus();
  };
  
  // Message bubble component
  const MessageBubble: React.FC<{ message: ChatMessage }> = ({ message }) => {
    const isUser = message.type === 'user';
    const bubbleBg = isUser 
      ? useColorModeValue('blue.500', 'blue.400')
      : useColorModeValue('gray.200', 'gray.700');
    const textColor = isUser 
      ? 'white'
      : useColorModeValue('gray.800', 'white');
    
    return (
      <Flex
        direction="row"
        justify={isUser ? 'flex-end' : 'flex-start'}
        mb={4}
        w="100%"
      >
        {!isUser && (
          <Avatar 
            icon={<Icon as={FiCpu} fontSize="1.2rem" />} 
            bg="teal.500" 
            color="white" 
            size="sm" 
            mr={2} 
          />
        )}
        
        <Box
          px={4}
          py={2}
          borderRadius="lg"
          maxW={{ base: "75%", md: "70%" }}
          bg={bubbleBg}
          color={textColor}
        >
          <Text>{message.text}</Text>
          <Text fontSize="xs" opacity={0.7} textAlign="right" mt={1}>
            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </Text>
        </Box>
        
        {isUser && (
          <Avatar 
            icon={<Icon as={FiUser} fontSize="1.2rem" />} 
            bg="blue.500" 
            color="white" 
            size="sm" 
            ml={2} 
          />
        )}
      </Flex>
    );
  };
  
  return (
    <AnimatedCard delay={0.4}>
      <Box
        bg={useColorModeValue('white', 'gray.800')}
        borderRadius="lg"
        boxShadow="md"
        overflow="hidden"
        height={{ base: "500px", md: "600px" }}
      >
        {/* Header */}
        <Box 
          p={4} 
          borderBottomWidth="1px" 
          bg={useColorModeValue('gray.50', 'gray.900')}
        >
          <Heading size="md">{title}</Heading>
          <Text fontSize="sm">
            Ask questions about market positioning, competitors, and industry trends
          </Text>
        </Box>
        
        {/* Messages area */}
        <Box 
          p={4} 
          height={{ base: "340px", md: "440px" }} 
          overflowY="auto"
        >
          <VStack spacing={0} align="stretch">
            {messages.map(message => (
              <MessageBubble key={message.id} message={message} />
            ))}
            
            {isLoading && (
              <Flex justify="flex-start" mb={4}>
                <Avatar 
                  icon={<Icon as={FiCpu} fontSize="1.2rem" />} 
                  bg="teal.500" 
                  color="white" 
                  size="sm" 
                  mr={2} 
                />
                <Box
                  px={4}
                  py={2}
                  borderRadius="lg"
                  bg={useColorModeValue('gray.200', 'gray.700')}
                >
                  <Text fontStyle="italic">Thinking...</Text>
                </Box>
              </Flex>
            )}
            
            <div ref={messagesEndRef} />
          </VStack>
        </Box>
        
        {/* Quick replies */}
        {messages.length <= 2 && (
          <Box px={4} pb={2}>
            <Text fontSize="xs" fontWeight="semibold" mb={2}>SUGGESTED QUESTIONS</Text>
            <Flex wrap="wrap" gap={2}>
              {sampleQuestions.map((question, index) => (
                <Box
                  key={index}
                  as="button"
                  px={3}
                  py={1}
                  borderRadius="full"
                  fontSize="xs"
                  bg={useColorModeValue('gray.100', 'gray.700')}
                  _hover={{ bg: useColorModeValue('gray.200', 'gray.600') }}
                  onClick={() => handleQuickReply(question)}
                >
                  <Flex align="center">
                    <Icon as={FiCornerDownRight} mr={1} />
                    {question}
                  </Flex>
                </Box>
              ))}
            </Flex>
          </Box>
        )}
        
        <Divider />
        
        {/* Input area */}
        <Box p={4}>
          <HStack>
            <Input
              id="chat-input"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about competitors, market trends, etc."
              variant="outline"
              disabled={isLoading}
            />
            <HoverEffectButton
              aria-label="Send message"
              disabled={isLoading || !inputValue.trim()}
              onClick={handleSendMessage}
              variant="primary"
            >
              <Icon as={FiSend} />
            </HoverEffectButton>
          </HStack>
        </Box>
      </Box>
    </AnimatedCard>
  );
};

// Helper function to generate dummy responses
const generateDummyResponse = (question: string, companyId: string): string => {
  const responses = [
    `Based on our analysis, ${companyId || 'your company'} has several major competitors in this space, including ABC Corp, XYZ Inc, and 123 Technologies. Each has different strengths in the market.`,
    "The market has been shifting toward sustainability and digital transformation. Recent industry reports show a 15% increase in companies adopting cloud-based solutions.",
    "Recent news highlights increasing competition in your sector, with several mergers and acquisitions announced in the past quarter. This could indicate market consolidation.",
    "Strategic opportunities could include expanding into emerging markets, focusing on sustainability initiatives, or developing strategic partnerships with complementary businesses.",
    "Our data shows changing consumer preferences in your industry, with increased demand for personalized solutions and ethical business practices.",
    "I've analyzed the competitive landscape and found that your top competitors have been investing heavily in AI and automation technologies."
  ];
  
  return responses[Math.floor(Math.random() * responses.length)];
};

export default ChatSection; 