import { useState, useEffect } from 'react';
import { isMobile } from '../utils';
import usePrefersReducedMotion from './usePrefersReducedMotion';

/**
 * Hook that determines if heavy visual effects are appropriate for the current device
 * @param mobileMaxWidth Optional width threshold for mobile detection
 * @returns Object with allowHeavy boolean flag
 */
function usePerformanceGuard(mobileMaxWidth?: number) {
  const prefersReducedMotion = usePrefersReducedMotion();
  const [isCurrentlyMobile, setIsCurrentlyMobile] = useState(
    typeof window !== 'undefined' ? isMobile(mobileMaxWidth) : false
  );
  
  // Update mobile state on window resize
  useEffect(() => {
    if (typeof window === 'undefined') return;
    
    const handleResize = () => {
      setIsCurrentlyMobile(isMobile(mobileMaxWidth));
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [mobileMaxWidth]);
  
  return {
    allowHeavy: !isCurrentlyMobile && !prefersReducedMotion
  };
}

export default usePerformanceGuard; 