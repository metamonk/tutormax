'use client';

import { useEffect, useState } from 'react';
import { usePWA } from '@/hooks/usePWA';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Download, X } from 'lucide-react';

export function InstallPrompt() {
  const { isInstalled, isInstallable, promptInstall } = usePWA();
  const [dismissed, setDismissed] = useState(false);
  const [show, setShow] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;

    // Check if user has previously dismissed the prompt
    const wasDismissed = localStorage.getItem('pwa-install-dismissed');
    if (wasDismissed) {
      const dismissedTime = parseInt(wasDismissed, 10);
      const daysSinceDismissal = (Date.now() - dismissedTime) / (1000 * 60 * 60 * 24);

      // Show again after 7 days
      if (daysSinceDismissal < 7) {
        setDismissed(true);
        return;
      }
    }

    // Wait 30 seconds before showing the prompt to avoid being intrusive
    const timer = setTimeout(() => {
      if (isInstallable && !isInstalled && !dismissed) {
        setShow(true);
      }
    }, 30000);

    return () => clearTimeout(timer);
  }, [isInstallable, isInstalled, dismissed, mounted]);

  const handleInstall = async () => {
    const installed = await promptInstall();
    if (installed) {
      setShow(false);
    }
  };

  const handleDismiss = () => {
    setShow(false);
    setDismissed(true);
    localStorage.setItem('pwa-install-dismissed', Date.now().toString());
  };

  // Don't render anything until mounted to avoid hydration mismatch
  if (!mounted || !show || isInstalled || !isInstallable || dismissed) {
    return null;
  }

  return (
    <div className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:max-w-md z-50 animate-in slide-in-from-bottom-5">
      <Card className="shadow-lg border-2">
        <CardHeader className="relative pb-3">
          <Button
            variant="ghost"
            size="icon"
            className="absolute right-2 top-2 h-6 w-6"
            onClick={handleDismiss}
          >
            <X className="h-4 w-4" />
          </Button>
          <div className="flex items-center gap-3">
            <div className="rounded-full bg-blue-100 dark:bg-blue-900 p-2">
              <Download className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <CardTitle className="text-lg">Install TutorMax</CardTitle>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pb-3">
          <CardDescription>
            Install our app for a better experience with offline access, faster loading, and push notifications.
          </CardDescription>
        </CardContent>
        <CardFooter className="flex gap-2">
          <Button onClick={handleInstall} className="flex-1">
            Install App
          </Button>
          <Button variant="outline" onClick={handleDismiss}>
            Not Now
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
