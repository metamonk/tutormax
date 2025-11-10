'use client';

/**
 * Compliance Reports Component
 * Displays FERPA, COPPA, and GDPR compliance dashboards and reports
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsContent } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Shield,
  Download,
  AlertTriangle,
  CheckCircle2,
  Clock,
  FileText,
  TrendingUp,
  Users,
  FileCheck
} from 'lucide-react';
import type {
  ComplianceDashboardResponse,
  ComplianceMetrics,
  ComplianceReport,
  ComplianceIssue
} from '@/lib/types';
import { cn } from '@/lib/utils';

interface ComplianceReportsProps {
  apiEndpoint?: string;
}

export function ComplianceReports({ apiEndpoint = '/api/admin/compliance/reports' }: ComplianceReportsProps) {
  const [data, setData] = useState<ComplianceDashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedReport, setSelectedReport] = useState<ComplianceReport | null>(null);

  useEffect(() => {
    fetchComplianceData();
  }, []);

  const fetchComplianceData = async () => {
    setLoading(true);
    try {
      const response = await fetch(apiEndpoint);
      const result = await response.json();
      if (result.success) {
        setData(result);
      }
    } catch (error) {
      console.error('Failed to fetch compliance data:', error);
    } finally {
      setLoading(false);
    }
  };

  const downloadReport = (report: ComplianceReport) => {
    const reportData = JSON.stringify(report, null, 2);
    const blob = new Blob([reportData], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `compliance-report-${report.report_type}-${report.id}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getSeverityColor = (severity: ComplianceIssue['severity']) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100';
      case 'high':
        return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-100';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100';
      case 'low':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100';
    }
  };

  const getStatusColor = (status: ComplianceIssue['status']) => {
    switch (status) {
      case 'open':
        return 'destructive';
      case 'in_progress':
        return 'default';
      case 'resolved':
        return 'secondary';
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="text-muted-foreground">Loading compliance data...</div>
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="text-muted-foreground">Failed to load compliance data</div>
        </CardContent>
      </Card>
    );
  }

  const { metrics, recent_reports, active_issues } = data;

  return (
    <div className="space-y-6">
      {/* Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>FERPA Compliance</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="text-3xl font-bold">
                {(metrics.ferpa_compliance_rate * 100).toFixed(1)}%
              </div>
              <Shield className="h-8 w-8 text-blue-500" />
            </div>
            <div className="text-xs text-muted-foreground mt-2">
              Educational Privacy Rights
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>COPPA Consent Rate</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="text-3xl font-bold">
                {(metrics.coppa_consent_rate * 100).toFixed(1)}%
              </div>
              <Users className="h-8 w-8 text-green-500" />
            </div>
            <div className="text-xs text-muted-foreground mt-2">
              Parental Consent (Under 13)
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>GDPR Compliance</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="text-3xl font-bold">
                {(metrics.gdpr_compliance_rate * 100).toFixed(1)}%
              </div>
              <FileCheck className="h-8 w-8 text-purple-500" />
            </div>
            <div className="text-xs text-muted-foreground mt-2">
              Data Protection Rights
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Pending Data Requests</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="text-3xl font-bold">{metrics.pending_data_requests}</div>
              <Clock className="h-8 w-8 text-orange-500" />
            </div>
            <div className="text-xs text-muted-foreground mt-2">
              {metrics.total_data_requests} total requests
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Active Issues */}
      {active_issues.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-orange-500" />
              Active Compliance Issues
            </CardTitle>
            <CardDescription>{active_issues.length} issues requiring attention</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {active_issues.map((issue) => (
                <Card key={issue.id} className="border-l-4 border-l-orange-500">
                  <CardHeader className="pb-2">
                    <div className="flex items-start justify-between">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <CardTitle className="text-base">{issue.issue_type}</CardTitle>
                          <Badge className={getSeverityColor(issue.severity)}>
                            {issue.severity}
                          </Badge>
                          <Badge variant={getStatusColor(issue.status) as any}>
                            {issue.status.replace('_', ' ')}
                          </Badge>
                        </div>
                        <CardDescription>{issue.description}</CardDescription>
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {new Date(issue.detected_at).toLocaleDateString()}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-4 text-sm">
                      <div>
                        <span className="text-muted-foreground">Affected Records:</span>{' '}
                        <span className="font-medium">{issue.affected_records}</span>
                      </div>
                      {issue.resolved_at && (
                        <div>
                          <span className="text-muted-foreground">Resolved:</span>{' '}
                          <span className="font-medium">
                            {new Date(issue.resolved_at).toLocaleDateString()}
                          </span>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Reports */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Recent Compliance Reports
          </CardTitle>
          <CardDescription>Generated compliance audit reports</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {recent_reports.map((report) => {
              const complianceRate = (report.compliant_records / report.total_records) * 100;
              const isCompliant = complianceRate >= 95;

              return (
                <Card key={report.id}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <CardTitle className="text-base">
                            {report.report_type.toUpperCase()} Compliance Report
                          </CardTitle>
                          {isCompliant ? (
                            <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100">
                              <CheckCircle2 className="h-3 w-3 mr-1" />
                              Compliant
                            </Badge>
                          ) : (
                            <Badge variant="destructive">
                              <AlertTriangle className="h-3 w-3 mr-1" />
                              Issues Found
                            </Badge>
                          )}
                        </div>
                        <CardDescription>
                          {new Date(report.period_start).toLocaleDateString()} -{' '}
                          {new Date(report.period_end).toLocaleDateString()}
                        </CardDescription>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => downloadReport(report)}
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Download
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div>
                        <div className="text-sm text-muted-foreground">Total Records</div>
                        <div className="text-2xl font-bold">{report.total_records}</div>
                      </div>
                      <div>
                        <div className="text-sm text-muted-foreground">Compliant</div>
                        <div className="text-2xl font-bold text-green-600">
                          {report.compliant_records}
                        </div>
                      </div>
                      <div>
                        <div className="text-sm text-muted-foreground">Non-Compliant</div>
                        <div className="text-2xl font-bold text-red-600">
                          {report.non_compliant_records}
                        </div>
                      </div>
                      <div>
                        <div className="text-sm text-muted-foreground">Pending</div>
                        <div className="text-2xl font-bold text-yellow-600">
                          {report.pending_records}
                        </div>
                      </div>
                    </div>

                    {/* Compliance Rate Progress Bar */}
                    <div className="mt-4">
                      <div className="flex items-center justify-between text-sm mb-2">
                        <span className="text-muted-foreground">Compliance Rate</span>
                        <span className="font-medium">{complianceRate.toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2 dark:bg-gray-700">
                        <div
                          className={cn(
                            'h-2 rounded-full transition-all',
                            isCompliant ? 'bg-green-600' : 'bg-red-600'
                          )}
                          style={{ width: `${complianceRate}%` }}
                        />
                      </div>
                    </div>

                    {/* Issues */}
                    {report.issues.length > 0 && (
                      <div className="mt-4">
                        <div className="text-sm font-medium mb-2">Issues Identified:</div>
                        <div className="space-y-2">
                          {report.issues.slice(0, 3).map((issue) => (
                            <div
                              key={issue.id}
                              className="flex items-center gap-2 text-sm p-2 bg-muted rounded"
                            >
                              <Badge className={getSeverityColor(issue.severity)}>
                                {issue.severity}
                              </Badge>
                              <span>{issue.issue_type}</span>
                              <span className="text-muted-foreground">
                                ({issue.affected_records} records)
                              </span>
                            </div>
                          ))}
                          {report.issues.length > 3 && (
                            <div className="text-sm text-muted-foreground">
                              +{report.issues.length - 3} more issues
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}

            {recent_reports.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                No compliance reports available
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Consent Records Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Consent Records</CardTitle>
          <CardDescription>COPPA and GDPR consent tracking</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-muted-foreground mb-2">Total Consent Records</div>
              <div className="text-3xl font-bold">{metrics.total_consent_records}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground mb-2">Active Consents</div>
              <div className="text-3xl font-bold text-green-600">
                {metrics.active_consent_records}
              </div>
            </div>
          </div>

          <div className="mt-4">
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="text-muted-foreground">Active Consent Rate</span>
              <span className="font-medium">
                {((metrics.active_consent_records / metrics.total_consent_records) * 100).toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2 dark:bg-gray-700">
              <div
                className="bg-green-600 h-2 rounded-full transition-all"
                style={{
                  width: `${(metrics.active_consent_records / metrics.total_consent_records) * 100}%`
                }}
              />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
