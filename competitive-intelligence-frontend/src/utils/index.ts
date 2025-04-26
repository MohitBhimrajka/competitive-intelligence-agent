/**
 * Utility functions for the application
 */

/**
 * Throttles a function to limit how often it can be called
 * @param fn The function to throttle
 * @param delay The minimum time between function calls in milliseconds
 * @returns A throttled version of the function
 */
export function throttle<T extends (...args: any[]) => any>(fn: T, delay: number): (...args: Parameters<T>) => void {
  let lastCall = 0;
  let timeoutId: ReturnType<typeof setTimeout> | null = null;
  
  return function(...args: Parameters<T>) {
    const now = Date.now();
    const timeSinceLastCall = now - lastCall;
    
    // Clear any existing timeout
    if (timeoutId !== null) {
      clearTimeout(timeoutId);
      timeoutId = null;
    }
    
    if (timeSinceLastCall >= delay) {
      // If enough time has passed, execute immediately
      lastCall = now;
      fn(...args);
    } else {
      // Otherwise, schedule for later
      timeoutId = setTimeout(() => {
        lastCall = Date.now();
        fn(...args);
        timeoutId = null;
      }, delay - timeSinceLastCall);
    }
  };
}

/**
 * Formats a number as a currency string
 * @param value The number to format
 * @param currency The currency code (default: 'USD')
 * @param locale The locale to use for formatting (default: 'en-US')
 * @returns Formatted currency string
 */
export function formatCurrency(
  value: number, 
  currency: string = 'USD',
  locale: string = 'en-US'
): string {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: currency,
  }).format(value);
}

/**
 * Detects if the current device is a mobile device
 * @param maxWidth The maximum width to consider as mobile (default: 768px)
 * @returns Boolean indicating if the device is mobile
 */
export function isMobile(maxWidth: number = 768): boolean {
  if (typeof window === 'undefined') {
    return false; // Default to desktop for SSR
  }
  
  return window.matchMedia(`(max-width: ${maxWidth}px)`).matches;
} 