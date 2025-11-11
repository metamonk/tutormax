'use client';

import { useEffect, useState } from 'react';

interface SessionCompletionIndicatorProps {
  totalSessions: number;
  completionRate?: number; // Optional: if not provided, defaults to 95.2%
}

export function SessionCompletionIndicator({ totalSessions, completionRate = 95.2 }: SessionCompletionIndicatorProps) {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => {
      setProgress(completionRate);
    }, 100);
    return () => clearTimeout(timer);
  }, [completionRate]);

  const circumference = 2 * Math.PI * 70;
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  const completedSessions = Math.round((totalSessions * completionRate) / 100);
  const incompleteSessions = totalSessions - completedSessions;

  return (
    <div className="flex flex-col items-center justify-center py-8">
      <div className="relative h-[200px] w-[200px]">
        <svg className="h-full w-full -rotate-90 transform">
          {/* Background circle */}
          <circle cx="100" cy="100" r="70" stroke="hsl(var(--muted))" strokeWidth="12" fill="none" />
          {/* Progress circle */}
          <circle
            cx="100"
            cy="100"
            r="70"
            stroke="hsl(var(--chart-2))"
            strokeWidth="12"
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-out"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div className="text-4xl font-bold tabular-nums">{progress.toFixed(1)}%</div>
          <div className="text-sm text-muted-foreground">Completion</div>
        </div>
      </div>
      <div className="mt-6 space-y-2 text-center">
        <div className="flex items-center justify-center gap-4 text-sm">
          <div>
            <span className="font-semibold tabular-nums">{completedSessions.toLocaleString()}</span>
            <span className="text-muted-foreground"> completed</span>
          </div>
          <div className="h-4 w-px bg-border" />
          <div>
            <span className="font-semibold tabular-nums">{incompleteSessions.toLocaleString()}</span>
            <span className="text-muted-foreground"> incomplete</span>
          </div>
        </div>
      </div>
    </div>
  );
}
