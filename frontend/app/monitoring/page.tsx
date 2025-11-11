'use client';

/**
 * System Performance Monitoring Dashboard
 * Real-time metrics visualization with Prometheus integration
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { RefreshCw, AlertTriangle, CheckCircle, Activity, Database, Zap } from 'lucide-react';

interface MetricValue {
  value: number;
  timestamp: string;
}

interface PerformanceMetrics {
  http: {
    requests_total: number;
    requests_per_second: number;
    avg_response_time: number;
    p95_response_time: number;
    p99_response_time: number;
    error_rate: number;
  };
  database: {
    active_connections: number;
    avg_query_time: number;
    queries_per_second: number;
    slow_queries: number;
  };
  cache: {
    hit_rate: number;
    operations_per_second: number;
    memory_usage_mb: number;
  };
  celery: {
    active_tasks: number;
    pending_tasks: number;
    completed_today: number;
    failed_today: number;
  };
  system: {
    cpu_percent: number;
    memory_percent: number;
    memory_used_gb: number;
    memory_available_gb: number;
  };
  sla: {
    response_time_compliance: number;
    intervention_time_compliance: number;
    overall_compliance: number;
    violations_today: number;
  };
}

export default function MonitoringDashboard() {
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      // In production, this would fetch from /api/performance/dashboard
      // For now, using mock data
      const mockMetrics: PerformanceMetrics = {
        http: {
          requests_total: 15234,
          requests_per_second: 42.3,
          avg_response_time: 145,
          p95_response_time: 320,
          p99_response_time: 580,
          error_rate: 0.3,
        },
        database: {
          active_connections: 23,
          avg_query_time: 12.5,
          queries_per_second: 150,
          slow_queries: 2,
        },
        cache: {
          hit_rate: 87.5,
          operations_per_second: 320,
          memory_usage_mb: 420,
        },
        celery: {
          active_tasks: 5,
          pending_tasks: 12,
          completed_today: 3456,
          failed_today: 3,
        },
        system: {
          cpu_percent: 45.2,
          memory_percent: 62.3,
          memory_used_gb: 4.9,
          memory_available_gb: 2.9,
        },
        sla: {
          response_time_compliance: 98.5,
          intervention_time_compliance: 97.2,
          overall_compliance: 97.8,
          violations_today: 5,
        },
      };

      setMetrics(mockMetrics);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();

    if (autoRefresh) {
      const interval = setInterval(fetchMetrics, 30000); // Refresh every 30 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const getStatusColor = (value: number, threshold: number, inverse: boolean = false) => {
    const isGood = inverse ? value < threshold : value > threshold;
    return isGood ? 'text-green-600' : 'text-red-600';
  };

  const getStatusBadge = (value: number, threshold: number, inverse: boolean = false) => {
    const isGood = inverse ? value < threshold : value > threshold;
    return (
      <Badge variant={isGood ? 'default' : 'destructive'} className={isGood ? 'bg-green-100 text-green-800' : ''}>
        {isGood ? 'Healthy' : 'Warning'}
      </Badge>
    );
  };

  if (loading && !metrics) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <RefreshCw className="h-8 w-8 animate-spin text-gray-400" />
        <span className="ml-3 text-gray-600">Loading metrics...</span>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      <div className="container mx-auto py-6 px-4 space-y-6">
        {/* Header */}
        <Card className="shadow-lg border-primary/10">
          <CardHeader>
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <Activity className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <CardTitle className="text-2xl font-bold">System Performance Monitoring</CardTitle>
                    <CardDescription className="mt-1">
                      Real-time metrics • Last updated: {lastUpdate.toLocaleTimeString()}
                    </CardDescription>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={autoRefresh ? "default" : "outline"} className="transition-all">
                  <div className={`h-2 w-2 rounded-full ${autoRefresh ? 'bg-success animate-pulse' : 'bg-muted-foreground'} mr-2`} />
                  {autoRefresh ? 'Live' : 'Paused'}
                </Badge>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setAutoRefresh(!autoRefresh)}
                  className="transition-all"
                >
                  <Activity className={`h-4 w-4 mr-2 ${autoRefresh ? 'animate-pulse' : ''}`} />
                  {autoRefresh ? 'Pause' : 'Resume'}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={fetchMetrics}
                  disabled={loading}
                  className="transition-all"
                >
                  <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                  Refresh
                </Button>
              </div>
            </div>
          </CardHeader>
        </Card>

        {/* SLA Status Alert */}
        {metrics && metrics.sla.overall_compliance < 95 && (
          <Alert variant="destructive" className="animate-slide-in-top border-destructive/50 shadow-lg">
            <AlertTriangle className="h-5 w-5" />
            <AlertTitle className="font-semibold">SLA Compliance Warning</AlertTitle>
            <AlertDescription className="mt-1">
              Overall SLA compliance is at <span className="font-semibold">{metrics.sla.overall_compliance}%</span> (target: 95%).{' '}
              <span className="font-semibold">{metrics.sla.violations_today}</span> violations today.
            </AlertDescription>
          </Alert>
        )}

        {/* System Health Indicator */}
        {metrics && (
          <Card className="shadow-md border-l-4 border-l-success">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <CheckCircle className="h-6 w-6 text-success" />
                  <div>
                    <div className="font-semibold text-lg">System Status: Operational</div>
                    <div className="text-sm text-muted-foreground">All services running normally</div>
                  </div>
                </div>
                <div className="flex items-center gap-6">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-success">{metrics.sla.overall_compliance}%</div>
                    <div className="text-xs text-muted-foreground">SLA</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-primary">{metrics.http.requests_per_second.toFixed(1)}</div>
                    <div className="text-xs text-muted-foreground">req/s</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-chart-3">{metrics.cache.hit_rate}%</div>
                    <div className="text-xs text-muted-foreground">cache hit</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Metrics Tabs */}
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="http">HTTP</TabsTrigger>
            <TabsTrigger value="database">Database</TabsTrigger>
            <TabsTrigger value="cache">Cache</TabsTrigger>
            <TabsTrigger value="sla">SLA</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* HTTP Metrics */}
              <Card className="transition-card hover-lift border-l-4 border-l-primary">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-semibold flex items-center text-muted-foreground">
                    <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center mr-2">
                      <Zap className="h-4 w-4 text-primary" />
                    </div>
                    HTTP Requests
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold mb-2">{metrics?.http.requests_per_second.toFixed(1)} <span className="text-lg text-muted-foreground">req/s</span></div>
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground">
                      p95: <span className="font-semibold text-foreground">{metrics?.http.p95_response_time}ms</span>
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Errors: <span className="font-semibold text-foreground">{metrics?.http.error_rate}%</span>
                    </p>
                  </div>
                  <div className="mt-3">{getStatusBadge(metrics?.http.p95_response_time || 0, 500, true)}</div>
                </CardContent>
              </Card>

              {/* Database Metrics */}
              <Card className="transition-card hover-lift border-l-4 border-l-chart-3">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-semibold flex items-center text-muted-foreground">
                    <div className="h-8 w-8 rounded-lg bg-chart-3/10 flex items-center justify-center mr-2">
                      <Database className="h-4 w-4 text-chart-3" />
                    </div>
                    Database
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold mb-2">{metrics?.database.active_connections} <span className="text-lg text-muted-foreground">conn</span></div>
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground">
                      Avg: <span className="font-semibold text-foreground">{metrics?.database.avg_query_time}ms</span>
                    </p>
                    <p className="text-xs text-muted-foreground">
                      <span className="font-semibold text-foreground">{metrics?.database.queries_per_second}</span> queries/s
                    </p>
                  </div>
                  <div className="mt-3">{getStatusBadge(metrics?.database.active_connections || 0, 80, true)}</div>
                </CardContent>
              </Card>

              {/* Cache Metrics */}
              <Card className="transition-card hover-lift border-l-4 border-l-success">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-semibold flex items-center text-muted-foreground">
                    <div className="h-8 w-8 rounded-lg bg-success/10 flex items-center justify-center mr-2">
                      <Activity className="h-4 w-4 text-success" />
                    </div>
                    Cache Hit Rate
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold mb-2">{metrics?.cache.hit_rate}<span className="text-lg text-muted-foreground">%</span></div>
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground">
                      <span className="font-semibold text-foreground">{metrics?.cache.operations_per_second}</span> ops/s
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Memory: <span className="font-semibold text-foreground">{metrics?.cache.memory_usage_mb} MB</span>
                    </p>
                  </div>
                  <div className="mt-3">{getStatusBadge(metrics?.cache.hit_rate || 0, 80)}</div>
                </CardContent>
              </Card>

              {/* SLA Compliance */}
              <Card className="transition-card hover-lift border-l-4 border-l-chart-4">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-semibold flex items-center text-muted-foreground">
                    <div className="h-8 w-8 rounded-lg bg-chart-4/10 flex items-center justify-center mr-2">
                      <CheckCircle className="h-4 w-4 text-chart-4" />
                    </div>
                    SLA Compliance
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold mb-2">{metrics?.sla.overall_compliance}<span className="text-lg text-muted-foreground">%</span></div>
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground">
                      Target: <span className="font-semibold text-foreground">95%</span>
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Violations: <span className="font-semibold text-foreground">{metrics?.sla.violations_today}</span> today
                    </p>
                  </div>
                  <div className="mt-3">{getStatusBadge(metrics?.sla.overall_compliance || 0, 95)}</div>
                </CardContent>
              </Card>
            </div>

            {/* System Resources */}
            <Card className="shadow-md">
              <CardHeader>
                <CardTitle className="text-lg font-bold">System Resources</CardTitle>
                <CardDescription>CPU and memory utilization</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-semibold">CPU Usage</span>
                      <span className={`text-sm font-bold ${getStatusColor(metrics?.system.cpu_percent || 0, 80, true)}`}>
                        {metrics?.system.cpu_percent}%
                      </span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-3 overflow-hidden">
                      <div
                        className="bg-gradient-to-r from-primary to-primary/80 h-3 rounded-full transition-all duration-500"
                        style={{ width: `${metrics?.system.cpu_percent}%` }}
                      />
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {metrics?.system.cpu_percent && metrics.system.cpu_percent < 80 ? 'Normal operation' : 'High load'}
                    </div>
                  </div>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-semibold">Memory Usage</span>
                      <span className={`text-sm font-bold ${getStatusColor(metrics?.system.memory_percent || 0, 80, true)}`}>
                        {metrics?.system.memory_percent}%
                      </span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-3 overflow-hidden">
                      <div
                        className="bg-gradient-to-r from-chart-3 to-chart-3/80 h-3 rounded-full transition-all duration-500"
                        style={{ width: `${metrics?.system.memory_percent}%` }}
                      />
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {metrics?.system.memory_used_gb}GB used / {metrics?.system.memory_available_gb}GB available
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Celery Tasks */}
            <Card className="shadow-md">
              <CardHeader>
                <CardTitle className="text-lg font-bold">Background Tasks (Celery)</CardTitle>
                <CardDescription>Async task processing status</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                  <div className="text-center p-4 rounded-lg bg-warning/10 border border-warning/20">
                    <div className="text-3xl font-bold text-warning mb-1">{metrics?.celery.active_tasks}</div>
                    <p className="text-sm font-medium text-muted-foreground">Active</p>
                  </div>
                  <div className="text-center p-4 rounded-lg bg-primary/10 border border-primary/20">
                    <div className="text-3xl font-bold text-primary mb-1">{metrics?.celery.pending_tasks}</div>
                    <p className="text-sm font-medium text-muted-foreground">Pending</p>
                  </div>
                  <div className="text-center p-4 rounded-lg bg-success/10 border border-success/20">
                    <div className="text-3xl font-bold text-success mb-1">{metrics?.celery.completed_today}</div>
                    <p className="text-sm font-medium text-muted-foreground">Completed</p>
                  </div>
                  <div className="text-center p-4 rounded-lg bg-destructive/10 border border-destructive/20">
                    <div className="text-3xl font-bold text-destructive mb-1">{metrics?.celery.failed_today}</div>
                    <p className="text-sm font-medium text-muted-foreground">Failed</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* HTTP Tab */}
          <TabsContent value="http">
            <Card className="shadow-md">
              <CardHeader>
                <CardTitle className="text-lg font-bold">HTTP Performance Metrics</CardTitle>
                <CardDescription>Request latency, throughput, and error rates</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <div className="p-4 rounded-lg bg-primary/5 border border-primary/10">
                      <div className="text-sm text-muted-foreground mb-1">Requests/sec</div>
                      <div className="text-3xl font-bold text-primary">{metrics?.http.requests_per_second}</div>
                    </div>
                    <div className="p-4 rounded-lg bg-chart-2/5 border border-chart-2/10">
                      <div className="text-sm text-muted-foreground mb-1">Avg Response Time</div>
                      <div className="text-3xl font-bold text-chart-2">{metrics?.http.avg_response_time}ms</div>
                    </div>
                    <div className="p-4 rounded-lg bg-destructive/5 border border-destructive/10">
                      <div className="text-sm text-muted-foreground mb-1">Error Rate</div>
                      <div className="text-3xl font-bold text-destructive">{metrics?.http.error_rate}%</div>
                    </div>
                    <div className="p-4 rounded-lg bg-chart-3/5 border border-chart-3/10">
                      <div className="text-sm text-muted-foreground mb-1">P95 Latency</div>
                      <div className="text-3xl font-bold text-chart-3">{metrics?.http.p95_response_time}ms</div>
                    </div>
                    <div className="p-4 rounded-lg bg-chart-4/5 border border-chart-4/10">
                      <div className="text-sm text-muted-foreground mb-1">P99 Latency</div>
                      <div className="text-3xl font-bold text-chart-4">{metrics?.http.p99_response_time}ms</div>
                    </div>
                    <div className="p-4 rounded-lg bg-muted/50 border border-border">
                      <div className="text-sm text-muted-foreground mb-1">Total Requests</div>
                      <div className="text-3xl font-bold">{metrics?.http.requests_total.toLocaleString()}</div>
                    </div>
                  </div>
                  <Alert>
                    <AlertDescription className="text-sm">
                      <span className="font-semibold">Performance Targets:</span> p95 &lt; 200ms, p99 &lt; 500ms, Error rate &lt; 1%
                    </AlertDescription>
                  </Alert>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Database Tab */}
          <TabsContent value="database">
            <Card className="shadow-md">
              <CardHeader>
                <CardTitle className="text-lg font-bold">Database Performance</CardTitle>
                <CardDescription>Connection pool, query performance, and slow queries</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-4 rounded-lg bg-chart-3/5 border border-chart-3/10">
                    <div className="text-sm text-muted-foreground mb-1">Active Connections</div>
                    <div className="text-3xl font-bold text-chart-3">{metrics?.database.active_connections}</div>
                    <div className="text-xs text-muted-foreground mt-1">/ 100 max</div>
                  </div>
                  <div className="p-4 rounded-lg bg-primary/5 border border-primary/10">
                    <div className="text-sm text-muted-foreground mb-1">Queries/sec</div>
                    <div className="text-3xl font-bold text-primary">{metrics?.database.queries_per_second}</div>
                  </div>
                  <div className="p-4 rounded-lg bg-success/5 border border-success/10">
                    <div className="text-sm text-muted-foreground mb-1">Avg Query Time</div>
                    <div className="text-3xl font-bold text-success">{metrics?.database.avg_query_time}ms</div>
                  </div>
                  <div className="p-4 rounded-lg bg-destructive/5 border border-destructive/10">
                    <div className="text-sm text-muted-foreground mb-1">Slow Queries</div>
                    <div className="text-3xl font-bold text-destructive">{metrics?.database.slow_queries}</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Cache Tab */}
          <TabsContent value="cache">
            <Card className="shadow-md">
              <CardHeader>
                <CardTitle className="text-lg font-bold">Cache Performance</CardTitle>
                <CardDescription>Redis cache hit rates and memory usage</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-6 rounded-lg bg-success/5 border border-success/10 text-center">
                    <div className="text-sm text-muted-foreground mb-2">Hit Rate</div>
                    <div className="text-4xl font-bold text-success mb-2">{metrics?.cache.hit_rate}%</div>
                    <div className="text-xs text-muted-foreground">Target: &gt; 80%</div>
                  </div>
                  <div className="p-6 rounded-lg bg-primary/5 border border-primary/10 text-center">
                    <div className="text-sm text-muted-foreground mb-2">Operations/sec</div>
                    <div className="text-4xl font-bold text-primary mb-2">{metrics?.cache.operations_per_second}</div>
                    <div className="text-xs text-muted-foreground">Cache throughput</div>
                  </div>
                  <div className="p-6 rounded-lg bg-chart-4/5 border border-chart-4/10 text-center">
                    <div className="text-sm text-muted-foreground mb-2">Memory Usage</div>
                    <div className="text-4xl font-bold text-chart-4 mb-2">{metrics?.cache.memory_usage_mb}</div>
                    <div className="text-xs text-muted-foreground">MB allocated</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* SLA Tab */}
          <TabsContent value="sla">
            <Card className="shadow-md">
              <CardHeader>
                <CardTitle className="text-lg font-bold">SLA Compliance</CardTitle>
                <CardDescription>Service Level Agreement tracking and violations</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-6 rounded-lg bg-success/5 border-2 border-success/20 text-center">
                      <div className="text-sm text-muted-foreground mb-2">Overall Compliance</div>
                      <div className="text-5xl font-bold text-success mb-2">{metrics?.sla.overall_compliance}%</div>
                      <Badge variant="outline" className="bg-success/10 text-success border-success/20">
                        {metrics?.sla.overall_compliance && metrics.sla.overall_compliance >= 95 ? 'Meeting SLA' : 'Below Target'}
                      </Badge>
                    </div>
                    <div className="p-6 rounded-lg bg-primary/5 border border-primary/10 text-center">
                      <div className="text-sm text-muted-foreground mb-2">Response Time SLA</div>
                      <div className="text-4xl font-bold text-primary mb-2">{metrics?.sla.response_time_compliance}%</div>
                      <div className="text-xs text-muted-foreground">API response targets</div>
                    </div>
                    <div className="p-6 rounded-lg bg-chart-3/5 border border-chart-3/10 text-center">
                      <div className="text-sm text-muted-foreground mb-2">Intervention Time SLA</div>
                      <div className="text-4xl font-bold text-chart-3 mb-2">{metrics?.sla.intervention_time_compliance}%</div>
                      <div className="text-xs text-muted-foreground">Intervention handling</div>
                    </div>
                  </div>
                  <div className="p-6 rounded-lg bg-destructive/5 border border-destructive/10">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm text-muted-foreground mb-1">SLA Violations Today</div>
                        <div className="text-5xl font-bold text-destructive">{metrics?.sla.violations_today}</div>
                      </div>
                      <AlertTriangle className="h-16 w-16 text-destructive/30" />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Grafana Link */}
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-sm text-gray-600 mb-3">
                For detailed time-series visualizations and alerting, view the Grafana dashboard
              </p>
              <Button variant="outline">
                <Activity className="h-4 w-4 mr-2" />
                Open Grafana Dashboard
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
