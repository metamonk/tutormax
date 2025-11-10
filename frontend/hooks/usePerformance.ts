'use client';

import { useEffect, useState } from 'react';

interface PerformanceMetrics {
  fcp?: number; // First Contentful Paint
  lcp?: number; // Largest Contentful Paint
  fid?: number; // First Input Delay
  cls?: number; // Cumulative Layout Shift
  ttfb?: number; // Time to First Byte
  navigationTiming?: PerformanceNavigationTiming;
}

export function usePerformance() {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({});

  useEffect(() => {
    if (typeof window === 'undefined' || !('performance' in window)) {
      return;
    }

    // Get navigation timing
    const navTiming = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    if (navTiming) {
      setMetrics(prev => ({
        ...prev,
        ttfb: navTiming.responseStart - navTiming.requestStart,
        navigationTiming: navTiming,
      }));
    }

    // Web Vitals using PerformanceObserver
    try {
      // First Contentful Paint
      const fcpObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.name === 'first-contentful-paint') {
            setMetrics(prev => ({
              ...prev,
              fcp: entry.startTime,
            }));
          }
        }
      });
      fcpObserver.observe({ entryTypes: ['paint'] });

      // Largest Contentful Paint
      const lcpObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1];
        setMetrics(prev => ({
          ...prev,
          lcp: lastEntry.startTime,
        }));
      });
      lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });

      // First Input Delay
      const fidObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          const fidEntry = entry as PerformanceEventTiming;
          setMetrics(prev => ({
            ...prev,
            fid: fidEntry.processingStart - fidEntry.startTime,
          }));
        }
      });
      fidObserver.observe({ entryTypes: ['first-input'] });

      // Cumulative Layout Shift
      let clsValue = 0;
      const clsObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          const layoutShiftEntry = entry as any;
          if (!layoutShiftEntry.hadRecentInput) {
            clsValue += layoutShiftEntry.value;
            setMetrics(prev => ({
              ...prev,
              cls: clsValue,
            }));
          }
        }
      });
      clsObserver.observe({ entryTypes: ['layout-shift'] });

      return () => {
        fcpObserver.disconnect();
        lcpObserver.disconnect();
        fidObserver.disconnect();
        clsObserver.disconnect();
      };
    } catch (error) {
      console.error('Performance monitoring error:', error);
    }
  }, []);

  return metrics;
}

// Helper to get performance score
export function getPerformanceScore(metrics: PerformanceMetrics): number {
  let score = 100;

  // LCP: Good < 2.5s, Needs Improvement < 4s, Poor > 4s
  if (metrics.lcp) {
    if (metrics.lcp > 4000) score -= 30;
    else if (metrics.lcp > 2500) score -= 15;
  }

  // FID: Good < 100ms, Needs Improvement < 300ms, Poor > 300ms
  if (metrics.fid) {
    if (metrics.fid > 300) score -= 25;
    else if (metrics.fid > 100) score -= 10;
  }

  // CLS: Good < 0.1, Needs Improvement < 0.25, Poor > 0.25
  if (metrics.cls) {
    if (metrics.cls > 0.25) score -= 25;
    else if (metrics.cls > 0.1) score -= 10;
  }

  // FCP: Good < 1.8s, Needs Improvement < 3s, Poor > 3s
  if (metrics.fcp) {
    if (metrics.fcp > 3000) score -= 20;
    else if (metrics.fcp > 1800) score -= 10;
  }

  return Math.max(0, score);
}
