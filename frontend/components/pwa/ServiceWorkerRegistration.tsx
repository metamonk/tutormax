'use client';

import { useEffect } from 'react';
import { registerServiceWorker } from '@/lib/sw-register';

/**
 * Component to handle Service Worker registration
 * Should be included once in the root layout
 */
export function ServiceWorkerRegistration() {
  useEffect(() => {
    // Only register in production
    if (process.env.NODE_ENV !== 'production') {
      console.log('[SW] Service Worker disabled in development');
      return;
    }

    // Register with a small delay to avoid blocking initial page load
    const timeout = setTimeout(() => {
      registerServiceWorker().then(result => {
        if (result.success) {
          console.log('[SW] Service Worker registered successfully');
        } else if (result.error) {
          console.error('[SW] Service Worker registration failed:', result.error);
        }
      });
    }, 1000);

    return () => clearTimeout(timeout);
  }, []);

  return null; // This component doesn't render anything
}
