'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Users } from 'lucide-react';

interface PeerComparisonProps {
  tutorId: string;
  timeWindow: '7day' | '30day' | '90day';
}

export function PeerComparison({ tutorId, timeWindow }: PeerComparisonProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Users className="h-5 w-5" />
          Peer Comparison
        </CardTitle>
        <CardDescription>
          Compare your performance with peers in the {timeWindow} window
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="text-center py-12 text-muted-foreground">
          <Users className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>Peer comparison analytics coming soon...</p>
        </div>
      </CardContent>
    </Card>
  );
}
