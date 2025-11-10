'use client';

import { WifiOff } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function OfflinePage() {
  const handleRetry = () => {
    if (typeof window !== 'undefined') {
      window.location.reload();
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 w-16 h-16 rounded-full bg-orange-100 dark:bg-orange-900/20 flex items-center justify-center">
            <WifiOff className="w-8 h-8 text-orange-600 dark:text-orange-400" />
          </div>
          <CardTitle className="text-2xl">You're Offline</CardTitle>
          <CardDescription className="text-base">
            It looks like you've lost your internet connection.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="text-sm text-muted-foreground text-center">
            <p className="mb-2">Some features may be limited while you're offline.</p>
            <p>Previously viewed pages may still be available.</p>
          </div>

          <Button
            onClick={handleRetry}
            className="w-full"
            size="lg"
          >
            Try Again
          </Button>

          <div className="pt-4 border-t">
            <h3 className="font-semibold mb-2 text-sm">Offline Features:</h3>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>• View cached pages</li>
              <li>• Access recently viewed data</li>
              <li>• Actions will sync when back online</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
