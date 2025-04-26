import React, { useEffect } from 'react';
import { motion, useAnimation } from 'framer-motion';
import { Input, InputProps } from '@chakra-ui/react';
import { FormControl, FormLabel, FormErrorMessage } from '@chakra-ui/form-control';

interface AnimatedInputProps extends Omit<InputProps, 'isInvalid'> {
  label?: string;
  error?: string;
  animate?: boolean;
}

const AnimatedInput: React.FC<AnimatedInputProps> = ({
  label,
  error,
  animate = true,
  ...props
}) => {
  const controls = useAnimation();
  
  // Create shake animation when error appears
  useEffect(() => {
    if (error && animate) {
      controls.start({
        x: [0, -10, 10, -10, 10, 0],
        transition: { duration: 0.5 }
      });
    }
  }, [error, animate, controls]);
  
  return (
    <FormControl isInvalid={!!error} mb={4}>
      {label && <FormLabel>{label}</FormLabel>}
      
      <motion.div animate={controls}>
        <Input 
          borderColor={error ? 'red.300' : 'gray.300'} 
          _hover={{ borderColor: error ? 'red.400' : 'gray.400' }}
          _focus={{ 
            borderColor: error ? 'red.500' : 'teal.500',
            boxShadow: error 
              ? '0 0 0 1px var(--chakra-colors-red-500)'
              : '0 0 0 1px var(--chakra-colors-teal-500)'
          }}
          {...props} 
        />
      </motion.div>
      
      {error && (
        <FormErrorMessage>
          {error}
        </FormErrorMessage>
      )}
    </FormControl>
  );
};

export default AnimatedInput; 