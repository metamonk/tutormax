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
  FileCheck,
  AlertCircle
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

      if (!response.ok) {
        // Gracefully handle missing endpoint (feature not yet implemented)
        console.warn(`Compliance endpoint unavailable: ${response.status} ${response.statusText}`);
        setData(null);
        return;
      }

      const result = await response.json();
      if (result.success) {
        setData(result);
      }
    } catch (error) {
      console.warn('Compliance data fetch failed:', error);
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
        return 'bg-red-600 dark:bg-red-500 text-white hover:bg-red-700 dark:hover:bg-red-600';
      case 'high':
        return 'bg-orange-600 dark:bg-orange-500 text-white hover:bg-orange-700 dark:hover:bg-orange-600';
      case 'medium':
        return 'bg-amber-600 dark:bg-amber-500 text-white hover:bg-amber-700 dark:hover:bg-amber-600';
      case 'low':
        return 'bg-slate-500 dark:bg-slate-600 text-white hover:bg-slate-600 dark:hover:bg-slate-700';
    }
  };

  const getStatusColor = (status: ComplianceIssue['status']) => {
    switch (status) {
      case 'open':
        return 'bg-red-100 dark:bg-red-950 text-red-800 dark:text-red-300 border-red-300 dark:border-red-800';
      case 'in_progress':
        return 'bg-blue-100 dark:bg-blue-950 text-blue-800 dark:text-blue-300 border-blue-300 dark:border-blue-800';
      case 'resolved':
        return 'bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 border-emerald-300 dark:border-emerald-800';
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
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-muted-foreground">FERPA Compliance</p>
                <p className="mt-2 text-3xl font-bold text-emerald-600 dark:text-emerald-400">
                  {(metrics.ferpa_compliance_rate * 100).toFixed(1)}%
                </p>
                <p className="mt-1 text-xs text-muted-foreground">Student privacy data protected</p>
              </div>
              <div className="rounded-xl bg-emerald-100 dark:bg-emerald-900/30 p-3 text-emerald-600 dark:text-emerald-400">
                <Shield className="h-5 w-5" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-muted-foreground">COPPA Consent Rate</p>
                <p className="mt-2 text-3xl font-bold text-blue-600 dark:text-blue-400">
                  {(metrics.coppa_consent_rate * 100).toFixed(1)}%
                </p>
                <p className="mt-1 text-xs text-muted-foreground">Parental consent obtained</p>
              </div>
              <div className="rounded-xl bg-blue-100 dark:bg-blue-900/30 p-3 text-blue-600 dark:text-blue-400">
                <Users className="h-5 w-5" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-muted-foreground">GDPR Compliance</p>
                <p className="mt-2 text-3xl font-bold text-violet-600 dark:text-violet-400">
                  {(metrics.gdpr_compliance_rate * 100).toFixed(1)}%
                </p>
                <p className="mt-1 text-xs text-muted-foreground">EU data protection compliant</p>
              </div>
              <div className="rounded-xl bg-violet-100 dark:bg-violet-900/30 p-3 text-violet-600 dark:text-violet-400">
                <FileCheck className="h-5 w-5" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-muted-foreground">Pending Data Requests</p>
                <p className="mt-2 text-3xl font-bold text-amber-600 dark:text-amber-400">
                  {metrics.pending_data_requests}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">{metrics.total_data_requests} total requests</p>
              </div>
              <div className="rounded-xl bg-amber-100 dark:bg-amber-900/30 p-3 text-amber-600 dark:text-amber-400">
                <Clock className="h-5 w-5" />
              </div>
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
                <div
                  key={issue.id}
                  className="rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 p-4"
                >
                  <div className="mb-3 flex flex-wrap items-center gap-2">
                    <Badge className={getSeverityColor(issue.severity)}>
                      {issue.severity.toUpperCase()}
                    </Badge>
                    <Badge variant="outline" className={getStatusColor(issue.status)}>
                      {issue.status === 'in_progress' ? 'IN PROGRESS' : issue.status.toUpperCase()}
                    </Badge>
                    <span className="font-semibold text-slate-900 dark:text-slate-50">{issue.issue_type}</span>
                  </div>
                  <p className="mb-3 text-sm text-slate-700 dark:text-slate-300">{issue.description}</p>
                  <div className="flex flex-wrap items-center gap-4 text-xs text-slate-600 dark:text-slate-400">
                    <div className="flex items-center gap-1">
                      <AlertCircle className="h-3.5 w-3.5" />
                      <span>{issue.affected_records} affected records</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock className="h-3.5 w-3.5" />
                      <span>Detected: {new Date(issue.detected_at).toLocaleDateString()}</span>
                    </div>
                    {issue.resolved_at && (
                      <div className="flex items-center gap-1">
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        <span>Resolved: {new Date(issue.resolved_at).toLocaleDateString()}</span>
                      </div>
                    )}
                  </div>
                </div>
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
          <div className="space-y-6">
            {recent_reports.map((report) => {
              const complianceRate = (report.compliant_records / report.total_records) * 100;
              const isCompliant = complianceRate >= 95;

              const getReportTypeColor = () => {
                switch (report.report_type.toLowerCase()) {
                  case 'ferpa':
                    return 'bg-emerald-600 dark:bg-emerald-500 text-white';
                  case 'coppa':
                    return 'bg-blue-600 dark:bg-blue-500 text-white';
                  case 'gdpr':
                    return 'bg-violet-600 dark:bg-violet-500 text-white';
                  default:
                    return 'bg-slate-600 dark:bg-slate-500 text-white';
                }
              };

              return (
                <div
                  key={report.id}
                  className="rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 p-5"
                >
                  <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <Badge className={getReportTypeColor()}>
                        {report.report_type.toUpperCase()}
                      </Badge>
                      <Badge
                        variant="outline"
                        className={isCompliant
                          ? "bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 border-emerald-300 dark:border-emerald-800"
                          : "bg-amber-100 dark:bg-amber-950 text-amber-800 dark:text-amber-300 border-amber-300 dark:border-amber-800"
                        }
                      >
                        {isCompliant ? 'COMPLIANT' : 'ISSUES FOUND'}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm text-muted-foreground">
                        {new Date(report.period_start).toLocaleDateString()} - {new Date(report.period_end).toLocaleDateString()}
                      </span>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => downloadReport(report)}
                      >
                        <Download className="mr-2 h-4 w-4" />
                        Download
                      </Button>
                    </div>
                  </div>

                  {/* Stats Grid */}
                  <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
                    <div className="rounded-md bg-white dark:bg-slate-950 p-3 border border-slate-200 dark:border-slate-800">
                      <p className="text-xs text-muted-foreground">Total Records</p>
                      <p className="mt-1 text-lg font-semibold">{report.total_records.toLocaleString()}</p>
                    </div>
                    <div className="rounded-md bg-white dark:bg-slate-950 p-3 border border-slate-200 dark:border-slate-800">
                      <p className="text-xs text-muted-foreground">Compliant</p>
                      <p className="mt-1 text-lg font-semibold text-emerald-600 dark:text-emerald-400">
                        {report.compliant_records.toLocaleString()}
                      </p>
                    </div>
                    <div className="rounded-md bg-white dark:bg-slate-950 p-3 border border-slate-200 dark:border-slate-800">
                      <p className="text-xs text-muted-foreground">Non-Compliant</p>
                      <p className="mt-1 text-lg font-semibold text-red-600 dark:text-red-400">
                        {report.non_compliant_records.toLocaleString()}
                      </p>
                    </div>
                    <div className="rounded-md bg-white dark:bg-slate-950 p-3 border border-slate-200 dark:border-slate-800">
                      <p className="text-xs text-muted-foreground">Pending</p>
                      <p className="mt-1 text-lg font-semibold text-amber-600 dark:text-amber-400">
                        {report.pending_records.toLocaleString()}
                      </p>
                    </div>
                  </div>

                  {/* Compliance Rate Progress Bar */}
                  <div className="mb-4">
                    <div className="mb-2 flex items-center justify-between">
                      <span className="text-sm font-medium">Compliance Rate</span>
                      <span className="text-sm font-bold">{complianceRate.toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-slate-200 dark:bg-slate-800 rounded-full h-2.5">
                      <div
                        className={cn(
                          'h-2.5 rounded-full transition-all',
                          isCompliant ? 'bg-emerald-600 dark:bg-emerald-500' : 'bg-amber-600 dark:bg-amber-500'
                        )}
                        style={{ width: `${complianceRate}%` }}
                      />
                    </div>
                  </div>

                  {/* Top Issues */}
                  {report.issues.length > 0 && (
                    <div className="rounded-md bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900 p-3">
                      <p className="mb-2 text-xs font-semibold text-amber-900 dark:text-amber-200">Top Issues Found:</p>
                      <ul className="space-y-1">
                        {report.issues.slice(0, 3).map((issue) => (
                          <li key={issue.id} className="flex items-start gap-2 text-xs text-amber-800 dark:text-amber-300">
                            <span className="mt-0.5 h-1.5 w-1.5 rounded-full bg-amber-500 dark:bg-amber-400 flex-shrink-0" />
                            <span>{issue.issue_type} ({issue.affected_records} records)</span>
                          </li>
                        ))}
                        {report.issues.length > 3 && (
                          <li className="text-xs text-amber-700 dark:text-amber-400 ml-3.5">
                            +{report.issues.length - 3} more issues
                          </li>
                        )}
                      </ul>
                    </div>
                  )}
                </div>
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
          <CardTitle>Consent Records Summary</CardTitle>
          <CardDescription>COPPA parental consent tracking</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 p-4">
                <p className="text-sm text-muted-foreground">Total Consent Records</p>
                <p className="mt-2 text-3xl font-bold">
                  {metrics.total_consent_records.toLocaleString()}
                </p>
              </div>
              <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 p-4">
                <p className="text-sm text-muted-foreground">Active Consents</p>
                <p className="mt-2 text-3xl font-bold text-emerald-600 dark:text-emerald-400">
                  {metrics.active_consent_records.toLocaleString()}
                </p>
              </div>
            </div>
            <div>
              <div className="mb-2 flex items-center justify-between">
                <span className="text-sm font-medium">Active Consent Rate</span>
                <span className="text-sm font-bold">
                  {((metrics.active_consent_records / metrics.total_consent_records) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-slate-200 dark:bg-slate-800 rounded-full h-3">
                <div
                  className="bg-emerald-600 dark:bg-emerald-500 h-3 rounded-full transition-all"
                  style={{
                    width: `${(metrics.active_consent_records / metrics.total_consent_records) * 100}%`
                  }}
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
