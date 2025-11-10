'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { TutorProfileHeader, TutorActiveFlags, TutorManagerNotes } from '@/components/tutor-profile';
import { SessionRatings } from '@/components/tutor-portal';
import type { TutorProfileResponse, TutorProfilePerformanceMetrics, RecentFeedback, InterventionHistoryItem } from '@/lib/types';
import type { RatingData } from '@/components/tutor-portal/SessionRatings';
import { ArrowLeft, RefreshCw, Star, MessageSquare, Target, Calendar } from 'lucide-react';

export default function TutorProfilePage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [profileData, setProfileData] = useState<TutorProfileResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const tutorId = params.id as string;

  const loadData = async () => {
    if (!tutorId) {
      setError('Tutor ID is required');
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await apiClient.getTutorProfileDetail(tutorId);
      setProfileData(data);
    } catch (err: any) {
      console.error('Failed to load tutor profile:', err);
      setError(err.response?.data?.detail || 'Failed to load tutor profile. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [tutorId]);

  // Check if user has permission to view tutor profiles
  const canViewProfile = user?.roles?.some(
    (role) => ['admin', 'operations_manager', 'people_ops'].includes(role)
  );

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 text-center">
            <h2 className="text-2xl font-bold mb-4">Authentication Required</h2>
            <p className="text-muted-foreground mb-6">
              Please log in to access tutor profiles.
            </p>
            <Button onClick={() => router.push('/login')}>Go to Login</Button>
          </div>
        </div>
      </div>
    );
  }

  if (!canViewProfile) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 text-center">
            <h2 className="text-2xl font-bold mb-4">Access Denied</h2>
            <p className="text-muted-foreground mb-6">
              You don't have permission to view tutor profiles.
            </p>
            <Button onClick={() => router.push('/')}>Go Home</Button>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 text-center">
            <h2 className="text-2xl font-bold mb-4 text-red-600">Error Loading Profile</h2>
            <p className="text-muted-foreground mb-6">{error}</p>
            <div className="flex gap-3 justify-center">
              <Button onClick={() => router.back()} variant="outline">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Go Back
              </Button>
              <Button onClick={loadData}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Try Again
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (loading || !profileData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <Button
            variant="ghost"
            onClick={() => router.back()}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          <Button onClick={loadData} variant="outline" disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {/* Profile Header */}
        <TutorProfileHeader
          tutorInfo={profileData.tutor_info}
          churnPredictions={profileData.churn_predictions}
        />

        {/* Content Tabs */}
        <Tabs defaultValue="performance" className="mt-6">
          <TabsList className="grid w-full grid-cols-5 lg:w-auto">
            <TabsTrigger value="performance">Performance</TabsTrigger>
            <TabsTrigger value="flags">Flags</TabsTrigger>
            <TabsTrigger value="feedback">Feedback</TabsTrigger>
            <TabsTrigger value="ratings">Ratings</TabsTrigger>
            <TabsTrigger value="notes">Notes</TabsTrigger>
          </TabsList>

          <TabsContent value="performance" className="space-y-6 mt-6">
            <PerformanceMetricsCard metrics={profileData.performance_metrics} />
            <InterventionHistoryCard interventions={profileData.intervention_history} />
          </TabsContent>

          <TabsContent value="flags" className="space-y-6 mt-6">
            <TutorActiveFlags flags={profileData.active_flags} />
          </TabsContent>

          <TabsContent value="feedback" className="space-y-6 mt-6">
            <RecentFeedbackCard feedback={profileData.recent_feedback} />
          </TabsContent>

          <TabsContent value="ratings" className="space-y-6 mt-6">
            <SessionRatings
              ratings={profileData.recent_feedback
                .filter((f) => f.rating !== null)
                .map((f): RatingData => ({
                  session_id: f.session_id,
                  student_id: f.student_id,
                  session_date: f.session_date,
                  rating: f.rating!,
                  feedback_text: f.feedback_text || undefined,
                  subject: f.subject,
                }))}
              loading={false}
            />
          </TabsContent>

          <TabsContent value="notes" className="space-y-6 mt-6">
            <TutorManagerNotes notes={profileData.manager_notes} />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

// Performance Metrics Card
function PerformanceMetricsCard({ metrics }: { metrics: TutorProfilePerformanceMetrics }) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Performance Metrics</CardTitle>
          <Badge variant="outline">{metrics.window}</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricItem label="Tier" value={metrics.performance_tier} />
          <MetricItem label="Sessions" value={metrics.sessions_completed.toString()} />
          <MetricItem label="Avg Rating" value={metrics.avg_rating?.toFixed(1) || 'N/A'} suffix="/5.0" />
          <MetricItem label="Engagement" value={metrics.engagement_score?.toFixed(1) || 'N/A'} suffix="/5.0" />
          <MetricItem label="First Session Success" value={metrics.first_session_success_rate ? `${(metrics.first_session_success_rate * 100).toFixed(0)}%` : 'N/A'} />
          <MetricItem label="Goals Met" value={metrics.learning_objectives_met_pct ? `${(metrics.learning_objectives_met_pct * 100).toFixed(0)}%` : 'N/A'} />
          <MetricItem label="No Shows" value={metrics.no_show_count.toString()} />
          <MetricItem label="Reschedule Rate" value={metrics.reschedule_rate ? `${(metrics.reschedule_rate * 100).toFixed(0)}%` : 'N/A'} />
        </div>
      </CardContent>
    </Card>
  );
}

