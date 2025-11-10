'use client';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { TutorPerformanceData } from '@/lib/types';
import { Target, TrendingUp, Users, AlertCircle, CheckCircle2, Clock } from 'lucide-react';

interface TutorMetricsProps {
  data: TutorPerformanceData | null;
  loading?: boolean;
}

export function TutorMetrics({ data, loading }: TutorMetricsProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Performance Metrics</CardTitle>
          <CardDescription>Loading your performance data...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data || !data.metrics) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Performance Metrics</CardTitle>
          <CardDescription>{data?.message || 'No metrics available yet'}</CardDescription>
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

  // Determine tier badge color
  const getTierColor = (tier: string | null) => {
    if (!tier) return 'secondary';
    switch (tier) {
      case 'Exemplary':
        return 'default'; // Green
      case 'Strong':
        return 'secondary'; // Blue
      case 'Developing':
        return 'outline'; // Yellow/Amber
      case 'Needs Attention':
      case 'At Risk':
        return 'destructive'; // Red
      default:
        return 'secondary';
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Performance Metrics</CardTitle>
            <CardDescription>
              {data.window === '7day' && 'Last 7 days'}
              {data.window === '30day' && 'Last 30 days'}
              {data.window === '90day' && 'Last 90 days'}
            </CardDescription>
          </div>
          {metrics.performance_tier && (
            <Badge variant={getTierColor(metrics.performance_tier)} className="text-sm px-3 py-1">
              {metrics.performance_tier}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Sessions Completed */}
          <div className="flex items-start space-x-3 p-4 rounded-lg bg-muted/50">
            <Users className="h-5 w-5 text-blue-600 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-muted-foreground">Sessions</p>
              <p className="text-2xl font-bold">{metrics.sessions_completed}</p>
            </div>
          </div>

          {/* Average Rating */}
          {metrics.avg_rating !== null && (
            <div className="flex items-start space-x-3 p-4 rounded-lg bg-muted/50">
              <TrendingUp className="h-5 w-5 text-green-600 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-muted-foreground">Avg Rating</p>
                <p className="text-2xl font-bold">{metrics.avg_rating.toFixed(1)}/5.0</p>
              </div>
            </div>
          )}

          {/* Engagement Score */}
          {metrics.engagement_score !== null && (
            <div className="flex items-start space-x-3 p-4 rounded-lg bg-muted/50">
              <Target className="h-5 w-5 text-purple-600 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-muted-foreground">Engagement</p>
                <p className="text-2xl font-bold">{metrics.engagement_score.toFixed(1)}/5.0</p>
              </div>
            </div>
          )}

          {/* First Session Success */}
          {metrics.first_session_success_rate !== null && (
            <div className="flex items-start space-x-3 p-4 rounded-lg bg-muted/50">
              <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-muted-foreground">First Session Success</p>
                <p className="text-2xl font-bold">{(metrics.first_session_success_rate * 100).toFixed(0)}%</p>
              </div>
            </div>
          )}

          {/* Learning Objectives Met */}
          {metrics.learning_objectives_met_pct !== null && (
            <div className="flex items-start space-x-3 p-4 rounded-lg bg-muted/50">
              <Target className="h-5 w-5 text-indigo-600 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-muted-foreground">Goals Met</p>
                <p className="text-2xl font-bold">{(metrics.learning_objectives_met_pct * 100).toFixed(0)}%</p>
              </div>
            </div>
          )}

          {/* No Shows */}
          <div className="flex items-start space-x-3 p-4 rounded-lg bg-muted/50">
            <AlertCircle className={`h-5 w-5 mt-0.5 ${metrics.no_show_count > 3 ? 'text-red-600' : 'text-orange-600'}`} />
            <div>
              <p className="text-sm font-medium text-muted-foreground">No Shows</p>
              <p className="text-2xl font-bold">{metrics.no_show_count}</p>
            </div>
          </div>

          {/* Response Time */}
          {metrics.response_time_avg_minutes !== null && (
            <div className="flex items-start space-x-3 p-4 rounded-lg bg-muted/50">
              <Clock className="h-5 w-5 text-blue-600 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-muted-foreground">Avg Response Time</p>
                <p className="text-2xl font-bold">{metrics.response_time_avg_minutes.toFixed(0)}m</p>
              </div>
            </div>
          )}

          {/* Reschedule Rate */}
          {metrics.reschedule_rate !== null && (
            <div className="flex items-start space-x-3 p-4 rounded-lg bg-muted/50">
              <AlertCircle className={`h-5 w-5 mt-0.5 ${metrics.reschedule_rate > 0.15 ? 'text-red-600' : 'text-green-600'}`} />
              <div>
                <p className="text-sm font-medium text-muted-foreground">Reschedule Rate</p>
                <p className="text-2xl font-bold">{(metrics.reschedule_rate * 100).toFixed(0)}%</p>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
