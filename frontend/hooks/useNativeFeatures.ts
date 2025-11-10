/**
 * React hooks for native device features
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  getCurrentLocation,
  watchLocation,
  clearLocationWatch,
  isBiometricAvailable,
  vibrate,
  canShare,
  shareContent,
  isFullScreen,
  requestFullScreen,
  exitFullScreen,
  getBatteryStatus,
  requestWakeLock,
  releaseWakeLock,
  copyToClipboard as copyToClipboardUtil,
  GeolocationPosition,
  ShareData,
  BatteryStatus,
} from '@/lib/native-features';

// ========== Geolocation Hook ==========

export function useGeolocation(watch = false) {
  const [position, setPosition] = useState<GeolocationPosition | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const getLocation = useCallback(async () => {
    setLoading(true);
    setError(null);

    const pos = await getCurrentLocation();
    if (pos) {
      setPosition(pos);
    } else {
      setError('Failed to get location');
    }

    setLoading(false);
  }, []);

  useEffect(() => {
    if (!watch) return;

    const watchId = watchLocation(
      (pos) => {
        setPosition(pos);
        setError(null);
      },
      {
        enableHighAccuracy: true,
      }
    );

    if (!watchId) {
      setError('Geolocation not supported');
      return;
    }

    return () => {
      clearLocationWatch(watchId);
    };
  }, [watch]);

  return {
    position,
    error,
    loading,
    getLocation,
  };
}

// ========== Biometric Hook ==========

export function useBiometric() {
  const [available, setAvailable] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    isBiometricAvailable().then((isAvailable) => {
      setAvailable(isAvailable);
      setLoading(false);
    });
  }, []);

  return {
    available,
    loading,
  };
}

// ========== Share Hook ==========

export function useShare() {
  const [canShareContent, setCanShareContent] = useState(false);

  useEffect(() => {
    setCanShareContent(canShare());
  }, []);

  const share = useCallback(async (data: ShareData) => {
    return await shareContent(data);
  }, []);

  return {
    canShare: canShareContent,
    share,
  };
}

// ========== Fullscreen Hook ==========

export function useFullScreen(elementRef?: React.RefObject<HTMLElement>) {
  const [fullScreen, setFullScreen] = useState(false);

  useEffect(() => {
    const handleFullScreenChange = () => {
      setFullScreen(isFullScreen());
    };

    document.addEventListener('fullscreenchange', handleFullScreenChange);
    document.addEventListener('webkitfullscreenchange', handleFullScreenChange);
    document.addEventListener('msfullscreenchange', handleFullScreenChange);

    return () => {
      document.removeEventListener('fullscreenchange', handleFullScreenChange);
      document.removeEventListener('webkitfullscreenchange', handleFullScreenChange);
      document.removeEventListener('msfullscreenchange', handleFullScreenChange);
    };
  }, []);

  const enter = useCallback(async () => {
    const element = elementRef?.current;
    const success = await requestFullScreen(element);
    if (success) {
      setFullScreen(true);
    }
    return success;
  }, [elementRef]);

  const exit = useCallback(async () => {
    const success = await exitFullScreen();
    if (success) {
      setFullScreen(false);
    }
    return success;
  }, []);

  const toggle = useCallback(async () => {
    if (fullScreen) {
      return await exit();
    } else {
      return await enter();
    }
  }, [fullScreen, enter, exit]);

  return {
    fullScreen,
    enter,
    exit,
    toggle,
  };
}

// ========== Battery Hook ==========

export function useBattery() {
  const [batteryStatus, setBatteryStatus] = useState<BatteryStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getBatteryStatus().then((status) => {
      setBatteryStatus(status);
      setLoading(false);
    });

    // Battery status can change, so we could add event listeners here
    // but for simplicity, we'll just fetch once
  }, []);

  return {
    battery: batteryStatus,
    loading,
  };
}

// ========== Wake Lock Hook ==========

export function useWakeLock() {
  const [active, setActive] = useState(false);

  const request = useCallback(async () => {
    const success = await requestWakeLock();
    setActive(success);
    return success;
  }, []);

  const release = useCallback(async () => {
    const success = await releaseWakeLock();
    if (success) {
      setActive(false);
    }
    return success;
  }, []);

  useEffect(() => {
    return () => {
      if (active) {
        releaseWakeLock();
      }
    };
  }, [active]);

  return {
    active,
    request,
    release,
  };
}

// ========== Vibration Hook ==========

export function useVibration() {
  const triggerVibration = useCallback((pattern: number | number[]) => {
    return vibrate(pattern);
  }, []);

  const vibrateShort = useCallback(() => {
    return vibrate(50);
  }, []);

  const vibrateLong = useCallback(() => {
    return vibrate(200);
  }, []);

  const vibratePattern = useCallback(() => {
    return vibrate([100, 50, 100, 50, 100]);
  }, []);

  return {
    vibrate: triggerVibration,
    vibrateShort,
    vibrateLong,
    vibratePattern,
  };
}

// ========== Clipboard Hook ==========

export function useClipboard() {
  const [copied, setCopied] = useState(false);

  const copy = useCallback(async (text: string) => {
    const success = await copyToClipboardUtil(text);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
    return success;
  }, []);

  return {
    copy,
    copied,
  };
}

// ========== All-in-one Native Features Hook ==========

export function useNativeFeatures() {
  const geolocation = useGeolocation(false);
  const biometric = useBiometric();
  const share = useShare();
  const fullScreen = useFullScreen();
  const battery = useBattery();
  const wakeLock = useWakeLock();
  const vibration = useVibration();
  const clipboard = useClipboard();

  return {
    geolocation,
    biometric,
    share,
    fullScreen,
    battery,
    wakeLock,
    vibration,
    clipboard,
  };
}
