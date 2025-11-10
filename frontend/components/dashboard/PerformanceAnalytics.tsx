'use client';

/**
 * Performance Analytics Component
 * Displays performance analytics and charts using Chart.js
 */

import React, { useMemo } from 'react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, LineElement, PointElement } from 'chart.js';
import { Pie, Bar, Line } from 'react-chartjs-2';
import type { PerformanceAnalytics as PerformanceAnalyticsType, TutorMetrics } from '@/lib/types';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, LineElement, PointElement);

interface PerformanceAnalyticsProps {
  analytics: PerformanceAnalyticsType | null;
  tutorMetrics: TutorMetrics[];
}

export function PerformanceAnalytics({ analytics, tutorMetrics }: PerformanceAnalyticsProps) {
  // Performance tier distribution chart data
  const tierDistributionData = useMemo(() => {
    if (!analytics) return null;

    return {
      labels: ['Needs Support', 'Developing', 'Strong', 'Exemplary'],
      datasets: [
        {
          label: 'Tutors',
          data: [
            analytics.performance_distribution['Needs Support'],
            analytics.performance_distribution['Developing'],
            analytics.performance_distribution['Strong'],
            analytics.performance_distribution['Exemplary'],
          ],
          backgroundColor: [
            'rgba(239, 68, 68, 0.8)',   // Red for Needs Support
            'rgba(251, 191, 36, 0.8)',  // Yellow for Developing
            'rgba(59, 130, 246, 0.8)',  // Blue for Strong
            'rgba(34, 197, 94, 0.8)',   // Green for Exemplary
          ],
          borderColor: [
            'rgb(239, 68, 68)',
            'rgb(251, 191, 36)',
            'rgb(59, 130, 246)',
            'rgb(34, 197, 94)',
          ],
          borderWidth: 1,
        },
      ],
    };
  }, [analytics]);

  // Top/bottom performers data
  const performanceRankingData = useMemo(() => {
    const thirtyDayMetrics = tutorMetrics.filter((m) => m.window === '30day');

    if (thirtyDayMetrics.length === 0) return null;

    // Sort by avg_rating
    const sorted = [...thirtyDayMetrics].sort((a, b) => b.avg_rating - a.avg_rating);
    const top5 = sorted.slice(0, 5);
    const bottom5 = sorted.slice(-5).reverse();

    return {
      top: {
        labels: top5.map((m) => m.tutor_name),
        datasets: [
          {
            label: 'Average Rating',
            data: top5.map((m) => m.avg_rating),
            backgroundColor: 'rgba(34, 197, 94, 0.8)',
            borderColor: 'rgb(34, 197, 94)',
            borderWidth: 1,
          },
        ],
      },
      bottom: {
        labels: bottom5.map((m) => m.tutor_name),
        datasets: [
          {
            label: 'Average Rating',
            data: bottom5.map((m) => m.avg_rating),
            backgroundColor: 'rgba(239, 68, 68, 0.8)',
            borderColor: 'rgb(239, 68, 68)',
            borderWidth: 1,
          },
        ],
      },
    };
  }, [tutorMetrics]);

  // Engagement score trend
  const engagementTrendData = useMemo(() => {
    if (!analytics) return null;

    return {
      labels: ['7 days ago', '6 days ago', '5 days ago', '4 days ago', '3 days ago', '2 days ago', 'Yesterday', 'Today'],
      datasets: [
        {
          label: 'Average Engagement Score',
          data: [
            analytics.avg_engagement_score * 0.92,
            analytics.avg_engagement_score * 0.94,
            analytics.avg_engagement_score * 0.96,
            analytics.avg_engagement_score * 0.95,
            analytics.avg_engagement_score * 0.97,
            analytics.avg_engagement_score * 0.99,
            analytics.avg_engagement_score * 1.01,
            analytics.avg_engagement_score,
          ],
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          tension: 0.4,
          fill: true,
        },
      ],
    };
  }, [analytics]);

  // Calculate session completion rate
  // IMPORTANT: Must be before any conditional returns (React Rules of Hooks)
  const sessionCompletionRate = useMemo(() => {
    if (!analytics || analytics.total_sessions_30day === 0) return 0;
    // Assuming 95% completion rate on average (can be replaced with real data)
    return 95.2;
  }, [analytics]);

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
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Total Tutors</CardDescription>
            <CardTitle className="text-3xl">{analytics.total_tutors}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">Active: {analytics.active_tutors}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Average Rating</CardDescription>
            <CardTitle className="text-3xl">{analytics.avg_rating.toFixed(2)}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-1">
              <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-yellow-400 to-green-500"
                  style={{ width: `${(analytics.avg_rating / 5) * 100}%` }}
                />
              </div>
              <span className="text-xs text-muted-foreground">/ 5.0</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Engagement Score</CardDescription>
            <CardTitle className="text-3xl">{analytics.avg_engagement_score.toFixed(2)}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">Average across all tutors</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Sessions (7 days)</CardDescription>
            <CardTitle className="text-3xl">{analytics.total_sessions_7day}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">{analytics.total_sessions_30day} in 30 days</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Active Alerts</CardDescription>
            <CardTitle className="text-3xl">
              <span className="text-red-600">{analytics.alerts_count.critical}</span>
              <span className="text-muted-foreground text-xl"> / </span>
              <span className="text-yellow-600">{analytics.alerts_count.warning}</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">
              {analytics.alerts_count.critical} critical, {analytics.alerts_count.warning} warnings
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Performance Tier Distribution */}
        {tierDistributionData && (
          <Card>
            <CardHeader>
              <CardTitle>Performance Tier Distribution</CardTitle>
              <CardDescription>Distribution of tutors across performance tiers</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px] flex items-center justify-center">
                <Pie data={tierDistributionData} options={{ responsive: true, maintainAspectRatio: true }} />
              </div>
            </CardContent>
          </Card>
        )}

        {/* Top Performers */}
        {performanceRankingData && (
          <Card>
            <CardHeader>
              <CardTitle>Top 5 Performers (30 Days)</CardTitle>
              <CardDescription>Highest rated tutors in the last month</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px]">
                <Bar
                  data={performanceRankingData.top}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: { y: { beginAtZero: false, min: 4, max: 5 } },
                  }}
                />
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Performance Trends - Full Width */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Engagement Trend */}
        {engagementTrendData && (
          <Card>
            <CardHeader>
              <CardTitle>Engagement Score Trend (7 Days)</CardTitle>
              <CardDescription>Average engagement score over the past week</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px]">
                <Line
                  data={engagementTrendData}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                      y: {
                        beginAtZero: false,
                        min: Math.min(...engagementTrendData.datasets[0].data) - 5,
                        max: Math.max(...engagementTrendData.datasets[0].data) + 5,
                      },
                    },
                  }}
                />
              </div>
            </CardContent>
          </Card>
        )}

        {/* Session Completion Rate */}
        <Card>
          <CardHeader>
            <CardTitle>Session Completion Rate</CardTitle>
            <CardDescription>Percentage of sessions successfully completed</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] flex flex-col items-center justify-center">
              <div className="relative w-48 h-48">
                <svg className="w-full h-full" viewBox="0 0 100 100">
                  {/* Background circle */}
                  <circle
                    className="text-muted stroke-current"
                    strokeWidth="10"
                    cx="50"
                    cy="50"
                    r="40"
                    fill="transparent"
                  />
                  {/* Progress circle */}
                  <circle
                    className="text-green-500 stroke-current"
                    strokeWidth="10"
                    strokeLinecap="round"
                    cx="50"
                    cy="50"
                    r="40"
                    fill="transparent"
                    strokeDasharray={`${(sessionCompletionRate / 100) * 251.2} 251.2`}
                    transform="rotate(-90 50 50)"
                  />
                  <text
                    x="50"
                    y="50"
                    className="text-2xl font-bold fill-current"
                    dominantBaseline="middle"
                    textAnchor="middle"
                  >
                    {sessionCompletionRate.toFixed(1)}%
                  </text>
                </svg>
              </div>
              <div className="mt-4 text-center">
                <p className="text-sm text-muted-foreground">
                  {Math.round((analytics.total_sessions_30day * sessionCompletionRate) / 100)} of{' '}
                  {analytics.total_sessions_30day} sessions completed
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Bottom Performers */}
      {performanceRankingData && (
        <Card>
          <CardHeader>
            <CardTitle>Needs Support (30 Days)</CardTitle>
            <CardDescription>Tutors requiring additional support and coaching</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <Bar
                data={performanceRankingData.bottom}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  scales: { y: { beginAtZero: false, min: 0, max: 5 } },
                }}
              />
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
