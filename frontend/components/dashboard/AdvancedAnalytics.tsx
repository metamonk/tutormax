'use client';

/**
 * Advanced Analytics Component
 *
 * Comprehensive analytics dashboard featuring:
 * - Churn heatmaps
 * - Cohort analysis
 * - Intervention effectiveness
 * - Predictive insights
 *
 * Part of Task 9: Advanced Analytics Dashboard
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  TrendingUp, TrendingDown, Users, Target, AlertTriangle,
  BarChart3, Activity, RefreshCw, Download
} from 'lucide-react';
import { ChurnHeatmap } from './analytics/ChurnHeatmap';
import { CohortAnalysis } from './analytics/CohortAnalysis';
import { InterventionEffectiveness } from './analytics/InterventionEffectiveness';
import { PredictiveInsights } from './analytics/PredictiveInsights';

interface AnalyticsOverview {
  summary: {
    total_tutors: number;
    active_tutors: number;
    churn_rate_30d: number;
    churned_last_30d: number;
    avg_retention_rate: number;
    generated_at: string;
  };
  churn_insights: {
    trend: string;
    high_risk_count: number;
  };
  intervention_summary: {
    total_active: number;
    avg_effectiveness: number;
  };
  quick_actions: Array<{
    action: string;
    count: number;
    priority: string;
  }>;
}

export function AdvancedAnalytics() {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [refreshing, setRefreshing] = useState(false);

  const fetchOverview = async () => {
    try {
      setRefreshing(true);
      const response = await fetch('http://localhost:8000/api/analytics/overview');

      if (!response.ok) {
        throw new Error(`Failed to fetch analytics: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      setOverview(data);
    } catch (error) {
      console.error('Failed to fetch analytics overview:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchOverview();
    // Refresh every 5 minutes
    const interval = setInterval(fetchOverview, 300000);
    return () => clearInterval(interval);
  }, []);

  const exportData = () => {
    // TODO: Implement export functionality
    console.log('Exporting analytics data...');
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
            <span className="ml-3 text-lg">Loading analytics...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Actions */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-2xl">Advanced Analytics</CardTitle>
              <CardDescription>
                Comprehensive insights into tutor performance, retention, and interventions
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={fetchOverview}
                disabled={refreshing}
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              <Button variant="outline" size="sm" onClick={exportData}>
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Summary Cards */}
      {overview && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Total Tutors */}
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Total Tutors</CardDescription>
              <CardTitle className="text-3xl">{overview.summary.total_tutors}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center text-sm">
                <Users className="h-4 w-4 mr-2 text-blue-600" />
                <span className="text-muted-foreground">
                  {overview.summary.active_tutors} active
                </span>
              </div>
            </CardContent>
          </Card>

          {/* Churn Rate */}
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>30-Day Churn Rate</CardDescription>
              <CardTitle className="text-3xl">
                {overview.summary.churn_rate_30d.toFixed(1)}%
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center text-sm">
                {overview.churn_insights.trend === 'increasing' ? (
                  <>
                    <TrendingUp className="h-4 w-4 mr-2 text-red-600" />
                    <span className="text-red-600">Increasing</span>
                  </>
                ) : (
                  <>
                    <TrendingDown className="h-4 w-4 mr-2 text-green-600" />
                    <span className="text-green-600">Stable</span>
                  </>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Retention Rate */}
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Avg Retention Rate</CardDescription>
              <CardTitle className="text-3xl">
                {overview.summary.avg_retention_rate.toFixed(1)}%
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center text-sm">
                <Target className="h-4 w-4 mr-2 text-green-600" />
                <span className="text-muted-foreground">Last 6 months</span>
              </div>
            </CardContent>
          </Card>

          {/* High Risk Tutors */}
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>High Risk Tutors</CardDescription>
              <CardTitle className="text-3xl">
                {overview.churn_insights.high_risk_count}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center text-sm">
                <AlertTriangle className="h-4 w-4 mr-2 text-orange-600" />
                <span className="text-orange-600">Needs attention</span>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Quick Actions */}
      {overview && overview.quick_actions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Recommended actions based on current data</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-3">
              {overview.quick_actions.map((action, index) => (
                <Badge
                  key={index}
                  variant={action.priority === 'high' ? 'destructive' : 'default'}
                  className="px-4 py-2 cursor-pointer hover:opacity-80"
                >
                  {action.action} ({action.count})
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Analytics Tabs */}
      <Card>
        <CardContent className="pt-6">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-4 mb-6">
              <TabsTrigger value="overview">
                <BarChart3 className="h-4 w-4 mr-2" />
                Overview
              </TabsTrigger>
              <TabsTrigger value="churn">
                <Activity className="h-4 w-4 mr-2" />
                Churn Analysis
              </TabsTrigger>
              <TabsTrigger value="cohort">
                <Users className="h-4 w-4 mr-2" />
                Cohorts
              </TabsTrigger>
              <TabsTrigger value="interventions">
                <Target className="h-4 w-4 mr-2" />
                Interventions
              </TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <PredictiveInsights />
                <InterventionEffectiveness summary={true} />
              </div>
            </TabsContent>

            <TabsContent value="churn">
              <ChurnHeatmap />
            </TabsContent>

            <TabsContent value="cohort">
              <CohortAnalysis />
            </TabsContent>

            <TabsContent value="interventions">
              <InterventionEffectiveness summary={false} />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
