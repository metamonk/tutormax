/**
 * PWA Utilities for TutorMax
 * Handles service worker registration, push notifications, and offline capabilities
 */

export interface BeforeInstallPromptEvent extends Event {
  readonly platforms: string[];
  readonly userChoice: Promise<{
    outcome: 'accepted' | 'dismissed';
    platform: string;
  }>;
  prompt(): Promise<void>;
}

export interface NetworkInformation extends EventTarget {
  readonly effectiveType: 'slow-2g' | '2g' | '3g' | '4g';
  readonly downlink: number;
  readonly rtt: number;
  readonly saveData: boolean;
  onchange: EventListener | null;
}

/**
 * Check if the app is running as a PWA
 */
export const isPWA = (): boolean => {
  if (typeof window === 'undefined') return false;
  return (
    window.matchMedia('(display-mode: standalone)').matches ||
    (window.navigator as any).standalone === true ||
    document.referrer.includes('android-app://')
  );
};

/**
 * Check if the browser supports PWA installation
 */
export const canInstallPWA = (): boolean => {
  if (typeof window === 'undefined') return false;
  return 'BeforeInstallPromptEvent' in window || 'standalone' in window.navigator;
};

/**
 * Get network information
 */
export const getNetworkInfo = (): NetworkInformation | null => {
  if (typeof navigator === 'undefined') return null;
  return (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection || null;
};

/**
 * Check if the user is on a slow connection
 */
export const isSlowConnection = (): boolean => {
  const connection = getNetworkInfo();
  if (!connection) return false;
  return connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g';
};

/**
 * Check if the user has data saver enabled
 */
export const hasDataSaver = (): boolean => {
  const connection = getNetworkInfo();
  return connection?.saveData || false;
};

/**
 * Request notification permission
 */
export const requestNotificationPermission = async (): Promise<NotificationPermission> => {
  if (!('Notification' in window)) {
    throw new Error('This browser does not support notifications');
  }
  return await Notification.requestPermission();
};

/**
 * Show a notification
 */
export const showNotification = async (title: string, options?: NotificationOptions): Promise<void> => {
  if (!('Notification' in window)) {
    console.warn('This browser does not support notifications');
    return;
  }

  if (Notification.permission === 'granted') {
    if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
      const registration = await navigator.serviceWorker.ready;
      await registration.showNotification(title, {
        icon: '/icon-192x192.png',
        badge: '/icon-72x72.png',
        ...(options as any), // vibrate is supported but not in TypeScript types
      });
    } else {
      new Notification(title, {
        icon: '/icon-192x192.png',
        ...options,
      });
    }
  }
};

/**
 * Register for push notifications
 */
export const subscribeToPushNotifications = async (): Promise<PushSubscription | null> => {
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
    console.warn('Push notifications are not supported');
    return null;
  }

  try {
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY,
    });
    return subscription;
  } catch (error) {
    console.error('Failed to subscribe to push notifications:', error);
    return null;
  }
};

/**
 * Check if geolocation is available
 */
export const hasGeolocation = (): boolean => {
  return 'geolocation' in navigator;
};

/**
 * Get user's current location
 */
export const getCurrentLocation = (): Promise<GeolocationPosition> => {
  return new Promise((resolve, reject) => {
    if (!hasGeolocation()) {
      reject(new Error('Geolocation is not supported'));
      return;
    }
    navigator.geolocation.getCurrentPosition(resolve, reject, {
      enableHighAccuracy: true,
      timeout: 5000,
      maximumAge: 0,
    });
  });
};

/**
 * Check if camera access is available
 */
export const hasCameraAccess = (): boolean => {
  return 'mediaDevices' in navigator && 'getUserMedia' in navigator.mediaDevices;
};

/**
 * Request camera access
 */
export const requestCameraAccess = async (): Promise<MediaStream> => {
  if (!hasCameraAccess()) {
    throw new Error('Camera access is not supported');
  }
  return await navigator.mediaDevices.getUserMedia({ video: true });
};

/**
 * Check if biometric authentication is available
 */
export const hasBiometricAuth = (): boolean => {
  if (typeof window === 'undefined') return false;
  return 'credentials' in navigator && 'PublicKeyCredential' in window;
};

/**
 * Request biometric authentication
 */
export const authenticateWithBiometrics = async (): Promise<boolean> => {
  if (!hasBiometricAuth()) {
    throw new Error('Biometric authentication is not supported');
  }

  try {
    const publicKeyCredentialRequestOptions: CredentialRequestOptions = {
      publicKey: {
        challenge: new Uint8Array(32),
        timeout: 60000,
        userVerification: 'required',
      },
    };

    const credential = await navigator.credentials.get(publicKeyCredentialRequestOptions);
    return !!credential;
  } catch (error) {
    console.error('Biometric authentication failed:', error);
    return false;
  }
};

/**
 * Share content using Web Share API
 */
export const shareContent = async (data: ShareData): Promise<boolean> => {
  if (!('share' in navigator)) {
    console.warn('Web Share API is not supported');
    return false;
  }

  try {
    await navigator.share(data);
    return true;
  } catch (error) {
    if ((error as Error).name !== 'AbortError') {
      console.error('Error sharing:', error);
    }
    return false;
  }
};

/**
 * Vibrate the device
 */
export const vibrate = (pattern: number | number[]): boolean => {
  if (!('vibrate' in navigator)) {
    return false;
  }
  return navigator.vibrate(pattern);
};

/**
 * Check if device is in landscape mode
 */
export const isLandscape = (): boolean => {
  if (typeof window === 'undefined') return false;
  return window.matchMedia('(orientation: landscape)').matches;
};

/**
 * Get device pixel ratio
 */
export const getDevicePixelRatio = (): number => {
  if (typeof window === 'undefined') return 1;
  return window.devicePixelRatio || 1;
};

/**
 * Check if device supports touch
 */
export const hasTouch = (): boolean => {
  if (typeof window === 'undefined') return false;
  return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
};

/**
 * Preload a resource
 */
export const preloadResource = (url: string, type: 'image' | 'script' | 'style' | 'font'): void => {
  const link = document.createElement('link');
  link.rel = 'preload';
  link.as = type;
  link.href = url;
  if (type === 'font') {
    link.crossOrigin = 'anonymous';
  }
  document.head.appendChild(link);
};

/**
 * Lazy load an image
 */
export const lazyLoadImage = (src: string): Promise<HTMLImageElement> => {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = src;
  });
};
