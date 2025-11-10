'use client';

/**
 * Main Dashboard Page for TutorMax Operations
 * Real-time dashboard with WebSocket integration
 *
 * Performance optimizations:
 * - Heavy analytics components are lazy loaded with dynamic imports
 * - ContributionGraph is loaded only when visible
 */

import React from 'react';
import dynamic from 'next/dynamic';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts';
import { useWebSocket } from '@/hooks';
import { CriticalAlerts } from '@/components/dashboard/CriticalAlerts';
import { InterventionTaskList } from '@/components/dashboard/InterventionTaskList';
import { PerformanceTiers } from '@/components/dashboard/PerformanceTiers';
import { ExportButton } from '@/components/dashboard/ExportButton';
import { CustomReportBuilder } from '@/components/dashboard/CustomReportBuilder';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Wifi, WifiOff, RefreshCw } from 'lucide-react';

// Lazy load heavy chart components with loading fallback
const PerformanceAnalytics = dynamic(
  () => import('@/components/dashboard/PerformanceAnalytics').then(mod => ({ default: mod.PerformanceAnalytics })),
  {
    loading: () => (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center h-64">
            <RefreshCw className="h-8 w-8 animate-spin text-gray-400" />
            <span className="ml-3 text-gray-500">Loading analytics...</span>
          </div>
        </CardContent>
      </Card>
    ),
    ssr: false, // Charts should only render on client
  }
);

const AdvancedAnalytics = dynamic(
  () => import('@/components/dashboard/AdvancedAnalytics').then(mod => ({ default: mod.AdvancedAnalytics })),
  {
    loading: () => (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center h-64">
            <RefreshCw className="h-8 w-8 animate-spin text-gray-400" />
            <span className="ml-3 text-gray-500">Loading advanced analytics...</span>
          </div>
        </CardContent>
      </Card>
    ),
    ssr: false,
  }
);

// Lazy load contribution graph (visualization library)
const ContributionGraphLazy = dynamic(
  () => import('@/components/kibo-ui/contribution-graph').then(mod => ({
    default: ({ data }: { data: any[] }) => (
      <mod.ContributionGraph data={data}>
        <mod.ContributionGraphCalendar>
          {({ activity, dayIndex, weekIndex }: any) => (
            <mod.ContributionGraphBlock
              activity={activity}
              dayIndex={dayIndex}
              weekIndex={weekIndex}
              className="hover:opacity-80 transition-opacity cursor-pointer"
            />
          )}
        </mod.ContributionGraphCalendar>
        <mod.ContributionGraphFooter>
          <mod.ContributionGraphTotalCount />
          <mod.ContributionGraphLegend />
        </mod.ContributionGraphFooter>
      </mod.ContributionGraph>
    )
  })),
  {
    loading: () => (
      <div className="flex items-center justify-center h-32">
        <RefreshCw className="h-6 w-6 animate-spin text-gray-400" />
        <span className="ml-2 text-sm text-gray-500">Loading heatmap...</span>
      </div>
    ),
    ssr: false,
  }
);

export default function DashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuth();
  const { state, resolveAlert, updateInterventionStatus } = useWebSocket();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  const connectionStatus = state.connected ? 'connected' : 'disconnected';
  const lastUpdateTime = state.lastUpdate
    ? new Date(state.lastUpdate).toLocaleTimeString()
    : 'Never';

  // Generate mock activity data for contribution graph (last 52 weeks)
  // Only generate on client to avoid hydration mismatch
  const activityData = React.useMemo(() => {
    if (!mounted) return [];

    const data = [];
    const today = new Date();
    for (let i = 364; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      const dateStr = date.toISOString().split('T')[0];
      // Simulate activity with deterministic pattern
      const count = (i % 7) * 2 + (i % 3);
      const level = count === 0 ? 0 : Math.min(4, Math.floor(count / 5) + 1);
      data.push({ date: dateStr, count, level });
    }
    return data;
  }, [mounted]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      <div className="container mx-auto py-6 px-4 space-y-6">
        {/* Header */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-2xl">TutorMax Operations Dashboard</CardTitle>
                <CardDescription>
                  {isAuthenticated
                    ? `Welcome back, ${user?.full_name}`
                    : 'Real-time tutor performance monitoring'}
                </CardDescription>
              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  {state.connected ? (
                    <Wifi className="h-5 w-5 text-green-600" />
                  ) : (
                    <WifiOff className="h-5 w-5 text-red-600" />
                  )}
                  <div className="text-sm">
                    <Badge variant={state.connected ? 'default' : 'destructive'}>
                      {connectionStatus}
                    </Badge>
                    <p className="text-xs text-muted-foreground mt-1">
                      Last update: {lastUpdateTime}
                    </p>
                  </div>
                </div>
                {/* Export and Report Tools */}
                <CustomReportBuilder />
                <ExportButton
                  reportType="tutor-performance"
                  filters={{
                    start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // Last 30 days
                    end_date: new Date(),
                  }}
                />
                <Button variant="outline" size="sm" onClick={() => router.push('/')}>
                  ← Back to Home
                </Button>
              </div>
            </div>
          </CardHeader>
        </Card>

        {/* Critical Alerts Section */}
        <section>
          <CriticalAlerts alerts={state.alerts} onResolve={resolveAlert} />
        </section>

        {/* Performance Tiers Section */}
        <section>
          <PerformanceTiers
            analytics={state.analytics}
            tutorMetrics={state.tutorMetrics}
            onTierClick={(tier) => {
              console.log('Tier clicked:', tier);
              // Future: Filter tutors by tier
            }}
          />
        </section>

        {/* Activity Heatmap Section */}
        <section>
          <Card>
            <CardHeader>
              <CardTitle>Activity Heatmap</CardTitle>
              <CardDescription>
                Daily activity overview for the past year
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ContributionGraphLazy data={activityData} />
            </CardContent>
          </Card>
        </section>

        {/* Main Dashboard Tabs */}
        <section>
          <Tabs defaultValue="overview" className="space-y-6">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="analytics">Analytics</TabsTrigger>
              <TabsTrigger value="interventions">Interventions</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-6">
              {/* Performance Analytics Section */}
              <PerformanceAnalytics
                analytics={state.analytics}
                tutorMetrics={state.tutorMetrics}
              />
            </TabsContent>

            <TabsContent value="analytics" className="space-y-6">
              {/* Advanced Analytics Section */}
              <AdvancedAnalytics />
            </TabsContent>

            <TabsContent value="interventions" className="space-y-6">
              {/* Intervention Tasks Section */}
              <InterventionTaskList
                tasks={state.interventionTasks}
                onUpdateStatus={updateInterventionStatus}
              />
            </TabsContent>
          </Tabs>
        </section>

        {/* Connection Status Footer */}
        {!state.connected && (
          <Card className="border-yellow-500 bg-yellow-50 dark:bg-yellow-950">
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <RefreshCw className="h-5 w-5 text-yellow-600 animate-spin" />
                <div>
                  <p className="font-semibold text-yellow-900 dark:text-yellow-100">
                    Reconnecting to server...
                  </p>
                  <p className="text-sm text-yellow-700 dark:text-yellow-300">
                    Real-time updates will resume when connection is restored.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
