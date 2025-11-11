/**
 * Animation Utilities and Configuration
 *
 * Provides centralized animation configurations, timing functions,
 * and utility helpers for consistent animations throughout the app.
 */

// ============================================================================
// Animation Timing & Easing
// ============================================================================

export const animationDuration = {
  fast: '150ms',
  normal: '250ms',
  slow: '350ms',
  slower: '500ms',
} as const;

export const animationEasing = {
  easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
  easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
  easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
  spring: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
  bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
} as const;

// ============================================================================
// Reusable Animation Classes
// ============================================================================

/**
 * Common animation class combinations for various UI elements
 */
export const animationClasses = {
  // Button & interactive element animations
  button: {
    base: 'transition-all duration-150 transform-gpu',
    hover: 'hover:scale-[1.02] hover:shadow-md active:scale-[0.98]',
    focus: 'focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
  },

  // Link animations
  link: {
    base: 'transition-colors duration-150',
    underline: 'underline-offset-4 hover:underline transition-all duration-150',
    interactive: 'hover:text-primary/80 active:text-primary/60 transition-colors duration-150',
  },

  // Icon button animations
  iconButton: {
    base: 'transition-all duration-150 transform-gpu',
    hover: 'hover:scale-110 active:scale-95',
    subtle: 'hover:opacity-80 active:opacity-60 transition-opacity duration-150',
  },

  // Card animations
  card: {
    base: 'transition-all duration-250 transform-gpu',
    // Subtle hover for non-interactive cards (visual feedback only)
    subtle: 'hover:shadow-md hover:border-border/80',
    // Standard hover with slight elevation
    hover: 'hover:shadow-lg hover:-translate-y-1',
    // Strong interactive hover for clickable cards
    interactive: 'cursor-pointer hover:shadow-xl hover:-translate-y-2 hover:border-primary/20 active:translate-y-0 active:shadow-md',
  },

  // Metric/Stat card animations (smaller cards with key metrics)
  metricCard: {
    base: 'transition-all duration-200 transform-gpu',
    hover: 'hover:shadow-md hover:border-border/80 hover:bg-accent/5',
    interactive: 'cursor-pointer hover:shadow-lg hover:-translate-y-0.5 hover:border-primary/30 active:translate-y-0',
  },

  // Fade animations
  fade: {
    in: 'animate-in fade-in',
    out: 'animate-out fade-out',
    inOut: 'animate-in fade-in animate-out fade-out',
  },

  // Slide animations
  slide: {
    in: 'animate-in slide-in-from-bottom',
    inFromTop: 'animate-in slide-in-from-top',
    inFromLeft: 'animate-in slide-in-from-left',
    inFromRight: 'animate-in slide-in-from-right',
    out: 'animate-out slide-out-to-bottom',
  },

  // Scale animations
  scale: {
    in: 'animate-in zoom-in',
    out: 'animate-out zoom-out',
  },

  // Loading & skeleton
  loading: {
    pulse: 'animate-pulse',
    spin: 'animate-spin',
    skeleton: 'skeleton',
  },
} as const;

// ============================================================================
// Animation Utility Functions
// ============================================================================

/**
 * Check if user prefers reduced motion
 */
export function prefersReducedMotion(): boolean {
  if (typeof window === 'undefined') return false;
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/**
 * Get animation duration based on user preferences
 */
export function getAnimationDuration(duration: keyof typeof animationDuration): string {
  if (prefersReducedMotion()) return '0ms';
  return animationDuration[duration];
}

/**
 * Conditionally apply animation classes based on reduced motion preference
 */
export function withAnimation(
  animationClass: string,
  fallbackClass: string = ''
): string {
  if (typeof window === 'undefined') return animationClass;
  return prefersReducedMotion() ? fallbackClass : animationClass;
}

/**
 * Combine multiple animation classes
 */
export function combineAnimations(...classes: string[]): string {
  return classes.filter(Boolean).join(' ');
}

// ============================================================================
// Stagger Animation Helper
// ============================================================================

/**
 * Generate staggered animation delay for list items
 * @param index - Item index in the list
 * @param baseDelay - Base delay in milliseconds (default: 50)
 * @param maxDelay - Maximum delay in milliseconds (default: 300)
 */
export function getStaggerDelay(
  index: number,
  baseDelay: number = 50,
  maxDelay: number = 300
): string {
  if (prefersReducedMotion()) return '0ms';
  const delay = Math.min(index * baseDelay, maxDelay);
  return `${delay}ms`;
}

/**
 * Create inline style for staggered animations
 */
export function staggerStyle(index: number): React.CSSProperties {
  return {
    animationDelay: getStaggerDelay(index),
  };
}

// ============================================================================
// Common Animation Variants (for inline styles)
// ============================================================================

export const animationVariants = {
  /**
   * Fade in animation
   */
  fadeIn: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    transition: { duration: 0.25 },
  },

  /**
   * Fade in and slide up
   */
  fadeInUp: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.25 },
  },

  /**
   * Scale in animation
   */
  scaleIn: {
    initial: { opacity: 0, scale: 0.95 },
    animate: { opacity: 1, scale: 1 },
    transition: { duration: 0.2 },
  },

  /**
   * Slide in from right
   */
  slideInRight: {
    initial: { x: '100%' },
    animate: { x: 0 },
    transition: { duration: 0.3 },
  },
} as const;

// ============================================================================
// CSS Variable-based Animations
// ============================================================================

/**
 * Generate CSS custom properties for animations
 */
export function generateAnimationVars(config: {
  duration?: string;
  delay?: string;
  easing?: string;
}): React.CSSProperties {
  return {
    '--animation-duration': config.duration || animationDuration.normal,
    '--animation-delay': config.delay || '0ms',
    '--animation-easing': config.easing || animationEasing.easeInOut,
  } as React.CSSProperties;
}

// ============================================================================
// Performance Optimization
// ============================================================================

/**
 * Classes that optimize animation performance by promoting to GPU
 */
export const performanceClasses = {
  willChange: 'will-change-transform',
  gpu: 'transform-gpu',
  backfaceHidden: 'backface-hidden',
} as const;

/**
 * Apply performance optimizations to animated elements
 */
export function withPerformance(className: string): string {
  return combineAnimations(
    className,
    performanceClasses.gpu
  );
}

// ============================================================================
// Touch & Mobile Optimizations
// ============================================================================

/**
 * Common touch-friendly classes
 */
export const touchClasses = {
  target: 'touch-target', // Ensures 44x44px minimum touch target
  noHighlight: 'no-tap-highlight', // Removes tap highlight on mobile
  all: 'touch-target no-tap-highlight',
} as const;

/**
 * Apply touch optimizations to interactive elements
 */
export function withTouchOptimization(className: string): string {
  return combineAnimations(
    className,
    touchClasses.all
  );
}

// ============================================================================
// Pre-built Component Animations
// ============================================================================

/**
 * Complete animation classes for common components
 */
export const componentAnimations = {
  // Standard card with subtle hover
  card: combineAnimations(
    animationClasses.card.base,
    animationClasses.card.subtle
  ),

  // Interactive clickable card
  cardInteractive: combineAnimations(
    animationClasses.card.base,
    animationClasses.card.interactive
  ),

  // Metric/stat card
  metricCard: combineAnimations(
    animationClasses.metricCard.base,
    animationClasses.metricCard.hover
  ),

  // Interactive metric card
  metricCardInteractive: combineAnimations(
    animationClasses.metricCard.base,
    animationClasses.metricCard.interactive
  ),
} as const;
