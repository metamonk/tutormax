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
import { ThemeToggle } from '@/components/theme-toggle';
import { Breadcrumb } from '@/components/navigation';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Wifi, WifiOff, RefreshCw } from 'lucide-react';
import { ChartSkeleton, CardSkeleton } from '@/components/ui/skeleton-patterns';
import { Skeleton } from '@/components/ui/skeleton';

// Lazy load heavy chart components with loading fallback
const PerformanceAnalytics = dynamic(
  () => import('@/components/dashboard/PerformanceAnalytics').then(mod => ({ default: mod.PerformanceAnalytics })),
  {
    loading: () => (
      <div className="grid gap-6 md:grid-cols-2">
        <CardSkeleton />
        <CardSkeleton />
      </div>
    ),
    ssr: false, // Charts should only render on client
  }
);

const AdvancedAnalytics = dynamic(
  () => import('@/components/dashboard/AdvancedAnalytics').then(mod => ({ default: mod.AdvancedAnalytics })),
  {
    loading: () => (
      <div className="space-y-6">
        <ChartSkeleton />
        <div className="grid gap-6 md:grid-cols-2">
          <ChartSkeleton />
          <ChartSkeleton />
        </div>
      </div>
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
      <div className="space-y-2">
        <div className="flex gap-1">
          {Array.from({ length: 53 }).map((_, i) => (
            <div key={i} className="flex flex-col gap-1">
              {Array.from({ length: 7 }).map((_, j) => (
                <Skeleton key={`${i}-${j}`} className="h-3 w-3 rounded-sm" />
              ))}
            </div>
          ))}
        </div>
        <div className="flex justify-between items-center pt-2">
          <Skeleton className="h-3 w-32" />
          <Skeleton className="h-3 w-24" />
        </div>
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
    <div className="min-h-screen bg-background">
      <div className="mx-auto max-w-[1400px] space-y-8 p-6 lg:p-8">
        {/* Breadcrumb */}
        <Breadcrumb />

        {/* Header */}
        <div className="space-y-6">
          <div className="flex items-start justify-between">
            <div className="space-y-2">
              <h1 className="text-balance text-3xl font-bold tracking-tight lg:text-4xl">
                Tutor Performance Dashboard
              </h1>
              <p className="text-pretty text-muted-foreground">
                {isAuthenticated
                  ? `Welcome back, ${user?.full_name} • Real-time performance monitoring`
                  : 'Real-time tutor performance monitoring and analytics'}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-2 shadow-sm">
                {state.connected ? (
                  <Wifi className="h-4 w-4 text-emerald-600" />
                ) : (
                  <WifiOff className="h-4 w-4 text-red-600" />
                )}
                <div className="text-sm">
                  <Badge variant={state.connected ? 'default' : 'destructive'} className="font-medium">
                    {connectionStatus}
                  </Badge>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {lastUpdateTime}
                  </p>
                </div>
              </div>
              <ThemeToggle />
              <CustomReportBuilder />
              <ExportButton
                reportType="tutor-performance"
                filters={{
                  start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
                  end_date: new Date(),
                }}
              />
              <Button variant="outline" size="sm" onClick={() => router.push('/')}>
                ← Home
              </Button>
            </div>
          </div>
        </div>

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
          <Card className="border-border bg-card shadow-sm">
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
          <Tabs defaultValue="overview" className="space-y-8">
            <TabsList className="grid w-full grid-cols-3 lg:w-[400px]">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="analytics">Analytics</TabsTrigger>
              <TabsTrigger value="interventions">Interventions</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-8">
              <PerformanceAnalytics
                analytics={state.analytics}
                tutorMetrics={state.tutorMetrics}
              />
            </TabsContent>

            <TabsContent value="analytics" className="space-y-8">
              <AdvancedAnalytics />
            </TabsContent>

            <TabsContent value="interventions" className="space-y-8">
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
