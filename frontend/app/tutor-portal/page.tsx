'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { TutorMetrics, TutorSessions, TutorRecommendations, SessionRatings } from '@/components/tutor-portal';
import { BadgeGallery } from '@/components/tutor-portal/BadgeGallery';
import { GoalTracker } from '@/components/tutor-portal/GoalTracker';
import { TrainingLibrary } from '@/components/tutor-portal/TrainingLibrary';
import { PeerComparison } from '@/components/tutor-portal/PeerComparison';
import type { TutorPerformanceData, TutorSessionsResponse, TutorRecommendationsResponse } from '@/lib/types';
import type { RatingData } from '@/components/tutor-portal/SessionRatings';
import { ArrowLeft, RefreshCw } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function TutorPortalPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [metricsData, setMetricsData] = useState<TutorPerformanceData | null>(null);
  const [sessionsData, setSessionsData] = useState<TutorSessionsResponse | null>(null);
  const [recommendationsData, setRecommendationsData] = useState<TutorRecommendationsResponse | null>(null);
  const [feedbackData, setFeedbackData] = useState<RatingData[]>([]);
  const [selectedWindow, setSelectedWindow] = useState<'7day' | '30day' | '90day'>('30day');
  const [error, setError] = useState<string | null>(null);

  // Get tutor ID from user context
  const tutorId = user?.tutor_id;

  const loadData = async () => {
    if (!tutorId) {
      setError('Tutor ID not found. Please ensure you are logged in as a tutor.');
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Load all data in parallel
      const [metrics, sessions, recommendations, feedback] = await Promise.all([
        apiClient.getTutorMetrics(tutorId, selectedWindow),
        apiClient.getTutorSessions(tutorId, 20, 0),
        apiClient.getTutorRecommendations(tutorId),
        apiClient.getTutorFeedback(tutorId, 20, 0).catch(() => ({ feedback: [], success: false, pagination: {} })),
      ]);

      setMetricsData(metrics);
      setSessionsData(sessions);
      setRecommendationsData(recommendations);

      // Transform feedback data to RatingData format
      if (feedback.success && feedback.feedback) {
        const ratingsData: RatingData[] = feedback.feedback
          .filter((f: any) => f.rating !== null)
          .map((f: any) => ({
            session_id: f.session_id,
            student_id: f.student_id,
            session_date: f.session_date,
            rating: f.rating,
            feedback_text: f.feedback_text,
            subject: f.subject || 'General',
          }));
        setFeedbackData(ratingsData);
      }
    } catch (err: any) {
      console.error('Failed to load tutor portal data:', err);
      setError(err.response?.data?.detail || 'Failed to load data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [tutorId, selectedWindow]);

  const handleLoadMoreSessions = async () => {
    if (!tutorId || !sessionsData) return;

    try {
      const moreSessions = await apiClient.getTutorSessions(
        tutorId,
        20,
        sessionsData.sessions.length
      );

      setSessionsData({
        ...moreSessions,
        sessions: [...sessionsData.sessions, ...moreSessions.sessions],
      });
    } catch (err) {
      console.error('Failed to load more sessions:', err);
    }
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 text-center">
            <h2 className="text-2xl font-bold mb-4">Authentication Required</h2>
            <p className="text-muted-foreground mb-6">
              Please log in to access your tutor portal.
            </p>
            <Button onClick={() => router.push('/login')}>Go to Login</Button>
          </div>
        </div>
      </div>
    );
  }

  if (!user.roles?.includes('tutor')) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 text-center">
            <h2 className="text-2xl font-bold mb-4">Access Denied</h2>
            <p className="text-muted-foreground mb-6">
              You must have the tutor role to access this portal.
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
        <div className="max-w-4xl mx-auto">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 text-center">
            <h2 className="text-2xl font-bold mb-4 text-red-600">Error Loading Data</h2>
            <p className="text-muted-foreground mb-6">{error}</p>
            <div className="flex gap-3 justify-center">
              <Button onClick={() => router.push('/')} variant="outline">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Go Home
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <Button
            variant="ghost"
            onClick={() => router.push('/')}
            className="mb-4"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Home
          </Button>

          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                Tutor Portal
              </h1>
              <p className="text-muted-foreground mt-1">
                Welcome back, {user.full_name || user.email}!
              </p>
            </div>
            <Button onClick={loadData} variant="outline" disabled={loading}>
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </div>

        {/* Time Window Selector */}
        <div className="mb-6 flex gap-2">
          <Button
            variant={selectedWindow === '7day' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedWindow('7day')}
          >
            Last 7 Days
          </Button>
          <Button
            variant={selectedWindow === '30day' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedWindow('30day')}
          >
            Last 30 Days
          </Button>
          <Button
            variant={selectedWindow === '90day' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedWindow('90day')}
          >
            Last 90 Days
          </Button>
        </div>

        {/* Content Tabs */}
        <Tabs defaultValue="metrics" className="space-y-6">
          <TabsList className="grid w-full grid-cols-7 lg:w-auto">
            <TabsTrigger value="metrics">Performance</TabsTrigger>
            <TabsTrigger value="badges">Badges</TabsTrigger>
            <TabsTrigger value="goals">Goals</TabsTrigger>
            <TabsTrigger value="training">Training</TabsTrigger>
            <TabsTrigger value="sessions">Sessions</TabsTrigger>
            <TabsTrigger value="ratings">Ratings</TabsTrigger>
            <TabsTrigger value="comparison">Peer Stats</TabsTrigger>
          </TabsList>

          <TabsContent value="metrics" className="space-y-6">
            <TutorMetrics data={metricsData} loading={loading} />
          </TabsContent>

          <TabsContent value="badges" className="space-y-6">
            {tutorId && <BadgeGallery tutorId={tutorId} />}
          </TabsContent>

          <TabsContent value="goals" className="space-y-6">
            {tutorId && <GoalTracker tutorId={tutorId} />}
          </TabsContent>

          <TabsContent value="training" className="space-y-6">
            {tutorId && <TrainingLibrary tutorId={tutorId} />}
          </TabsContent>

          <TabsContent value="sessions" className="space-y-6">
            <TutorSessions
              data={sessionsData}
              loading={loading}
              onLoadMore={handleLoadMoreSessions}
              hasMore={sessionsData?.pagination.has_more}
            />
          </TabsContent>

          <TabsContent value="ratings" className="space-y-6">
            <SessionRatings ratings={feedbackData} loading={loading} />
          </TabsContent>

          <TabsContent value="comparison" className="space-y-6">
            {tutorId && <PeerComparison tutorId={tutorId} timeWindow={selectedWindow} />}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
