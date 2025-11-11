'use client';

/**
 * Performance Analytics Component
 * Displays performance analytics and charts using Recharts
 */

import React from 'react';
import type { PerformanceAnalytics as PerformanceAnalyticsType, TutorMetrics } from '@/lib/types';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { PerformanceTierChart } from '@/components/charts/PerformanceTierChart';
import { TopPerformersChart } from '@/components/charts/TopPerformersChart';
import { EngagementTrendChart } from '@/components/charts/EngagementTrendChart';
import { SessionCompletionIndicator } from '@/components/charts/SessionCompletionIndicator';
import { BottomPerformersChart } from '@/components/charts/BottomPerformersChart';

interface PerformanceAnalyticsProps {
  analytics: PerformanceAnalyticsType | null;
  tutorMetrics: TutorMetrics[];
}

export function PerformanceAnalytics({ analytics, tutorMetrics }: PerformanceAnalyticsProps) {

  if (!analytics) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Performance Analytics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <p className="text-muted-foreground">Loading analytics data...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Key Metrics Summary */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {/* Total Tutors */}
        <Card className="relative overflow-hidden border-border bg-card shadow-sm transition-shadow hover:shadow-md">
          <div className="p-6">
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <p className="text-sm font-medium text-muted-foreground">Total Tutors</p>
                <p className="text-3xl font-bold tracking-tight">{analytics.total_tutors}</p>
              </div>
              <div className="rounded-lg bg-primary/10 p-2">
                <svg className="h-5 w-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
            </div>
            <div className="mt-4 flex items-center gap-1">
              <span className="text-sm font-medium text-accent">{analytics.active_tutors} active</span>
              <span className="text-sm text-muted-foreground">currently online</span>
            </div>
          </div>
        </Card>

        {/* Average Rating */}
        <Card className="relative overflow-hidden border-border bg-card shadow-sm transition-shadow hover:shadow-md">
          <div className="p-6">
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <p className="text-sm font-medium text-muted-foreground">Avg Rating</p>
                <p className="text-3xl font-bold tracking-tight">{analytics.avg_rating.toFixed(2)}</p>
              </div>
              <div className="rounded-lg bg-primary/10 p-2">
                <svg className="h-5 w-5 text-primary" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
              </div>
            </div>
            <div className="mt-4 flex items-center gap-2">
              <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-yellow-400 to-green-500 transition-all"
                  style={{ width: `${(analytics.avg_rating / 5) * 100}%` }}
                />
              </div>
              <span className="text-sm text-muted-foreground">/ 5.0</span>
            </div>
          </div>
        </Card>

        {/* Engagement Score */}
        <Card className="relative overflow-hidden border-border bg-card shadow-sm transition-shadow hover:shadow-md">
          <div className="p-6">
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <p className="text-sm font-medium text-muted-foreground">Engagement</p>
                <p className="text-3xl font-bold tracking-tight">{analytics.avg_engagement_score.toFixed(1)}%</p>
              </div>
              <div className="rounded-lg bg-primary/10 p-2">
                <svg className="h-5 w-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
            </div>
            <div className="mt-4 flex items-center gap-1">
              <svg className="h-3 w-3 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
              </svg>
              <span className="text-sm font-medium text-accent">+5.2%</span>
              <span className="text-sm text-muted-foreground">vs last month</span>
            </div>
          </div>
        </Card>

        {/* Sessions */}
        <Card className="relative overflow-hidden border-border bg-card shadow-sm transition-shadow hover:shadow-md">
          <div className="p-6">
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <p className="text-sm font-medium text-muted-foreground">Sessions</p>
                <p className="text-3xl font-bold tracking-tight">{analytics.total_sessions_7day.toLocaleString()}</p>
              </div>
              <div className="rounded-lg bg-primary/10 p-2">
                <svg className="h-5 w-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
            </div>
            <div className="mt-4 flex items-center gap-1">
              <svg className="h-3 w-3 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
              </svg>
              <span className="text-sm font-medium text-accent">+18.7%</span>
              <span className="text-sm text-muted-foreground">({analytics.total_sessions_30day.toLocaleString()} last 30d)</span>
            </div>
          </div>
        </Card>

        {/* Active Alerts */}
        <Card className="relative overflow-hidden border-border bg-card shadow-sm transition-shadow hover:shadow-md">
          <div className="p-6">
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <p className="text-sm font-medium text-muted-foreground">Alerts</p>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-bold tracking-tight text-red-600">{analytics.alerts_count.critical}</span>
                  <span className="text-xl text-muted-foreground">/</span>
                  <span className="text-3xl font-bold tracking-tight text-yellow-600">{analytics.alerts_count.warning}</span>
                </div>
              </div>
              <div className="rounded-lg bg-red-500/10 p-2">
                <svg className="h-5 w-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
            </div>
            <div className="mt-4 flex items-center gap-1">
              <svg className="h-3 w-3 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
              <span className="text-sm font-medium text-accent">-8 alerts</span>
              <span className="text-sm text-muted-foreground">resolved</span>
            </div>
          </div>
        </Card>
      </div>

      {/* Charts Section */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Performance Tier Distribution */}
        <Card className="border-border bg-card shadow-sm">
          <CardHeader>
            <CardTitle>Performance Tier Distribution</CardTitle>
            <CardDescription>Distribution of tutors across performance tiers</CardDescription>
          </CardHeader>
          <CardContent>
            <PerformanceTierChart distribution={analytics.performance_distribution} />
          </CardContent>
        </Card>

        {/* Top Performers */}
        <Card className="border-border bg-card shadow-sm">
          <CardHeader>
            <CardTitle>Top 5 Performers (30 Days)</CardTitle>
            <CardDescription>Highest rated tutors in the last month</CardDescription>
          </CardHeader>
          <CardContent>
            <TopPerformersChart tutorMetrics={tutorMetrics} />
          </CardContent>
        </Card>
      </div>

      {/* Performance Trends */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Engagement Trend */}
        <Card className="border-border bg-card shadow-sm">
          <CardHeader>
            <CardTitle>Engagement Score Trend</CardTitle>
            <CardDescription>Average engagement score over the past week</CardDescription>
          </CardHeader>
          <CardContent>
            <EngagementTrendChart avgEngagementScore={analytics.avg_engagement_score} />
          </CardContent>
        </Card>

        {/* Session Completion Rate */}
        <Card className="border-border bg-card shadow-sm">
          <CardHeader>
            <CardTitle>Session Completion Rate</CardTitle>
            <CardDescription>Percentage of sessions successfully completed</CardDescription>
          </CardHeader>
          <CardContent>
            <SessionCompletionIndicator totalSessions={analytics.total_sessions_30day} />
          </CardContent>
        </Card>
      </div>

      {/* Bottom Performers - Full Width */}
      <Card className="border-border bg-card shadow-sm">
        <CardHeader>
          <CardTitle>Needs Support (30 Days)</CardTitle>
          <CardDescription>Tutors requiring additional support and coaching</CardDescription>
        </CardHeader>
        <CardContent>
          <BottomPerformersChart tutorMetrics={tutorMetrics} />
        </CardContent>
      </Card>
    </div>
  );
}
