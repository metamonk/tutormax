'use client';

/**
 * Page Transition Component
 *
 * Provides smooth fade-in animations for page transitions in Next.js App Router.
 * Respects prefers-reduced-motion for accessibility.
 */

import * as React from 'react';
import { usePathname } from 'next/navigation';
import { usePrefersReducedMotion } from '@/hooks/use-animations';

interface PageTransitionProps {
  children: React.ReactNode;
  /**
   * Animation variant to use
   * @default "fade"
   */
  variant?: 'fade' | 'slide-up' | 'slide-down' | 'scale';
  /**
   * Animation duration in milliseconds
   * @default 250
   */
  duration?: number;
  /**
   * Optional className to apply to the wrapper
   */
  className?: string;
}

export function PageTransition({
  children,
  variant = 'fade',
  duration = 250,
  className,
}: PageTransitionProps) {
  const pathname = usePathname();
  const prefersReducedMotion = usePrefersReducedMotion();
  const [isVisible, setIsVisible] = React.useState(true);

  React.useEffect(() => {
    // Skip animation if user prefers reduced motion
    if (prefersReducedMotion) {
      setIsVisible(true);
      return;
    }

    // Trigger fade out/in on route change
    setIsVisible(false);
    const timeout = setTimeout(() => setIsVisible(true), 50);

    return () => clearTimeout(timeout);
  }, [pathname, prefersReducedMotion]);

  const animationClasses = React.useMemo(() => {
    if (prefersReducedMotion) {
      return '';
    }

    const baseClasses = 'transition-all transform-gpu';

    if (!isVisible) {
      return `${baseClasses} opacity-0`;
    }

    switch (variant) {
      case 'fade':
        return `${baseClasses} animate-fade-in`;
      case 'slide-up':
        return `${baseClasses} animate-slide-in-bottom`;
      case 'slide-down':
        return `${baseClasses} animate-slide-in-top`;
      case 'scale':
        return `${baseClasses} animate-scale-in`;
      default:
        return `${baseClasses} animate-fade-in`;
    }
  }, [isVisible, variant, prefersReducedMotion]);

  return (
    <div
      className={`${animationClasses} ${className || ''}`}
      style={{
        animationDuration: prefersReducedMotion ? '0ms' : `${duration}ms`,
      }}
    >
      {children}
    </div>
  );
}

/**
 * Staggered List Animation Component
 *
 * Animates list items with a stagger effect
 */
export function StaggeredList({
  children,
  className,
  staggerDelay = 50,
  maxDelay = 300,
}: {
  children: React.ReactNode;
  className?: string;
  staggerDelay?: number;
  maxDelay?: number;
}) {
  const prefersReducedMotion = usePrefersReducedMotion();

  if (prefersReducedMotion) {
    return <div className={className}>{children}</div>;
  }

  const childrenArray = React.Children.toArray(children);

  return (
    <div className={className}>
      {childrenArray.map((child, index) => {
        const delay = Math.min(index * staggerDelay, maxDelay);

        return (
          <div
            key={index}
            className="animate-slide-in-bottom"
            style={{
              animationDelay: `${delay}ms`,
              animationFillMode: 'both',
            }}
          >
            {child}
          </div>
        );
      })}
    </div>
  );
}

/**
 * Staggered Grid Animation Component
 *
 * Animates grid items with a stagger effect
 */
export function StaggeredGrid({
  children,
  className,
  staggerDelay = 50,
  maxDelay = 400,
}: {
  children: React.ReactNode;
  className?: string;
  staggerDelay?: number;
  maxDelay?: number;
}) {
  const prefersReducedMotion = usePrefersReducedMotion();

  if (prefersReducedMotion) {
    return <div className={className}>{children}</div>;
  }

  const childrenArray = React.Children.toArray(children);

  return (
    <div className={className}>
      {childrenArray.map((child, index) => {
        const delay = Math.min(index * staggerDelay, maxDelay);

        return (
          <div
            key={index}
            className="animate-scale-in"
            style={{
              animationDelay: `${delay}ms`,
              animationFillMode: 'both',
            }}
          >
            {child}
          </div>
        );
      })}
    </div>
  );
}

/**
 * Fade In When Visible Component
 *
 * Animates element when it enters the viewport using Intersection Observer
 */
export function FadeInWhenVisible({
  children,
  className,
  threshold = 0.1,
  rootMargin = '0px',
}: {
  children: React.ReactNode;
  className?: string;
  threshold?: number;
  rootMargin?: string;
}) {
  const prefersReducedMotion = usePrefersReducedMotion();
  const [isVisible, setIsVisible] = React.useState(false);
  const ref = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (prefersReducedMotion) {
      setIsVisible(true);
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          // Unobserve after first intersection
          observer.disconnect();
        }
      },
      {
        threshold,
        rootMargin,
      }
    );

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => {
      observer.disconnect();
    };
  }, [threshold, rootMargin, prefersReducedMotion]);

  return (
    <div
      ref={ref}
      className={`transition-all duration-500 transform-gpu ${
        isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
      } ${className || ''}`}
    >
      {children}
    </div>
  );
}
