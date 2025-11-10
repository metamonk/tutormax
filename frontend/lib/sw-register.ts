/**
 * Service Worker Registration Utility
 * Handles registration, updates, and lifecycle events
 */

export interface ServiceWorkerRegistrationResult {
  success: boolean;
  registration?: ServiceWorkerRegistration;
  error?: Error;
}

/**
 * Register the service worker
 */
export async function registerServiceWorker(): Promise<ServiceWorkerRegistrationResult> {
  // Only register in production and if service workers are supported
  if (
    typeof window === 'undefined' ||
    !('serviceWorker' in navigator) ||
    process.env.NODE_ENV !== 'production'
  ) {
    return { success: false };
  }

  try {
    const registration = await navigator.serviceWorker.register('/sw.js', {
      scope: '/',
    });

    console.log('[SW] Service Worker registered successfully:', registration.scope);

    // Check for updates
    registration.addEventListener('updatefound', () => {
      const newWorker = registration.installing;
      if (!newWorker) return;

      console.log('[SW] Update found, installing new version...');

      newWorker.addEventListener('statechange', () => {
        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
          console.log('[SW] New version available, ready to activate');

          // Notify the app about the update
          window.dispatchEvent(new CustomEvent('sw-update-available', {
            detail: { registration }
          }));
        }
      });
    });

    // Check for updates periodically (every hour)
    setInterval(() => {
      registration.update().catch(err => {
        console.error('[SW] Update check failed:', err);
      });
    }, 60 * 60 * 1000);

    return { success: true, registration };
  } catch (error) {
    console.error('[SW] Service Worker registration failed:', error);
    return {
      success: false,
      error: error instanceof Error ? error : new Error('Unknown error')
    };
  }
}

/**
 * Unregister all service workers
 */
export async function unregisterServiceWorker(): Promise<boolean> {
  if (typeof window === 'undefined' || !('serviceWorker' in navigator)) {
    return false;
  }

  try {
    const registration = await navigator.serviceWorker.getRegistration();
    if (registration) {
      const result = await registration.unregister();
      console.log('[SW] Service Worker unregistered:', result);
      return result;
    }
    return false;
  } catch (error) {
    console.error('[SW] Unregister failed:', error);
    return false;
  }
}

/**
 * Skip waiting and activate new service worker immediately
 */
export function skipWaiting(): void {
  if (typeof window === 'undefined' || !('serviceWorker' in navigator)) {
    return;
  }

  navigator.serviceWorker.getRegistration().then(registration => {
    if (registration?.waiting) {
      registration.waiting.postMessage({ type: 'SKIP_WAITING' });
    }
  });
}

/**
 * Request service worker to cache specific URLs
 */
export function cacheUrls(urls: string[]): void {
  if (typeof window === 'undefined' || !('serviceWorker' in navigator)) {
    return;
  }

  navigator.serviceWorker.controller?.postMessage({
    type: 'CACHE_URLS',
    urls,
  });
}

/**
 * Clear all caches
 */
export function clearCache(): void {
  if (typeof window === 'undefined' || !('serviceWorker' in navigator)) {
    return;
  }

  navigator.serviceWorker.controller?.postMessage({
    type: 'CLEAR_CACHE',
  });
}

/**
 * Check if service worker is registered and active
 */
export async function isServiceWorkerActive(): Promise<boolean> {
  if (typeof window === 'undefined' || !('serviceWorker' in navigator)) {
    return false;
  }

  try {
    const registration = await navigator.serviceWorker.getRegistration();
    return registration?.active !== undefined;
  } catch {
    return false;
  }
}

/**
 * Get service worker registration info
 */
export async function getServiceWorkerInfo() {
  if (typeof window === 'undefined' || !('serviceWorker' in navigator)) {
    return null;
  }

  try {
    const registration = await navigator.serviceWorker.getRegistration();
    if (!registration) return null;

    return {
      scope: registration.scope,
      updateViaCache: registration.updateViaCache,
      hasActive: !!registration.active,
      hasWaiting: !!registration.waiting,
      hasInstalling: !!registration.installing,
    };
  } catch {
    return null;
  }
}
