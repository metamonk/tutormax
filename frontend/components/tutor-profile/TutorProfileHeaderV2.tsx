'use client';

import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Mail,
  MapPin,
  GraduationCap,
  Calendar,
  Clock,
  AlertTriangle,
  TrendingUp,
  Star,
  Target,
  CheckCircle2,
  XCircle,
  Timer,
  RefreshCw,
  Trophy,
  User,
} from 'lucide-react';
import type { TutorBasicInfo, ChurnPredictionWindow, TutorProfilePerformanceMetrics } from '@/lib/types';

interface TutorProfileHeaderV2Props {
  tutorInfo: TutorBasicInfo;
  churnPredictions: ChurnPredictionWindow[];
  performanceMetrics?: TutorProfilePerformanceMetrics;
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

export function TutorProfileHeaderV2({ tutorInfo, churnPredictions, performanceMetrics }: TutorProfileHeaderV2Props) {
  const getChurnRiskLevel = (score: number) => {
    if (score >= 70) return { label: 'Critical', variant: 'destructive' as const };
    if (score >= 50) return { label: 'High', variant: 'destructive' as const };
    if (score >= 30) return { label: 'Medium', variant: 'secondary' as const };
    return { label: 'Low', variant: 'outline' as const };
  };

  const getChurnRiskColor = (score: number) => {
    if (score >= 50) return 'hsl(var(--destructive))';
    if (score >= 30) return 'hsl(var(--warning))';
    return 'hsl(var(--success))';
  };

  const getTierColor = (tier: string) => {
    switch (tier.toLowerCase()) {
      case 'exemplary':
        return 'bg-success/10 text-success border-success/20';
      case 'strong':
        return 'bg-primary/10 text-primary border-primary/20';
      case 'developing':
        return 'bg-warning/10 text-warning border-warning/20';
      case 'needs attention':
      case 'at risk':
        return 'bg-destructive/10 text-destructive border-destructive/20';
      default:
        return 'bg-muted text-muted-foreground';
    }
  };

  const getPerformanceColor = (value: number, threshold: number) => {
    if (value >= threshold) return 'text-success';
    if (value >= threshold * 0.7) return 'text-warning';
    return 'text-destructive';
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const getInitials = (name: string) => {
    if (!name || typeof name !== 'string') return 'TU';
    return name
      .split(' ')
      .filter((n) => n.length > 0)
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2) || 'TU';
  };

  return (
    <div className="space-y-6">
      <Card className="w-full shadow-sm">
        <CardHeader className="border-b bg-muted/30 pb-6">
          <div className="flex flex-col gap-6 sm:flex-row sm:items-start sm:gap-6">
            {/* Avatar with gradient */}
            <div className="relative">
              <div className="flex h-20 w-20 items-center justify-center rounded-xl bg-gradient-to-br from-primary via-accent to-primary text-2xl font-bold text-primary-foreground shadow-md">
                {getInitials(tutorInfo.name)}
              </div>
            </div>

            {/* Profile Info */}
            <div className="flex-1 space-y-3">
              <div className="flex flex-wrap items-center gap-3">
                <h2 className="text-balance text-2xl font-bold tracking-tight">{tutorInfo.name}</h2>
                <Badge variant={tutorInfo.status === 'active' ? 'default' : 'secondary'} className="capitalize">
                  {tutorInfo.status}
                </Badge>
              </div>

              <div className="grid gap-2 text-sm text-muted-foreground sm:grid-cols-2">
                <div className="flex items-center gap-2">
                  <Mail className="h-4 w-4" />
                  <span className="truncate">{tutorInfo.email}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  <span>Onboarded: {formatDate(tutorInfo.onboarding_date)}</span>
                </div>
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4" />
                  <span>Tenure: {tutorInfo.tenure_days} days</span>
                </div>
                {tutorInfo.location && (
                  <div className="flex items-center gap-2">
                    <MapPin className="h-4 w-4" />
                    <span>{tutorInfo.location}</span>
                  </div>
                )}
                {tutorInfo.education_level && (
                  <div className="flex items-center gap-2">
                    <GraduationCap className="h-4 w-4" />
                    <span>{tutorInfo.education_level}</span>
                  </div>
                )}
              </div>

              {/* Subjects */}
              {tutorInfo.subjects.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {tutorInfo.subjects.map((subject, idx) => (
                    <Badge key={idx} variant="outline" className="text-xs">
                      {subject}
                    </Badge>
                  ))}
                </div>
              )}

              <p className="text-xs text-muted-foreground">ID: {tutorInfo.tutor_id}</p>
            </div>
          </div>
        </CardHeader>

        <CardContent className="p-6">
          <div className="space-y-6">
            {/* Churn Risk Panel */}
            <div>
              <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold">
                <AlertTriangle className="h-5 w-5" />
                Churn Risk Assessment
              </h3>
              <div className="grid gap-4 sm:grid-cols-3">
                {churnPredictions.map((pred) => {
                  const score = pred.churn_score;
                  const riskLevel = getChurnRiskLevel(score);
                  const riskColor = getChurnRiskColor(score);
                  return (
                    <Card key={pred.window} className="border-2 bg-muted/30">
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                          <div className="space-y-1">
                            <p className="text-sm font-medium text-muted-foreground">{pred.window.toUpperCase()}</p>
                            <div className="flex items-center gap-2">
                              <span className="text-2xl font-bold" style={{ color: riskColor }}>
                                {score.toFixed(0)}%
                              </span>
                              {score >= 50 && <AlertTriangle className="h-5 w-5" style={{ color: riskColor }} />}
                            </div>
                          </div>
                          <Badge variant={riskLevel.variant} className="shrink-0 border">
                            {riskLevel.label}
                          </Badge>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </div>

            {/* Performance Metrics Grid */}
            {performanceMetrics && (
              <div>
                <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold">
                  <TrendingUp className="h-5 w-5" />
                  Performance Metrics
                </h3>

                {/* Performance Tier */}
                {performanceMetrics.performance_tier && (
                  <div className="mb-4">
                    <Card className={`border-2 ${getTierColor(performanceMetrics.performance_tier)}`}>
                      <CardContent className="flex items-center gap-3 p-4">
                        <Trophy className="h-6 w-6" />
                        <div>
                          <p className="text-sm font-medium">Performance Tier</p>
                          <p className="text-xl font-bold capitalize">{performanceMetrics.performance_tier}</p>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                )}

                {/* Metrics Grid */}
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  <Card className="bg-muted/30">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="space-y-1">
                          <p className="text-sm text-muted-foreground">Sessions Completed</p>
                          <p className="text-2xl font-bold">{performanceMetrics.sessions_completed}</p>
                        </div>
                        <CheckCircle2 className="h-5 w-5 text-success" />
                      </div>
                    </CardContent>
                  </Card>

                  {performanceMetrics.avg_rating !== null && (
                    <Card className="bg-muted/30">
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between">
                          <div className="space-y-1">
                            <p className="text-sm text-muted-foreground">Average Rating</p>
                            <div className="flex items-baseline gap-1">
                              <p
                                className={`text-2xl font-bold ${getPerformanceColor(performanceMetrics.avg_rating, 4.5)}`}
                              >
                                {performanceMetrics.avg_rating.toFixed(1)}
                              </p>
                              <span className="text-sm text-muted-foreground">/ 5.0</span>
                            </div>
                          </div>
                          <Star className="h-5 w-5 text-warning" />
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {performanceMetrics.engagement_score !== null && (() => {
                    const engagementScore = normalizeEngagement(performanceMetrics.engagement_score);
                    return engagementScore !== null ? (
                      <Card className="bg-muted/30">
                        <CardContent className="p-4">
                          <div className="flex items-start justify-between">
                            <div className="space-y-1">
                              <p className="text-sm text-muted-foreground">Engagement Score</p>
                              <div className="flex items-baseline gap-1">
                                <p
                                  className={`text-2xl font-bold ${getPerformanceColor(engagementScore * 100, 80)}`}
                                >
                                  {(engagementScore * 100).toFixed(0)}
                                </p>
                                <span className="text-sm text-muted-foreground">/ 100</span>
                              </div>
                            </div>
                            <Target className="h-5 w-5 text-primary" />
                          </div>
                        </CardContent>
                      </Card>
                    ) : null;
                  })()}

                  {performanceMetrics.first_session_success_rate !== null && (() => {
                    const firstSessionSuccess = normalizePercentage(performanceMetrics.first_session_success_rate);
                    return firstSessionSuccess !== null ? (
                      <Card className="bg-muted/30">
                        <CardContent className="p-4">
                          <div className="flex items-start justify-between">
                            <div className="space-y-1">
                              <p className="text-sm text-muted-foreground">First Session Success</p>
                              <div className="flex items-baseline gap-1">
                                <p
                                  className={`text-2xl font-bold ${getPerformanceColor(firstSessionSuccess, 85)}`}
                                >
                                  {firstSessionSuccess.toFixed(0)}%
                                </p>
                              </div>
                            </div>
                            <CheckCircle2 className="h-5 w-5 text-success" />
                          </div>
                        </CardContent>
                      </Card>
                    ) : null;
                  })()}

                  {performanceMetrics.learning_objectives_met_pct !== null && (() => {
                    const learningObjectives = normalizePercentage(performanceMetrics.learning_objectives_met_pct);
                    return learningObjectives !== null ? (
                      <Card className="bg-muted/30">
                        <CardContent className="p-4">
                          <div className="flex items-start justify-between">
                            <div className="space-y-1">
                              <p className="text-sm text-muted-foreground">Learning Objectives Met</p>
                              <div className="flex items-baseline gap-1">
                                <p
                                  className={`text-2xl font-bold ${getPerformanceColor(learningObjectives, 90)}`}
                                >
                                  {learningObjectives.toFixed(0)}%
                                </p>
                              </div>
                            </div>
                            <Target className="h-5 w-5 text-accent" />
                          </div>
                        </CardContent>
                      </Card>
                    ) : null;
                  })()}

                  <Card className="bg-muted/30">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="space-y-1">
                          <p className="text-sm text-muted-foreground">No Shows</p>
                          <p
                            className={`text-2xl font-bold ${
                              performanceMetrics.no_show_count <= 2
                                ? 'text-success'
                                : performanceMetrics.no_show_count <= 5
                                  ? 'text-warning'
                                  : 'text-destructive'
                            }`}
                          >
                            {performanceMetrics.no_show_count}
                          </p>
                        </div>
                        <XCircle className="h-5 w-5 text-destructive" />
                      </div>
                    </CardContent>
                  </Card>

                  {performanceMetrics.reschedule_rate !== null && (() => {
                    const rescheduleRate = normalizePercentage(performanceMetrics.reschedule_rate);
                    return rescheduleRate !== null ? (
                      <Card className="bg-muted/30">
                        <CardContent className="p-4">
                          <div className="flex items-start justify-between">
                            <div className="space-y-1">
                              <p className="text-sm text-muted-foreground">Reschedule Rate</p>
                              <div className="flex items-baseline gap-1">
                                <p
                                  className={`text-2xl font-bold ${
                                    rescheduleRate <= 10
                                      ? 'text-success'
                                      : rescheduleRate <= 20
                                        ? 'text-warning'
                                        : 'text-destructive'
                                  }`}
                                >
                                  {rescheduleRate.toFixed(1)}%
                                </p>
                              </div>
                            </div>
                            <RefreshCw className="h-5 w-5 text-muted-foreground" />
                          </div>
                        </CardContent>
                      </Card>
                    ) : null;
                  })()}
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
