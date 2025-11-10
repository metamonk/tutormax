'use client';

import { useEffect, useState, useCallback } from 'react';

interface ServiceWorkerState {
  isSupported: boolean;
  isRegistered: boolean;
  isUpdateAvailable: boolean;
  registration: ServiceWorkerRegistration | null;
}

export function useServiceWorker() {
  const [state, setState] = useState<ServiceWorkerState>({
    isSupported: false,
    isRegistered: false,
    isUpdateAvailable: false,
    registration: null,
  });

  useEffect(() => {
    if (typeof window === 'undefined' || !('serviceWorker' in navigator)) {
      return;
    }

    setState(prev => ({ ...prev, isSupported: true }));

    const checkRegistration = async () => {
      try {
        const registration = await navigator.serviceWorker.getRegistration();
        if (registration) {
          setState(prev => ({
            ...prev,
            isRegistered: true,
            registration,
          }));

          // Check for updates
          registration.addEventListener('updatefound', () => {
            const newWorker = registration.installing;
            if (newWorker) {
              newWorker.addEventListener('statechange', () => {
                if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                  setState(prev => ({ ...prev, isUpdateAvailable: true }));
                }
              });
            }
          });
        }
      } catch (error) {
        console.error('Service worker registration check failed:', error);
      }
    };

    checkRegistration();

    // Listen for controller changes
    const handleControllerChange = () => {
      window.location.reload();
    };

    // Listen for custom update event from sw-register
    const handleUpdateAvailable = () => {
      setState(prev => ({ ...prev, isUpdateAvailable: true }));
    };

    navigator.serviceWorker.addEventListener('controllerchange', handleControllerChange);
    window.addEventListener('sw-update-available', handleUpdateAvailable);

    return () => {
      navigator.serviceWorker.removeEventListener('controllerchange', handleControllerChange);
      window.removeEventListener('sw-update-available', handleUpdateAvailable);
    };
  }, []);

  const update = useCallback(async () => {
    if (state.registration) {
      await state.registration.update();
    }
  }, [state.registration]);

  const skipWaiting = useCallback(async () => {
    if (state.registration?.waiting) {
      state.registration.waiting.postMessage({ type: 'SKIP_WAITING' });
    }
  }, [state.registration]);

  return {
    ...state,
    update,
    skipWaiting,
  };
}
