import React from 'react';
import { Box, BoxProps } from '@chakra-ui/react';

const GlassmorphicContainer: React.FC<BoxProps> = (props) => {
  return (
    <Box className="glass p-8 shadow-lg" {...props} />
  );
};

export default GlassmorphicContainer; 