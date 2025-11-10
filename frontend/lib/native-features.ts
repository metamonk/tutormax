/**
 * Native device feature utilities for PWA
 * Provides access to camera, geolocation, biometric auth, and other native APIs
 */

// ========== Camera Access ==========

export interface CameraOptions {
  facingMode?: 'user' | 'environment';
  width?: number;
  height?: number;
}

/**
 * Request camera access and get media stream
 */
export async function requestCameraAccess(options: CameraOptions = {}): Promise<MediaStream | null> {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    console.error('[Native] Camera API not supported');
    return null;
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: options.facingMode || 'user',
        width: options.width || 1280,
        height: options.height || 720,
      },
    });

    console.log('[Native] Camera access granted');
    return stream;
  } catch (error) {
    console.error('[Native] Camera access denied:', error);
    return null;
  }
}

/**
 * Capture image from camera stream
 */
export async function captureImageFromCamera(options: CameraOptions = {}): Promise<Blob | null> {
  const stream = await requestCameraAccess(options);
  if (!stream) return null;

  return new Promise((resolve) => {
    const video = document.createElement('video');
    video.srcObject = stream;
    video.play();

    video.onloadedmetadata = () => {
      const canvas = document.createElement('canvas');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      const ctx = canvas.getContext('2d');
      if (!ctx) {
        stream.getTracks().forEach(track => track.stop());
        resolve(null);
        return;
      }

      ctx.drawImage(video, 0, 0);

      canvas.toBlob((blob) => {
        stream.getTracks().forEach(track => track.stop());
        resolve(blob);
      }, 'image/jpeg', 0.9);
    };
  });
}

/**
 * Stop camera stream
 */
export function stopCameraStream(stream: MediaStream): void {
  stream.getTracks().forEach(track => track.stop());
  console.log('[Native] Camera stream stopped');
}

// ========== Geolocation ==========

export interface GeolocationPosition {
  latitude: number;
  longitude: number;
  accuracy: number;
  altitude: number | null;
  altitudeAccuracy: number | null;
  heading: number | null;
  speed: number | null;
}

export interface GeolocationOptions {
  enableHighAccuracy?: boolean;
  timeout?: number;
  maximumAge?: number;
}

/**
 * Get current geolocation
 */
export async function getCurrentLocation(
  options: GeolocationOptions = {}
): Promise<GeolocationPosition | null> {
  if (!navigator.geolocation) {
    console.error('[Native] Geolocation API not supported');
    return null;
  }

  return new Promise((resolve) => {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        console.log('[Native] Location obtained');
        resolve({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
          altitude: position.coords.altitude,
          altitudeAccuracy: position.coords.altitudeAccuracy,
          heading: position.coords.heading,
          speed: position.coords.speed,
        });
      },
      (error) => {
        console.error('[Native] Location error:', error.message);
        resolve(null);
      },
      {
        enableHighAccuracy: options.enableHighAccuracy ?? true,
        timeout: options.timeout ?? 10000,
        maximumAge: options.maximumAge ?? 0,
      }
    );
  });
}

/**
 * Watch location changes
 */
export function watchLocation(
  callback: (position: GeolocationPosition) => void,
  options: GeolocationOptions = {}
): number | null {
  if (!navigator.geolocation) {
    console.error('[Native] Geolocation API not supported');
    return null;
  }

  const watchId = navigator.geolocation.watchPosition(
    (position) => {
      callback({
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy: position.coords.accuracy,
        altitude: position.coords.altitude,
        altitudeAccuracy: position.coords.altitudeAccuracy,
        heading: position.coords.heading,
        speed: position.coords.speed,
      });
    },
    (error) => {
      console.error('[Native] Location watch error:', error.message);
    },
    {
      enableHighAccuracy: options.enableHighAccuracy ?? true,
      timeout: options.timeout ?? 10000,
      maximumAge: options.maximumAge ?? 0,
    }
  );

  console.log('[Native] Location watch started');
  return watchId;
}

/**
 * Clear location watch
 */
export function clearLocationWatch(watchId: number): void {
  if (navigator.geolocation) {
    navigator.geolocation.clearWatch(watchId);
    console.log('[Native] Location watch cleared');
  }
}

