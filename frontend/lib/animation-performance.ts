/**
 * Animation Performance Utilities
 *
 * Utilities for monitoring and optimizing animation performance in development.
 */

/**
 * Monitor animation performance
 * Only runs in development mode
 */
export function monitorAnimationPerformance() {
  if (process.env.NODE_ENV !== 'development') {
    return;
  }

  if (typeof window === 'undefined') {
    return;
  }

  // Monitor long animation frames
  if ('PerformanceObserver' in window) {
    try {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          // Warn about slow animations (> 16ms = dropped frames)
          if (entry.duration > 16) {
            console.warn(
              `⚠️  Slow animation detected: ${entry.name} took ${entry.duration.toFixed(2)}ms (target: <16ms)`
            );
          }
        }
      });

      observer.observe({ entryTypes: ['measure'] });
    } catch (e) {
      // PerformanceObserver not fully supported
      console.warn('PerformanceObserver not available');
    }
  }

  // Monitor layout shifts during animations
  if ('PerformanceObserver' in window && 'layoutShift' in PerformanceEntry.prototype) {
    try {
      const layoutShiftObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          const layoutShift = entry as any;
          if (layoutShift.value > 0.1) {
            console.warn(
              `⚠️  Layout shift detected: ${layoutShift.value.toFixed(3)} (target: <0.1)`
            );
          }
        }
      });

      layoutShiftObserver.observe({ entryTypes: ['layout-shift'] });
    } catch (e) {
      // Layout shift observation not supported
    }
  }

  // Report at page unload
  window.addEventListener('beforeunload', () => {
    const measures = performance.getEntriesByType('measure');
    const slowAnimations = measures.filter((m) => m.duration > 100);

    if (slowAnimations.length > 0) {
      console.group('🐌 Slow Animations Summary');
      slowAnimations.forEach((measure) => {
        console.log(`${measure.name}: ${measure.duration.toFixed(2)}ms`);
      });
      console.groupEnd();
    }
  });
}

/**
 * Measure animation performance
 * Wraps an animation with performance marks
 */
export function measureAnimation<T>(
  name: string,
  fn: () => T | Promise<T>
): T | Promise<T> {
  if (process.env.NODE_ENV !== 'development') {
    return fn();
  }

  performance.mark(`${name}-start`);

  const result = fn();

  if (result instanceof Promise) {
    return result.then((value) => {
      performance.mark(`${name}-end`);
      performance.measure(name, `${name}-start`, `${name}-end`);
      return value;
    });
  }

  performance.mark(`${name}-end`);
  performance.measure(name, `${name}-start`, `${name}-end`);

  return result;
}

/**
 * Check if animations are causing performance issues
 */
export function checkAnimationPerformance(): {
  fps: number;
  slowAnimations: PerformanceMeasure[];
  layoutShifts: number;
} {
  const measures = performance.getEntriesByType('measure') as PerformanceMeasure[];
  const slowAnimations = measures.filter((m) => m.duration > 16);

  // Estimate FPS based on animation durations
  const avgFrameTime = measures.length > 0
    ? measures.reduce((sum, m) => sum + m.duration, 0) / measures.length
    : 16;

  const fps = Math.round(1000 / avgFrameTime);

  // Get layout shifts
  const layoutShifts = performance.getEntriesByType('layout-shift');
  const totalLayoutShift = layoutShifts.reduce(
    (sum, entry: any) => sum + (entry.value || 0),
    0
  );

  return {
    fps: Math.min(fps, 60),
    slowAnimations,
    layoutShifts: totalLayoutShift,
  };
}

/**
 * Get animation performance report
 */
export function getAnimationReport(): string {
  const { fps, slowAnimations, layoutShifts } = checkAnimationPerformance();

  let report = `📊 Animation Performance Report\n`;
  report += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
  report += `FPS: ${fps} ${fps >= 55 ? '✅' : fps >= 30 ? '⚠️' : '❌'}\n`;
  report += `Layout Shifts: ${layoutShifts.toFixed(3)} ${layoutShifts < 0.1 ? '✅' : '⚠️'}\n`;
  report += `Slow Animations: ${slowAnimations.length} ${slowAnimations.length === 0 ? '✅' : '⚠️'}\n`;

  if (slowAnimations.length > 0) {
    report += `\n🐌 Slow Animations:\n`;
    slowAnimations.forEach((measure) => {
      report += `  • ${measure.name}: ${measure.duration.toFixed(2)}ms\n`;
    });
  }

  return report;
}

/**
 * Log animation performance to console
 */
export function logAnimationPerformance() {
  if (process.env.NODE_ENV !== 'development') {
    return;
  }

  console.log(getAnimationReport());
}

/**
 * Clear animation performance data
 */
export function clearAnimationPerformance() {
  performance.clearMarks();
  performance.clearMeasures();
}

/**
 * React hook to monitor component animation performance
 */
export function useAnimationPerformance(componentName: string) {
  if (process.env.NODE_ENV !== 'development') {
    return;
  }

  if (typeof window === 'undefined') {
    return;
  }

  performance.mark(`${componentName}-mount`);

  return () => {
    performance.mark(`${componentName}-unmount`);
    performance.measure(
      `${componentName}-lifetime`,
      `${componentName}-mount`,
      `${componentName}-unmount`
    );
  };
}
