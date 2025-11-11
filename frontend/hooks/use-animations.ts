'use client';

import { useEffect, useState } from 'react';

/**
 * Hook to check if user prefers reduced motion
 * @returns boolean indicating if reduced motion is preferred
 */
export function usePrefersReducedMotion(): boolean {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

    // Set initial value
    setPrefersReducedMotion(mediaQuery.matches);

    // Listen for changes
    const handleChange = (event: MediaQueryListEvent) => {
      setPrefersReducedMotion(event.matches);
    };

    mediaQuery.addEventListener('change', handleChange);

    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  }, []);

  return prefersReducedMotion;
}

/**
 * Hook to conditionally apply animation classes based on reduced motion preference
 * @param animationClass - The animation class to apply
 * @param fallbackClass - The fallback class when animations are disabled
 * @returns The appropriate class name
 */
export function useAnimationClass(
  animationClass: string,
  fallbackClass: string = ''
): string {
  const prefersReducedMotion = usePrefersReducedMotion();
  return prefersReducedMotion ? fallbackClass : animationClass;
}

/**
 * Hook to get animation duration based on user preferences
 * @param duration - The desired animation duration in ms
 * @returns The duration (0ms if reduced motion is preferred)
 */
export function useAnimationDuration(duration: number): number {
  const prefersReducedMotion = usePrefersReducedMotion();
  return prefersReducedMotion ? 0 : duration;
}

/**
 * Hook for staggered list animations
 * @param itemCount - Number of items in the list
 * @param baseDelay - Base delay between items in ms
 * @returns Array of delay values for each item
 */
export function useStaggeredAnimation(
  itemCount: number,
  baseDelay: number = 50
): number[] {
  const prefersReducedMotion = usePrefersReducedMotion();

  if (prefersReducedMotion) {
    return new Array(itemCount).fill(0);
  }

  return Array.from({ length: itemCount }, (_, i) => i * baseDelay);
}
