import { useState, useEffect } from 'react';

/**
 * Custom hook that returns a boolean indicating if the user prefers reduced motion
 * This is useful for conditionally disabling animations for accessibility
 */
export const usePrefersReducedMotion = (): boolean => {
  // Default to false (animations enabled) on server or when matchMedia isn't available
  const [prefersReducedMotion, setPrefersReducedMotion] = useState<boolean>(false);
  
  useEffect(() => {
    // Check if window is available (for SSR compatibility)
    if (typeof window === 'undefined') return;
    
    // Create the media query
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    
    // Set the initial value
    setPrefersReducedMotion(mediaQuery.matches);
    
    // Define the change handler
    const handleChange = (event: MediaQueryListEvent): void => {
      setPrefersReducedMotion(event.matches);
    };
    
    // Add the change listener
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange);
    } else {
      // For older browsers
      mediaQuery.addListener(handleChange);
    }
    
    // Clean up
    return () => {
      if (mediaQuery.removeEventListener) {
        mediaQuery.removeEventListener('change', handleChange);
      } else {
        // For older browsers
        mediaQuery.removeListener(handleChange);
      }
    };
  }, []);
  
  return prefersReducedMotion;
};

export default usePrefersReducedMotion; 