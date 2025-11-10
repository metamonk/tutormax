'use client';

import { useEffect, useState } from 'react';
import { getNetworkInfo, isSlowConnection, hasDataSaver, NetworkInformation } from '@/lib/pwa-utils';

interface NetworkStatus {
  online: boolean;
  effectiveType: 'slow-2g' | '2g' | '3g' | '4g' | 'unknown';
  downlink: number;
  rtt: number;
  saveData: boolean;
  isSlowConnection: boolean;
}

export function useNetworkStatus(): NetworkStatus {
  const [status, setStatus] = useState<NetworkStatus>(() => {
    const connection = getNetworkInfo();
    return {
      online: typeof navigator !== 'undefined' ? navigator.onLine : true,
      effectiveType: connection?.effectiveType || 'unknown',
      downlink: connection?.downlink || 0,
      rtt: connection?.rtt || 0,
      saveData: hasDataSaver(),
      isSlowConnection: isSlowConnection(),
    };
  });

  useEffect(() => {
    const updateOnlineStatus = () => {
      const connection = getNetworkInfo();
      setStatus({
        online: navigator.onLine,
        effectiveType: connection?.effectiveType || 'unknown',
        downlink: connection?.downlink || 0,
        rtt: connection?.rtt || 0,
        saveData: hasDataSaver(),
        isSlowConnection: isSlowConnection(),
      });
    };

    const updateConnectionStatus = () => {
      const connection = getNetworkInfo();
      setStatus(prev => ({
        ...prev,
        effectiveType: connection?.effectiveType || 'unknown',
        downlink: connection?.downlink || 0,
        rtt: connection?.rtt || 0,
        saveData: hasDataSaver(),
        isSlowConnection: isSlowConnection(),
      }));
    };

    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);

    const connection = getNetworkInfo();
    if (connection) {
      connection.addEventListener('change', updateConnectionStatus);
    }

    return () => {
      window.removeEventListener('online', updateOnlineStatus);
      window.removeEventListener('offline', updateOnlineStatus);
      if (connection) {
        connection.removeEventListener('change', updateConnectionStatus);
      }
    };
  }, []);

  return status;
}
