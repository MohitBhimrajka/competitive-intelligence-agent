import React from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';

interface AnimatedCardProps extends HTMLMotionProps<'div'> {
  delay?: number;
}

const AnimatedCard: React.FC<AnimatedCardProps> = ({ 
  children, 
  delay = 0, 
  ...props 
}) => {
  return (
    <motion.div
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ 
        duration: 0.5,
        delay,
        ease: 'easeOut'
      }}
      whileHover={{ scale: 1.03 }}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export default AnimatedCard; 