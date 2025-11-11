'use client';

/**
 * Data Retention & Compliance Management Dashboard
 *
 * Main admin interface for:
 * - Scanning for eligible archival records
 * - Archiving data (FERPA 7-year retention)
 * - Anonymizing data for analytics
 * - Processing GDPR deletion requests
 * - Viewing compliance reports
 */

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import type {
  RetentionScanResult,
  RetentionPolicy,
  RetentionReport
} from '@/lib/types';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Database,
  Archive,
  UserX,
  FileBarChart,
  ShieldCheck,
  AlertTriangle,
  Clock
} from 'lucide-react';
import { toast } from 'sonner';

export function DataRetentionDashboard() {
  const [loading, setLoading] = useState(false);
  const [policy, setPolicy] = useState<RetentionPolicy | null>(null);
  const [scanResults, setScanResults] = useState<RetentionScanResult | null>(null);
  const [report, setReport] = useState<RetentionReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadPolicy();
  }, []);

  const loadPolicy = async () => {
    try {
      const policyData = await apiClient.getRetentionPolicy();
      setPolicy(policyData);
    } catch (err) {
      console.error('Failed to load retention policy:', err);
      toast.error('Failed to load retention policy');
    }
  };

  const handleQuickScan = async () => {
    try {
      setLoading(true);
      setError(null);
      const results = await apiClient.scanRetention(true); // dry run
      setScanResults(results);
      toast.success('Scan completed successfully');
    } catch (err) {
      setError('Failed to scan for eligible records');
      toast.error('Scan failed');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateReport = async () => {
    try {
      setLoading(true);
      setError(null);
      const reportData = await apiClient.getRetentionReport();
      setReport(reportData);
      toast.success('Report generated successfully');
    } catch (err) {
      setError('Failed to generate report');
      toast.error('Report generation failed');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Overview Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-muted-foreground">FERPA Retention</p>
                <p className="mt-2 text-2xl font-bold">7 Years</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {policy?.ferpa.retention_period_days} days retention period
                </p>
              </div>
              <div className="rounded-xl bg-blue-100 dark:bg-blue-900/30 p-3 text-blue-600 dark:text-blue-400">
                <Clock className="h-4 w-4" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-muted-foreground">Eligible for Archival</p>
                <p className="mt-2 text-2xl font-bold text-amber-600 dark:text-amber-400">
                  {scanResults?.summary.total_students_for_archival || 0}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Students past retention period
                </p>
              </div>
              <div className="rounded-xl bg-amber-100 dark:bg-amber-900/30 p-3 text-amber-600 dark:text-amber-400">
                <Archive className="h-4 w-4" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-muted-foreground">GDPR Compliance</p>
                <p className="mt-2 text-2xl font-bold text-emerald-600 dark:text-emerald-400">Active</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Right to be forgotten enabled
                </p>
              </div>
              <div className="rounded-xl bg-emerald-100 dark:bg-emerald-900/30 p-3 text-emerald-600 dark:text-emerald-400">
                <ShieldCheck className="h-4 w-4" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-muted-foreground">Recent Actions</p>
                <p className="mt-2 text-2xl font-bold text-violet-600 dark:text-violet-400">
                  {report?.retention_actions_taken.archival_operations || 0}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Archival operations this period
                </p>
              </div>
              <div className="rounded-xl bg-violet-100 dark:bg-violet-900/30 p-3 text-violet-600 dark:text-violet-400">
                <Database className="h-4 w-4" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>
            Common data retention management tasks
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <Button
              onClick={handleQuickScan}
              disabled={loading}
              variant="outline"
            >
              <Database className="mr-2 h-4 w-4" />
              Run Scan
            </Button>
            <Button
              onClick={handleGenerateReport}
              disabled={loading}
              variant="outline"
            >
              <FileBarChart className="mr-2 h-4 w-4" />
              Generate Report
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Main Tabs */}
      <Tabs defaultValue="scan" className="space-y-4">
        <TabsList>
          <TabsTrigger value="scan">Scan & Archive</TabsTrigger>
          <TabsTrigger value="gdpr">GDPR Deletion</TabsTrigger>
          <TabsTrigger value="reports">Reports</TabsTrigger>
          <TabsTrigger value="policy">Policy</TabsTrigger>
        </TabsList>

        <TabsContent value="scan" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Retention Scan Results</CardTitle>
              <CardDescription>
                Records eligible for archival or anonymization
              </CardDescription>
            </CardHeader>
            <CardContent>
              {scanResults ? (
                <div className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-3">
                    <div className="rounded-lg border p-4">
                      <div className="text-sm font-medium text-muted-foreground">Students</div>
                      <div className="text-2xl font-bold">
                        {scanResults.summary.total_students_for_archival}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Eligible for archival
                      </div>
                    </div>
                    <div className="rounded-lg border p-4">
                      <div className="text-sm font-medium text-muted-foreground">Sessions</div>
                      <div className="text-2xl font-bold">
                        {scanResults.summary.total_sessions_for_archival}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Past retention period
                      </div>
                    </div>
                    <div className="rounded-lg border p-4">
                      <div className="text-sm font-medium text-muted-foreground">Audit Logs</div>
                      <div className="text-2xl font-bold">
                        {scanResults.summary.total_audit_logs_for_archival}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Ready for archival
                      </div>
                    </div>
                  </div>

                  {scanResults.eligible_for_archival.students.length > 0 && (
                    <div>
                      <h3 className="text-sm font-semibold mb-2">Eligible Students (Preview)</h3>
                      <div className="space-y-2">
                        {scanResults.eligible_for_archival.students.slice(0, 5).map((student) => (
                          <div key={student.student_id} className="flex items-center justify-between rounded-lg border p-3">
                            <div>
                              <div className="font-medium">{student.name}</div>
                              <div className="text-sm text-muted-foreground">
                                ID: {student.student_id} • Last activity: {new Date(student.last_activity).toLocaleDateString()}
                              </div>
                            </div>
                            <Badge variant="secondary">
                              {student.days_since_activity} days ago
                            </Badge>
                          </div>
                        ))}
                        {scanResults.eligible_for_archival.students.length > 5 && (
                          <p className="text-sm text-muted-foreground">
                            ...and {scanResults.eligible_for_archival.students.length - 5} more
                          </p>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <Database className="mx-auto h-12 w-12 mb-4 opacity-50" />
                  <p>No scan results yet. Click "Run Scan" to start.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="gdpr" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>GDPR Data Deletion</CardTitle>
              <CardDescription>
                Process user requests for data deletion (Right to be Forgotten)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  GDPR deletion requests are permanent and cannot be undone.
                  All user data will be removed while maintaining anonymized audit logs for compliance.
                </AlertDescription>
              </Alert>
              <div className="mt-4 text-sm text-muted-foreground">
                Use the GDPR Deletion tab to process deletion requests.
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="reports" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Compliance Report</CardTitle>
              <CardDescription>
                Data retention and deletion activity summary
              </CardDescription>
            </CardHeader>
            <CardContent>
              {report ? (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-sm font-semibold mb-3">Current Data Inventory</h3>
                    <div className="grid gap-4 md:grid-cols-3">
                      <div className="rounded-lg border p-4">
                        <div className="text-sm font-medium text-muted-foreground">Active Students</div>
                        <div className="text-2xl font-bold">
                          {report.current_data_inventory.active_students}
                        </div>
                      </div>
                      <div className="rounded-lg border p-4">
                        <div className="text-sm font-medium text-muted-foreground">Active Tutors</div>
                        <div className="text-2xl font-bold">
                          {report.current_data_inventory.active_tutors}
                        </div>
                      </div>
                      <div className="rounded-lg border p-4">
                        <div className="text-sm font-medium text-muted-foreground">Total Sessions</div>
                        <div className="text-2xl font-bold">
                          {report.current_data_inventory.total_sessions}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-sm font-semibold mb-3">Retention Actions Taken</h3>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between rounded-lg border p-3">
                        <span className="text-sm">Archival Operations</span>
                        <Badge>{report.retention_actions_taken.archival_operations}</Badge>
                      </div>
                      <div className="flex items-center justify-between rounded-lg border p-3">
                        <span className="text-sm">Anonymization Operations</span>
                        <Badge>{report.retention_actions_taken.anonymization_operations}</Badge>
                      </div>
                      <div className="flex items-center justify-between rounded-lg border p-3">
                        <span className="text-sm">Deletion Requests Processed</span>
                        <Badge>{report.retention_actions_taken.deletion_requests_processed}</Badge>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-sm font-semibold mb-3">Compliance Status</h3>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between rounded-lg border p-3">
                        <span className="text-sm">FERPA Retention Policy</span>
                        <Badge variant="secondary">{report.compliance_status.ferpa_retention_policy}</Badge>
                      </div>
                      <div className="flex items-center justify-between rounded-lg border p-3">
                        <span className="text-sm">GDPR Anonymization Threshold</span>
                        <Badge variant="secondary">{report.compliance_status.gdpr_anonymization_eligible_after}</Badge>
                      </div>
                      <div className="flex items-center justify-between rounded-lg border p-3">
                        <span className="text-sm">Audit Log Retention</span>
                        <Badge variant="secondary">{report.compliance_status.audit_log_retention}</Badge>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <FileBarChart className="mx-auto h-12 w-12 mb-4 opacity-50" />
                  <p>No report generated yet. Click "Generate Report" to start.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="policy" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Data Retention Policy</CardTitle>
              <CardDescription>
                Current retention and compliance policies
              </CardDescription>
            </CardHeader>
            <CardContent>
              {policy && (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-sm font-semibold mb-3">FERPA (Educational Records)</h3>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between rounded-lg border p-3">
                        <span className="text-sm">Retention Period</span>
                        <Badge variant="secondary">{policy.ferpa.retention_period_years} years</Badge>
                      </div>
                      <div className="flex items-center justify-between rounded-lg border p-3">
                        <span className="text-sm">Retention Days</span>
                        <Badge variant="secondary">{policy.ferpa.retention_period_days} days</Badge>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-sm font-semibold mb-3">GDPR (User Rights)</h3>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between rounded-lg border p-3">
                        <span className="text-sm">Right to Erasure</span>
                        <Badge variant="secondary">{policy.gdpr.right_to_erasure}</Badge>
                      </div>
                      <div className="flex items-center justify-between rounded-lg border p-3">
                        <span className="text-sm">Anonymization After</span>
                        <Badge variant="secondary">{policy.gdpr.anonymization_after_days} days</Badge>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-sm font-semibold mb-3">Automated Archival</h3>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between rounded-lg border p-3">
                        <span className="text-sm">Status</span>
                        <Badge variant={policy.automated_archival.enabled ? "default" : "secondary"}>
                          {policy.automated_archival.enabled ? "Enabled" : "Disabled"}
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between rounded-lg border p-3">
                        <span className="text-sm">Grace Period</span>
                        <Badge variant="secondary">{policy.automated_archival.grace_period_days} days</Badge>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
