'use client';

import type React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Trophy, Calendar, Star, Target, CheckCircle2, TrendingUp, Clock, AlertCircle, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { TutorPerformanceData } from '@/lib/types';
import { MetricsGridSkeleton } from '@/components/ui/skeleton-patterns';

interface MetricCardProps {
  icon: React.ElementType;
  label: string;
  value: string | number;
  variant?: 'default' | 'success' | 'warning' | 'destructive';
  iconColor?: string;
}

function MetricCard({ icon: Icon, label, value, variant = 'default', iconColor }: MetricCardProps) {
  const bgClasses = {
    default: 'bg-muted/50',
    success: 'bg-success/10',
    warning: 'bg-warning/10',
    destructive: 'bg-destructive/10',
  };

  const textClasses = {
    default: 'text-foreground',
    success: 'text-success',
    warning: 'text-warning',
    destructive: 'text-destructive',
  };

  return (
    <Card className={cn('overflow-hidden', bgClasses[variant])}>
      <CardContent className="p-6">
        <div className="flex items-center gap-4">
          <div
            className={cn(
              'flex h-12 w-12 shrink-0 items-center justify-center rounded-lg',
              bgClasses[variant === 'default' ? 'default' : variant]
            )}
            style={iconColor ? { backgroundColor: iconColor } : undefined}
          >
            <Icon className={cn('h-6 w-6', textClasses[variant])} />
          </div>
          <div className="flex-1 space-y-1">
            <p className="text-sm font-medium text-muted-foreground">{label}</p>
            <p className={cn('text-3xl font-bold tracking-tight', textClasses[variant])}>{value}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function getTierBadgeVariant(tier: string | null) {
  if (!tier) return 'secondary';
  switch (tier) {
    case 'Exemplary':
      return 'default';
    case 'Strong':
      return 'secondary';
    case 'Developing':
      return 'secondary';
    case 'Needs Attention':
      return 'outline';
    case 'At Risk':
      return 'destructive';
    default:
      return 'secondary';
  }
}

function getTierColor(tier: string | null) {
  if (!tier) return 'hsl(var(--chart-1))';
  switch (tier) {
    case 'Exemplary':
      return 'hsl(var(--chart-2))';
    case 'Strong':
      return 'hsl(var(--chart-1))';
    case 'Developing':
      return 'hsl(var(--chart-3))';
    case 'Needs Attention':
      return 'hsl(var(--warning))';
    case 'At Risk':
      return 'hsl(var(--destructive))';
    default:
      return 'hsl(var(--chart-1))';
  }
}

interface TutorMetricsV2Props {
  data: TutorPerformanceData | null;
  loading?: boolean;
}

// Helper function to normalize percentage values (handles both 0-1 and 0-100 formats)
function normalizePercentage(value: number | null): number | null {
  if (value === null) return null;
  // If value is between 0-1, convert to percentage
  if (value >= 0 && value <= 1) {
    return value * 100;
  }
  // If value is already 0-100, return as-is (capped at 100)
  return Math.min(value, 100);
}

// Helper function to normalize engagement score (should be 0-1, display as 0-1)
function normalizeEngagement(value: number | null): number | null {
  if (value === null) return null;
  // If value is > 1, it's incorrectly stored as percentage, convert back
  if (value > 1) {
    return value / 100;
  }
  // Already in correct 0-1 format
  return value;
}

export function TutorMetricsV2({ data, loading }: TutorMetricsV2Props) {
  if (loading) {
    return (
      <div className="space-y-6">
        <MetricsGridSkeleton metrics={6} />
      </div>
    );
  }

  if (!data || !data.metrics) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Performance Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-center text-muted-foreground">
            <Target className="h-12 w-12 mb-4 opacity-50" />
            <p>Complete more sessions to see your performance metrics.</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const { metrics } = data;
  const performanceTier = metrics.performance_tier;

  // Normalize values to handle both decimal and percentage formats
  const engagementScore = normalizeEngagement(metrics.engagement_score);
  const firstSessionSuccess = normalizePercentage(metrics.first_session_success_rate);
  const learningObjectives = normalizePercentage(metrics.learning_objectives_met_pct);
  const rescheduleRate = normalizePercentage(metrics.reschedule_rate);

  return (
    <div className="space-y-6">
      {/* Performance Overview Card */}
      <Card className="overflow-hidden border-2">
        <CardHeader className="pb-4">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <CardTitle className="text-xl">Performance Overview</CardTitle>
            {performanceTier && (
              <Badge
                variant={getTierBadgeVariant(performanceTier)}
                className="w-fit text-sm font-semibold"
                style={{
                  backgroundColor: getTierColor(performanceTier),
                  color: 'white',
                }}
              >
                <Trophy className="mr-2 h-4 w-4" />
                {performanceTier}
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="space-y-2 rounded-lg bg-muted/30 p-4">
              <div className="flex items-center gap-2">
                <div className="h-3 w-3 rounded-full" style={{ backgroundColor: 'hsl(var(--chart-1))' }} />
                <p className="text-sm font-medium text-muted-foreground">Sessions</p>
              </div>
              <p className="text-2xl font-bold">{metrics.sessions_completed}</p>
            </div>

            {metrics.avg_rating !== null && (
              <div className="space-y-2 rounded-lg bg-muted/30 p-4">
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full" style={{ backgroundColor: 'hsl(var(--chart-2))' }} />
                  <p className="text-sm font-medium text-muted-foreground">Avg Rating</p>
                </div>
                <p className="text-2xl font-bold">{metrics.avg_rating.toFixed(1)}</p>
              </div>
            )}

            {engagementScore !== null && (
              <div className="space-y-2 rounded-lg bg-muted/30 p-4">
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full" style={{ backgroundColor: 'hsl(var(--chart-3))' }} />
                  <p className="text-sm font-medium text-muted-foreground">Engagement</p>
                </div>
                <p className="text-2xl font-bold">{engagementScore.toFixed(2)}</p>
              </div>
            )}

            {firstSessionSuccess !== null && (
              <div className="space-y-2 rounded-lg bg-muted/30 p-4">
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full" style={{ backgroundColor: 'hsl(var(--chart-4))' }} />
                  <p className="text-sm font-medium text-muted-foreground">First Session Success</p>
                </div>
                <p className="text-2xl font-bold">{firstSessionSuccess.toFixed(0)}%</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Metric Cards Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        <MetricCard
          icon={Calendar}
          label="Sessions Completed"
          value={metrics.sessions_completed}
          variant="default"
          iconColor="hsl(var(--chart-1))"
        />

        {metrics.avg_rating !== null && (
          <MetricCard icon={Star} label="Average Rating" value={metrics.avg_rating.toFixed(1)} variant="success" />
        )}

        {engagementScore !== null && (
          <MetricCard
            icon={TrendingUp}
            label="Engagement Score"
            value={engagementScore.toFixed(2)}
            variant="success"
          />
        )}

        {firstSessionSuccess !== null && (
          <MetricCard
            icon={CheckCircle2}
            label="First Session Success"
            value={`${firstSessionSuccess.toFixed(0)}%`}
            variant="success"
          />
        )}

        {learningObjectives !== null && (
          <MetricCard
            icon={Target}
            label="Learning Objectives Met"
            value={`${learningObjectives.toFixed(0)}%`}
            variant="success"
          />
        )}

        <MetricCard
          icon={AlertCircle}
          label="No Shows"
          value={metrics.no_show_count}
          variant={metrics.no_show_count > 5 ? 'destructive' : metrics.no_show_count > 3 ? 'warning' : 'default'}
        />

        {metrics.response_time_avg_minutes !== null && (
          <MetricCard
            icon={Clock}
            label="Avg Response Time"
            value={`${metrics.response_time_avg_minutes.toFixed(0)}m`}
            variant="default"
            iconColor="hsl(var(--chart-5))"
          />
        )}

        {rescheduleRate !== null && (
          <MetricCard
            icon={RefreshCw}
            label="Reschedule Rate"
            value={`${rescheduleRate.toFixed(1)}%`}
            variant={rescheduleRate > 20 ? 'destructive' : rescheduleRate > 15 ? 'warning' : 'default'}
          />
        )}
      </div>
    </div>
  );
}