// ========== Biometric Authentication (WebAuthn) ==========

export interface BiometricCredential {
  id: string;
  rawId: ArrayBuffer;
  type: string;
}

/**
 * Check if biometric authentication is available
 */
export async function isBiometricAvailable(): Promise<boolean> {
  if (!window.PublicKeyCredential) {
    return false;
  }

  try {
    const available = await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable();
    console.log('[Native] Biometric available:', available);
    return available;
  } catch (error) {
    console.error('[Native] Biometric check failed:', error);
    return false;
  }
}

/**
 * Register biometric credential
 */
export async function registerBiometric(
  userId: string,
  userName: string
): Promise<BiometricCredential | null> {
  if (!(await isBiometricAvailable())) {
    console.error('[Native] Biometric not available');
    return null;
  }

  try {
    const challenge = crypto.getRandomValues(new Uint8Array(32));

    const credential = await navigator.credentials.create({
      publicKey: {
        challenge,
        rp: {
          name: 'TutorMax',
          id: window.location.hostname,
        },
        user: {
          id: new TextEncoder().encode(userId),
          name: userName,
          displayName: userName,
        },
        pubKeyCredParams: [
          { type: 'public-key', alg: -7 }, // ES256
          { type: 'public-key', alg: -257 }, // RS256
        ],
        authenticatorSelection: {
          authenticatorAttachment: 'platform',
          userVerification: 'required',
        },
        timeout: 60000,
      },
    }) as PublicKeyCredential | null;

    if (!credential) {
      console.error('[Native] Failed to create credential');
      return null;
    }

    console.log('[Native] Biometric registered');
    return {
      id: credential.id,
      rawId: credential.rawId,
      type: credential.type,
    };
  } catch (error) {
    console.error('[Native] Biometric registration failed:', error);
    return null;
  }
}

/**
 * Authenticate with biometric
 */
export async function authenticateWithBiometric(
  credentialId: string
): Promise<boolean> {
  if (!(await isBiometricAvailable())) {
    console.error('[Native] Biometric not available');
    return false;
  }

  try {
    const challenge = crypto.getRandomValues(new Uint8Array(32));

    const credential = await navigator.credentials.get({
      publicKey: {
        challenge,
        allowCredentials: [
          {
            type: 'public-key',
            id: Uint8Array.from(atob(credentialId), c => c.charCodeAt(0)),
          },
        ],
        timeout: 60000,
        userVerification: 'required',
      },
    });

    const success = credential !== null;
    console.log('[Native] Biometric authentication:', success ? 'success' : 'failed');
    return success;
  } catch (error) {
    console.error('[Native] Biometric authentication failed:', error);
    return false;
  }
}

// ========== Vibration API ==========

/**
 * Trigger device vibration
 * @param pattern - Vibration pattern in milliseconds (number or array)
 */
export function vibrate(pattern: number | number[]): boolean {
  if (!navigator.vibrate) {
    console.log('[Native] Vibration API not supported');
    return false;
  }

  const success = navigator.vibrate(pattern);
  console.log('[Native] Vibration triggered:', success);
  return success;
}

/**
 * Stop vibration
 */
export function stopVibration(): boolean {
  if (!navigator.vibrate) {
    return false;
  }

  return navigator.vibrate(0);
}

// ========== Web Share API ==========

export interface ShareData {
  title?: string;
  text?: string;
  url?: string;
  files?: File[];
}

/**
 * Check if Web Share API is available
 */
export function canShare(data?: ShareData): boolean {
  if (!navigator.share) {
    return false;
  }

  if (data && navigator.canShare) {
    return navigator.canShare(data);
  }

  return true;
}

/**
 * Share content using native share dialog
 */
export async function shareContent(data: ShareData): Promise<boolean> {
  if (!canShare(data)) {
    console.error('[Native] Share API not supported');
    return false;
  }

  try {
    await navigator.share(data);
    console.log('[Native] Content shared successfully');
    return true;
  } catch (error) {
    if ((error as Error).name === 'AbortError') {
      console.log('[Native] Share cancelled by user');
    } else {
      console.error('[Native] Share failed:', error);
    }
    return false;
  }
}

// ========== Full Screen API ==========

/**
 * Request full screen mode
 */
