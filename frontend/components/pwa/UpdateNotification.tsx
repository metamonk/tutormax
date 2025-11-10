'use client';

import { useEffect, useState } from 'react';
import { useServiceWorker } from '@/hooks/useServiceWorker';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { RefreshCw } from 'lucide-react';

export function UpdateNotification() {
  const { isUpdateAvailable, skipWaiting } = useServiceWorker();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Don't render anything until mounted to avoid hydration mismatch
  if (!mounted || !isUpdateAvailable) {
    return null;
  }

  const handleUpdate = () => {
    skipWaiting();
  };

  return (
    <div className="fixed top-4 left-4 right-4 md:left-auto md:right-4 md:max-w-md z-50 animate-in slide-in-from-top-5">
      <Alert className="shadow-lg border-2 border-blue-500 bg-blue-50 dark:bg-blue-950">
        <RefreshCw className="h-4 w-4" />
        <AlertTitle>Update Available</AlertTitle>
        <AlertDescription className="flex items-center justify-between gap-4">
          <span>A new version of TutorMax is available.</span>
          <Button size="sm" onClick={handleUpdate}>
            Update Now
          </Button>
        </AlertDescription>
      </Alert>
    </div>
  );
}
