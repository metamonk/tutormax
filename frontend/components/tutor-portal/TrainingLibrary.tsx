'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { BookOpen } from 'lucide-react';

interface TrainingLibraryProps {
  tutorId: string;
}

export function TrainingLibrary({ tutorId }: TrainingLibraryProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BookOpen className="h-5 w-5" />
          Training Library
        </CardTitle>
        <CardDescription>
          Access recommended training materials and resources
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="text-center py-12 text-muted-foreground">
          <BookOpen className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>Training library coming soon...</p>
        </div>
      </CardContent>
    </Card>
  );
}
