import React, { useState, ReactNode } from 'react';
import { 
  Box, 
  Grid, 
  IconButton, 
  Flex, 
  Heading,
  useBreakpointValue
} from '@chakra-ui/react';
import { useColorMode } from '@chakra-ui/color-mode';
import { motion, HTMLMotionProps } from 'framer-motion';
import { FiMenu, FiX, FiMoon, FiSun } from 'react-icons/fi';

interface DashboardLayoutProps {
  children: ReactNode;
  title?: string;
}

const DashboardLayout: React.FC<DashboardLayoutProps> = ({ 
  children,
  title = 'Dashboard'
}) => {
  const [isSidebarOpen, setSidebarOpen] = useState(true);
  const { colorMode, toggleColorMode } = useColorMode();
  
  // Responsive sidebar width adjustments
  const sidebarWidth = useBreakpointValue({ base: '100%', md: isSidebarOpen ? '250px' : '60px' });
  const isMobile = useBreakpointValue({ base: true, md: false });
  
  // If mobile and sidebar is open, we show an overlay
  const showOverlay = isMobile && isSidebarOpen;
  
  // Animation variants for sidebar
  const sidebarVariants = {
    open: { width: isMobile ? '80%' : '250px', x: 0 },
    closed: { width: isMobile ? '0%' : '60px', x: isMobile ? '-100%' : 0 }
  };
  
  // On mobile the sidebar slides in from the left
  // On desktop it just expands/contracts
  
  return (
    <Grid
      templateColumns={isMobile ? '1fr' : `${sidebarWidth} 1fr`}
      templateRows="auto 1fr"
      templateAreas={{
        base: `"header" "main"`,
        md: `"sidebar header" "sidebar main"`
      }}
      minH="100vh"
    >
      {/* Header */}
      <Flex
        as="header"
        gridArea="header"
        py={4}
        px={6}
        align="center"
        justify="space-between"
        borderBottomWidth="1px"
        position="sticky"
        top={0}
        bg={colorMode === 'dark' ? 'gray.800' : 'white'}
        zIndex={10}
      >
        <Flex align="center">
          {isMobile && (
            <IconButton
              aria-label={isSidebarOpen ? "Close Sidebar" : "Open Sidebar"}
              variant="ghost"
              mr={3}
              onClick={() => setSidebarOpen(!isSidebarOpen)}
            >
              {isSidebarOpen ? <FiX /> : <FiMenu />}
            </IconButton>
          )}
          <Heading size="md">{title}</Heading>
        </Flex>
        
        <IconButton
          aria-label={colorMode === 'dark' ? "Switch to Light Mode" : "Switch to Dark Mode"}
          variant="ghost"
          onClick={toggleColorMode}
        >
          {colorMode === 'dark' ? <FiSun /> : <FiMoon />}
        </IconButton>
      </Flex>
      
      {/* Sidebar - as motion.div for animation */}
      <motion.div
        style={{
          gridArea: isMobile ? 'main' : 'sidebar',
          backgroundColor: colorMode === 'dark' ? 'var(--chakra-colors-gray-900)' : 'var(--chakra-colors-gray-50)',
          borderRightWidth: isMobile ? 0 : '1px',
          position: isMobile ? 'fixed' : 'relative',
          top: isMobile ? 0 : 'auto',
          left: isMobile ? 0 : 'auto',
          height: isMobile ? '100vh' : 'auto',
          zIndex: isMobile ? 20 : 10,
          paddingTop: '1rem',
          paddingBottom: '1rem',
          overflowX: 'hidden',
          overflowY: 'auto'
        }}
        variants={sidebarVariants}
        animate={isSidebarOpen ? 'open' : 'closed'}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        initial="closed"
      >
        {/* Sidebar content */}
        <Flex direction="column" height="100%">
          {/* Logo or brand */}
          <Flex 
            align="center" 
            mb={8} 
            px={6}
            justify={isSidebarOpen ? "flex-start" : "center"}
          >
            {isSidebarOpen ? (
              <Heading size="md">Company Intel</Heading>
            ) : (
              <Box>CI</Box>
            )}
          </Flex>
          
          {/* Sidebar links would go here */}
          {/* Example: <SidebarNavigation isCollapsed={!isSidebarOpen} /> */}
          
          {/* Toggle button - only on desktop */}
          {!isMobile && (
            <IconButton
              aria-label={isSidebarOpen ? "Close Sidebar" : "Open Sidebar"}
              variant="ghost"
              alignSelf={isSidebarOpen ? "flex-end" : "center"}
              mx={isSidebarOpen ? 3 : 'auto'}
              mt="auto"
              mb={4}
              onClick={() => setSidebarOpen(!isSidebarOpen)}
            >
              {isSidebarOpen ? <FiX /> : <FiMenu />}
            </IconButton>
          )}
        </Flex>
      </motion.div>
      
      {/* Overlay for mobile */}
      {showOverlay && (
        <Box
          position="fixed"
          top={0}
          left={0}
          right={0}
          bottom={0}
          bg="blackAlpha.600"
          zIndex={15}
          onClick={() => setSidebarOpen(false)}
        />
      )}
      
      {/* Main content */}
      <Box
        gridArea="main"
        bg={colorMode === 'dark' ? 'gray.800' : 'gray.100'}
        p={6}
        overflowY="auto"
      >
        {children}
      </Box>
    </Grid>
  );
};

export default DashboardLayout; 