export async function requestFullScreen(element?: HTMLElement): Promise<boolean> {
  const target = element || document.documentElement;

  try {
    if (target.requestFullscreen) {
      await target.requestFullscreen();
    } else if ((target as any).webkitRequestFullscreen) {
      await (target as any).webkitRequestFullscreen();
    } else if ((target as any).msRequestFullscreen) {
      await (target as any).msRequestFullscreen();
    } else {
      console.error('[Native] Fullscreen API not supported');
      return false;
    }

    console.log('[Native] Fullscreen mode enabled');
    return true;
  } catch (error) {
    console.error('[Native] Fullscreen request failed:', error);
    return false;
  }
}

/**
 * Exit full screen mode
 */
export async function exitFullScreen(): Promise<boolean> {
  try {
    if (document.exitFullscreen) {
      await document.exitFullscreen();
    } else if ((document as any).webkitExitFullscreen) {
      await (document as any).webkitExitFullscreen();
    } else if ((document as any).msExitFullscreen) {
      await (document as any).msExitFullscreen();
    } else {
      console.error('[Native] Fullscreen API not supported');
      return false;
    }

    console.log('[Native] Fullscreen mode exited');
    return true;
  } catch (error) {
    console.error('[Native] Fullscreen exit failed:', error);
    return false;
  }
}

/**
 * Check if currently in full screen mode
 */
export function isFullScreen(): boolean {
  return !!(
    document.fullscreenElement ||
    (document as any).webkitFullscreenElement ||
    (document as any).msFullscreenElement
  );
}

// ========== Clipboard API ==========

/**
 * Copy text to clipboard
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text);
      console.log('[Native] Text copied to clipboard');
      return true;
    }

    // Fallback for older browsers
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    const success = document.execCommand('copy');
    document.body.removeChild(textarea);

    console.log('[Native] Text copied to clipboard (fallback)');
    return success;
  } catch (error) {
    console.error('[Native] Copy to clipboard failed:', error);
    return false;
  }
}

/**
 * Read text from clipboard
 */
export async function readFromClipboard(): Promise<string | null> {
  try {
    if (navigator.clipboard && navigator.clipboard.readText) {
      const text = await navigator.clipboard.readText();
      console.log('[Native] Text read from clipboard');
      return text;
    }

    console.error('[Native] Clipboard read not supported');
    return null;
  } catch (error) {
    console.error('[Native] Read from clipboard failed:', error);
    return null;
  }
}

// ========== Battery Status API ==========

export interface BatteryStatus {
  level: number; // 0.0 to 1.0
  charging: boolean;
  chargingTime: number; // seconds until fully charged
  dischargingTime: number; // seconds until empty
}

/**
 * Get battery status
 */
export async function getBatteryStatus(): Promise<BatteryStatus | null> {
  if (!('getBattery' in navigator)) {
    console.log('[Native] Battery Status API not supported');
    return null;
  }

  try {
    const battery = await (navigator as any).getBattery();
    return {
      level: battery.level,
      charging: battery.charging,
      chargingTime: battery.chargingTime,
      dischargingTime: battery.dischargingTime,
    };
  } catch (error) {
    console.error('[Native] Battery status failed:', error);
    return null;
  }
}

// ========== Wake Lock API ==========

let wakeLock: any = null;

/**
 * Request wake lock to keep screen on
 */
export async function requestWakeLock(): Promise<boolean> {
  if (!('wakeLock' in navigator)) {
    console.log('[Native] Wake Lock API not supported');
    return false;
  }

  try {
    wakeLock = await (navigator as any).wakeLock.request('screen');
    console.log('[Native] Wake lock acquired');

    wakeLock.addEventListener('release', () => {
      console.log('[Native] Wake lock released');
    });

    return true;
  } catch (error) {
    console.error('[Native] Wake lock request failed:', error);
    return false;
  }
}

/**
 * Release wake lock
 */
export async function releaseWakeLock(): Promise<boolean> {
  if (!wakeLock) {
    return false;
  }

  try {
    await wakeLock.release();
    wakeLock = null;
    console.log('[Native] Wake lock released');
    return true;
  } catch (error) {
    console.error('[Native] Wake lock release failed:', error);
    return false;
  }
}
