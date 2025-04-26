import React from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';

interface HoverEffectButtonProps extends HTMLMotionProps<'button'> {
  variant?: 'primary' | 'secondary' | 'outline';
}

const HoverEffectButton: React.FC<HoverEffectButtonProps> = ({
  children,
  variant = 'primary',
  className = '',
  ...props
}) => {
  // Base classes that will apply to all variants
  let buttonClasses = 'py-2 px-4 rounded-md font-medium transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 ';
  
  // Add variant-specific classes
  switch (variant) {
    case 'primary':
      buttonClasses += 'bg-teal-500 text-white hover:bg-teal-600 focus:ring-teal-500 ';
      break;
    case 'secondary':
      buttonClasses += 'bg-blue-500 text-white hover:bg-blue-600 focus:ring-blue-500 ';
      break;
    case 'outline':
      buttonClasses += 'bg-transparent border border-teal-500 text-teal-500 hover:bg-teal-50 focus:ring-teal-500 ';
      break;
    default:
      buttonClasses += 'bg-teal-500 text-white hover:bg-teal-600 focus:ring-teal-500 ';
  }
  
  // Combine with any additional classes passed as props
  buttonClasses += className;
  
  return (
    <motion.button
      className={buttonClasses}
      whileHover={{ 
        scale: 1.05,
        boxShadow: '0px 5px 10px rgba(0, 0, 0, 0.15)'
      }}
      whileTap={{ 
        scale: 0.95 
      }}
      {...props}
    >
      {children}
    </motion.button>
  );
};

export default HoverEffectButton; 