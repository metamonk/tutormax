'use client';

import { useNetworkStatus } from '@/hooks/useNetworkStatus';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { WifiOff, Wifi } from 'lucide-react';
import { useEffect, useState } from 'react';

export function OfflineIndicator() {
  const { online, isSlowConnection, effectiveType } = useNetworkStatus();
  const [showReconnected, setShowReconnected] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (online && showReconnected) {
      const timer = setTimeout(() => setShowReconnected(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [online, showReconnected]);

  useEffect(() => {
    if (online && !showReconnected) {
      setShowReconnected(true);
    }
  }, [online]);

  // Don't render anything until mounted to avoid hydration mismatch
  if (!mounted) {
    return null;
  }

  if (online && !isSlowConnection && !showReconnected) {
    return null;
  }

  return (
    <div className="fixed top-4 left-4 right-4 z-50 animate-in slide-in-from-top-5">
      {!online ? (
        <Alert variant="destructive" className="shadow-lg">
          <WifiOff className="h-4 w-4" />
          <AlertDescription>
            You're offline. Some features may be unavailable.
          </AlertDescription>
        </Alert>
      ) : showReconnected ? (
        <Alert className="shadow-lg bg-green-50 dark:bg-green-950 border-green-500">
          <Wifi className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-600 dark:text-green-400">
            You're back online!
          </AlertDescription>
        </Alert>
      ) : isSlowConnection ? (
        <Alert className="shadow-lg bg-yellow-50 dark:bg-yellow-950 border-yellow-500">
          <Wifi className="h-4 w-4 text-yellow-600" />
          <AlertDescription className="text-yellow-600 dark:text-yellow-400">
            Slow connection detected ({effectiveType}). Loading may be slower.
          </AlertDescription>
        </Alert>
      ) : null}
    </div>
  );
}
