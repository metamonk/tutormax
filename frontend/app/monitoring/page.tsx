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
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-2xl">System Performance Monitoring</CardTitle>
                <CardDescription>
                  Real-time metrics from Prometheus • Last updated: {lastUpdate.toLocaleTimeString()}
                </CardDescription>
              </div>
              <div className="flex items-center gap-3">
                <Button variant="outline" size="sm" onClick={() => setAutoRefresh(!autoRefresh)}>
                  <Activity className={`h-4 w-4 mr-2 ${autoRefresh ? 'animate-pulse' : ''}`} />
                  {autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
                </Button>
                <Button variant="outline" size="sm" onClick={fetchMetrics}>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Refresh
                </Button>
              </div>
            </div>
          </CardHeader>
        </Card>

        {/* SLA Status Alert */}
        {metrics && metrics.sla.overall_compliance < 95 && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>SLA Compliance Warning</AlertTitle>
            <AlertDescription>
              Overall SLA compliance is at {metrics.sla.overall_compliance}% (target: 95%). {metrics.sla.violations_today}{' '}
              violations today.
            </AlertDescription>
          </Alert>
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
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* HTTP Metrics */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium flex items-center">
                    <Zap className="h-4 w-4 mr-2 text-blue-600" />
                    HTTP Requests
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{metrics?.http.requests_per_second.toFixed(1)} req/s</div>
                  <p className="text-xs text-gray-600 mt-1">
                    p95: {metrics?.http.p95_response_time}ms • Errors: {metrics?.http.error_rate}%
                  </p>
                  {getStatusBadge(metrics?.http.p95_response_time || 0, 500, true)}
                </CardContent>
              </Card>

              {/* Database Metrics */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium flex items-center">
                    <Database className="h-4 w-4 mr-2 text-purple-600" />
                    Database
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{metrics?.database.active_connections} connections</div>
                  <p className="text-xs text-gray-600 mt-1">
                    Avg query: {metrics?.database.avg_query_time}ms • {metrics?.database.queries_per_second} q/s
                  </p>
                  {getStatusBadge(metrics?.database.active_connections || 0, 80, true)}
                </CardContent>
              </Card>

              {/* Cache Metrics */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium flex items-center">
                    <Activity className="h-4 w-4 mr-2 text-green-600" />
                    Cache Hit Rate
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{metrics?.cache.hit_rate}%</div>
                  <p className="text-xs text-gray-600 mt-1">
                    {metrics?.cache.operations_per_second} ops/s • {metrics?.cache.memory_usage_mb} MB
                  </p>
                  {getStatusBadge(metrics?.cache.hit_rate || 0, 80)}
                </CardContent>
              </Card>

              {/* SLA Compliance */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium flex items-center">
                    <CheckCircle className="h-4 w-4 mr-2 text-yellow-600" />
                    SLA Compliance
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{metrics?.sla.overall_compliance}%</div>
                  <p className="text-xs text-gray-600 mt-1">{metrics?.sla.violations_today} violations today</p>
                  {getStatusBadge(metrics?.sla.overall_compliance || 0, 95)}
                </CardContent>
              </Card>
            </div>

            {/* System Resources */}
            <Card>
              <CardHeader>
                <CardTitle>System Resources</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium">CPU Usage</span>
                      <span className={`text-sm font-bold ${getStatusColor(metrics?.system.cpu_percent || 0, 80, true)}`}>
                        {metrics?.system.cpu_percent}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${metrics?.system.cpu_percent}%` }}
                      />
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium">Memory Usage</span>
                      <span
                        className={`text-sm font-bold ${getStatusColor(metrics?.system.memory_percent || 0, 80, true)}`}
                      >
                        {metrics?.system.memory_percent}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-purple-600 h-2 rounded-full"
                        style={{ width: `${metrics?.system.memory_percent}%` }}
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Celery Tasks */}
            <Card>
              <CardHeader>
                <CardTitle>Background Tasks (Celery)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <div className="text-2xl font-bold text-yellow-600">{metrics?.celery.active_tasks}</div>
                    <p className="text-xs text-gray-600">Active</p>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-blue-600">{metrics?.celery.pending_tasks}</div>
                    <p className="text-xs text-gray-600">Pending</p>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-green-600">{metrics?.celery.completed_today}</div>
                    <p className="text-xs text-gray-600">Completed Today</p>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-red-600">{metrics?.celery.failed_today}</div>
                    <p className="text-xs text-gray-600">Failed Today</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* HTTP Tab */}
          <TabsContent value="http">
            <Card>
              <CardHeader>
                <CardTitle>HTTP Performance Metrics</CardTitle>
                <CardDescription>Request latency, throughput, and error rates</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <div>
                      <div className="text-sm text-gray-600">Requests/sec</div>
                      <div className="text-2xl font-bold">{metrics?.http.requests_per_second}</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">Avg Response Time</div>
                      <div className="text-2xl font-bold">{metrics?.http.avg_response_time}ms</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">Error Rate</div>
                      <div className="text-2xl font-bold">{metrics?.http.error_rate}%</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">P95 Latency</div>
                      <div className="text-2xl font-bold">{metrics?.http.p95_response_time}ms</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">P99 Latency</div>
                      <div className="text-2xl font-bold">{metrics?.http.p99_response_time}ms</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">Total Requests</div>
                      <div className="text-2xl font-bold">{metrics?.http.requests_total.toLocaleString()}</div>
                    </div>
                  </div>
                  <div className="text-xs text-gray-500 mt-4">
                    ℹ️ Target: p95 {'<'} 200ms, p99 {'<'} 500ms, Error rate {'<'} 1%
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Database Tab */}
          <TabsContent value="database">
            <Card>
              <CardHeader>
                <CardTitle>Database Performance</CardTitle>
                <CardDescription>Connection pool, query performance, and slow queries</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                  <div>
                    <div className="text-sm text-gray-600">Active Connections</div>
                    <div className="text-2xl font-bold">{metrics?.database.active_connections} / 100</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">Queries/sec</div>
                    <div className="text-2xl font-bold">{metrics?.database.queries_per_second}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">Avg Query Time</div>
                    <div className="text-2xl font-bold">{metrics?.database.avg_query_time}ms</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">Slow Queries</div>
                    <div className="text-2xl font-bold text-red-600">{metrics?.database.slow_queries}</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Cache Tab */}
          <TabsContent value="cache">
            <Card>
              <CardHeader>
                <CardTitle>Cache Performance</CardTitle>
                <CardDescription>Redis cache hit rates and memory usage</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-6">
                  <div>
                    <div className="text-sm text-gray-600">Hit Rate</div>
                    <div className="text-2xl font-bold text-green-600">{metrics?.cache.hit_rate}%</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">Operations/sec</div>
                    <div className="text-2xl font-bold">{metrics?.cache.operations_per_second}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">Memory Usage</div>
                    <div className="text-2xl font-bold">{metrics?.cache.memory_usage_mb} MB</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* SLA Tab */}
          <TabsContent value="sla">
            <Card>
              <CardHeader>
                <CardTitle>SLA Compliance</CardTitle>
                <CardDescription>Service Level Agreement tracking and violations</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
                    <div>
                      <div className="text-sm text-gray-600">Overall Compliance</div>
                      <div className="text-3xl font-bold text-green-600">{metrics?.sla.overall_compliance}%</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">Response Time SLA</div>
                      <div className="text-2xl font-bold">{metrics?.sla.response_time_compliance}%</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">Intervention Time SLA</div>
                      <div className="text-2xl font-bold">{metrics?.sla.intervention_time_compliance}%</div>
                    </div>
                  </div>
                  <div className="mt-6">
                    <div className="text-sm text-gray-600 mb-2">Violations Today</div>
                    <div className="text-4xl font-bold text-red-600">{metrics?.sla.violations_today}</div>
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
