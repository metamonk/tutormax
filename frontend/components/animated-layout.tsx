'use client';

/**
 * Animated Layout Component
 *
 * A layout wrapper that provides page transition animations.
 * Can be used in Next.js App Router layouts or as a wrapper component.
 *
 * Usage in layout.tsx:
 * ```tsx
 * import { AnimatedLayout } from '@/components/animated-layout';
 *
 * export default function Layout({ children }) {
 *   return <AnimatedLayout>{children}</AnimatedLayout>;
 * }
 * ```
 */

import * as React from 'react';
import { PageTransition } from './page-transition';

interface AnimatedLayoutProps {
  children: React.ReactNode;
  /**
   * Animation variant for page transitions
   * @default "fade"
   */
  variant?: 'fade' | 'slide-up' | 'slide-down' | 'scale';
  /**
   * Whether to enable page transitions
   * @default true
   */
  enableTransitions?: boolean;
}

export function AnimatedLayout({
  children,
  variant = 'fade',
  enableTransitions = true,
}: AnimatedLayoutProps) {
  if (!enableTransitions) {
    return <>{children}</>;
  }

  return (
    <PageTransition variant={variant}>
      {children}
    </PageTransition>
  );
}