function MetricItem({ label, value, suffix }: { label: string; value: string; suffix?: string }) {
  return (
    <div className="p-3 rounded-lg bg-muted/50">
      <p className="text-xs text-muted-foreground mb-1">{label}</p>
      <p className="text-lg font-bold">
        {value}
        {suffix && <span className="text-sm font-normal text-muted-foreground ml-1">{suffix}</span>}
      </p>
    </div>
  );
}

// Intervention History Card
function InterventionHistoryCard({ interventions }: { interventions: InterventionHistoryItem[] }) {
  if (interventions.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Intervention History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-center text-muted-foreground">
            <Target className="h-12 w-12 mb-4 opacity-50" />
            <p>No interventions recorded</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Intervention History</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {interventions.map((intervention) => (
            <div key={intervention.intervention_id} className="p-4 border rounded-lg">
              <div className="flex items-start justify-between mb-2">
                <div>
                  <Badge variant="outline" className="mb-2 capitalize">{intervention.intervention_type.replace('_', ' ')}</Badge>
                  <p className="text-sm text-muted-foreground">{intervention.trigger_reason}</p>
                </div>
                <Badge variant="secondary" className="capitalize">{intervention.status}</Badge>
              </div>
              {intervention.notes && (
                <p className="text-sm mt-2 italic">{intervention.notes}</p>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// Recent Feedback Card
function RecentFeedbackCard({ feedback }: { feedback: RecentFeedback[] }) {
  if (feedback.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Feedback</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-center text-muted-foreground">
            <MessageSquare className="h-12 w-12 mb-4 opacity-50" />
            <p>No recent feedback available</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Feedback</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {feedback.map((fb) => (
            <div key={fb.session_id} className="p-4 border rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Badge variant="outline">{fb.subject}</Badge>
                  <span className="text-sm text-muted-foreground flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {new Date(fb.session_date).toLocaleDateString()}
                  </span>
                </div>
                {fb.rating && (
                  <div className="flex items-center gap-1">
                    <Star className="h-4 w-4 text-yellow-500 fill-current" />
                    <span className="font-bold">{fb.rating}/5</span>
                  </div>
                )}
              </div>
              {fb.feedback_text && (
                <p className="text-sm italic mt-2">&ldquo;{fb.feedback_text}&rdquo;</p>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
