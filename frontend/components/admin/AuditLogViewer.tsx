'use client';

/**
 * Audit Log Viewer Component
 * Displays searchable and filterable audit logs for admin review
 */

import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  TableProvider,
  TableHeader,
  TableHeaderGroup,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  TableColumnHeader,
  type ColumnDef
} from '@/components/kibo-ui/table';
import { Download, Search, Filter, Calendar, ChevronLeft, ChevronRight, Activity, CheckCircle2, XCircle, TrendingUp } from 'lucide-react';
import type { AuditLogEntry, AuditLogFilters, AuditLogResponse } from '@/lib/types';
import { cn } from '@/lib/utils';

interface AuditLogViewerProps {
  initialData?: AuditLogEntry[];
  apiEndpoint?: string;
}

export function AuditLogViewer({ initialData = [], apiEndpoint = '/api/audit/logs' }: AuditLogViewerProps) {
  const [logs, setLogs] = useState<AuditLogEntry[]>(initialData);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [filters, setFilters] = useState<AuditLogFilters>({});
  const [searchQuery, setSearchQuery] = useState('');
  const [stats, setStats] = useState({
    totalEntries: 0,
    successRate: 0,
    failedActions: 0,
    recentActivity: 0
  });

  const pageSize = 100;

  // Fetch audit logs
  const fetchLogs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        limit: pageSize.toString(),
        offset: (page * pageSize).toString(),
        ...Object.fromEntries(
          Object.entries(filters).filter(([_, v]) => v !== undefined && v !== '')
        )
      });

      const response = await fetch(`${apiEndpoint}?${params}`);

      if (!response.ok) {
        // Gracefully handle missing or unauthorized endpoint
        console.warn(`Audit logs endpoint unavailable: ${response.status} ${response.statusText}`);
        setLogs([]);
        setTotal(0);
        setLoading(false);
        return;
      }

      const data: AuditLogResponse = await response.json();

      if (data.success) {
        setLogs(data.logs);
        setTotal(data.total);

        // Calculate stats
        const successCount = data.logs.filter((log: AuditLogEntry) => log.status === 'success').length;
        const failedCount = data.logs.filter((log: AuditLogEntry) => log.status === 'failure').length;
        const recentCount = data.logs.filter((log: AuditLogEntry) => {
          const logTime = new Date(log.timestamp).getTime();
          const dayAgo = Date.now() - (24 * 60 * 60 * 1000);
          return logTime >= dayAgo;
        }).length;

        setStats({
          totalEntries: data.total,
          successRate: data.total > 0 ? (successCount / data.total) * 100 : 0,
          failedActions: failedCount,
          recentActivity: recentCount
        });
      }
    } catch (error) {
      console.error('Failed to fetch audit logs:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialData.length === 0) {
      fetchLogs();
    }
  }, [page, filters]);

  // Filter logs by search query
  const filteredLogs = useMemo(() => {
    if (!searchQuery) return logs;

    const query = searchQuery.toLowerCase();
    return logs.filter(log =>
      log.user_email?.toLowerCase().includes(query) ||
      log.action.toLowerCase().includes(query) ||
      log.resource_type.toLowerCase().includes(query) ||
      log.resource_id?.toLowerCase().includes(query) ||
      log.ip_address?.toLowerCase().includes(query)
    );
  }, [logs, searchQuery]);

  // Define table columns
  const columns: ColumnDef<AuditLogEntry>[] = useMemo(() => [
    {
      accessorKey: 'timestamp',
      header: ({ column }) => <TableColumnHeader column={column} title="Timestamp" />,
      cell: ({ row }) => {
        const date = new Date(row.original.timestamp);
        const formattedDate = date.toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
          year: 'numeric'
        });
        const formattedTime = date.toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit'
        });

        return (
          <div className="flex flex-col">
            <span className="text-sm font-medium">{formattedDate}</span>
            <span className="text-xs text-muted-foreground font-mono">{formattedTime}</span>
          </div>
        );
      },
    },
    {
      accessorKey: 'user_email',
      header: ({ column }) => <TableColumnHeader column={column} title="User" />,
      cell: ({ row }) => (
        <span className="text-sm font-mono">
          {row.original.user_email || <span className="text-muted-foreground">System</span>}
        </span>
      ),
    },
    {
      accessorKey: 'action',
      header: ({ column }) => <TableColumnHeader column={column} title="Action" />,
      cell: ({ row }) => {
        const action = row.original.action;

        const getActionColor = () => {
          if (action.includes('create')) return 'bg-success/10 text-success-foreground border-success/30';
          if (action.includes('update')) return 'bg-primary/10 text-primary border-primary/30';
          if (action.includes('delete')) return 'bg-destructive/10 text-destructive-foreground border-destructive/30';
          return 'bg-muted text-muted-foreground';
        };

        return (
          <Badge variant="outline" className={getActionColor()}>
            {action}
          </Badge>
        );
      },
    },
    {
      accessorKey: 'resource_type',
      header: ({ column }) => <TableColumnHeader column={column} title="Resource Type" />,
      cell: ({ row }) => (
        <div className="text-sm font-medium">{row.original.resource_type}</div>
      ),
    },
    {
      accessorKey: 'resource_id',
      header: 'Resource ID',
      cell: ({ row }) => (
        <div className="text-sm text-muted-foreground font-mono">
          {row.original.resource_id || '-'}
        </div>
      ),
    },
    {
      accessorKey: 'ip_address',
      header: 'IP Address',
      cell: ({ row }) => (
        <div className="text-sm font-mono">{row.original.ip_address || '-'}</div>
      ),
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => {
        const status = row.original.status;
        const isSuccess = status === 'success';

        return (
          <div className="flex items-center gap-2">
            {isSuccess ? (
              <CheckCircle2 className="h-4 w-4 text-success" />
            ) : (
              <XCircle className="h-4 w-4 text-destructive" />
            )}
            <span className="text-sm capitalize">{status}</span>
          </div>
        );
      },
    },
    {
      accessorKey: 'details',
      header: 'Details',
      cell: ({ row }) => {
        const details = row.original.details;
        if (!details || Object.keys(details).length === 0) {
          return <span className="text-muted-foreground">-</span>;
        }

        return (
          <details className="text-xs">
            <summary className="cursor-pointer text-primary">View</summary>
            <pre className="mt-2 p-2 bg-muted rounded text-xs overflow-x-auto">
              {JSON.stringify(details, null, 2)}
            </pre>
          </details>
        );
      },
    },
  ], []);

  // Export to CSV
  const exportToCSV = () => {
    const headers = ['Timestamp', 'User', 'Action', 'Resource Type', 'Resource ID', 'IP Address', 'Status', 'Details'];
    const csvRows = [
      headers.join(','),
      ...filteredLogs.map(log => [
        log.timestamp,
        log.user_email || 'System',
        log.action,
        log.resource_type,
        log.resource_id || '',
        log.ip_address || '',
        log.status,
        log.details ? JSON.stringify(log.details).replace(/,/g, ';') : ''
      ].map(field => `"${field}"`).join(','))
    ].join('\n');

    const blob = new Blob([csvRows], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit-logs-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Entries</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold">{stats.totalEntries.toLocaleString()}</div>
            <p className="mt-1 text-xs text-muted-foreground">All time records</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Success Rate</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-success" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold">{stats.successRate.toFixed(1)}%</div>
            <p className="mt-1 text-xs text-muted-foreground">Successful operations</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Failed Actions</CardTitle>
            <XCircle className="h-4 w-4 text-destructive" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold">{stats.failedActions}</div>
            <p className="mt-1 text-xs text-muted-foreground">Requires attention</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Recent Activity</CardTitle>
            <TrendingUp className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold">{stats.recentActivity}</div>
            <p className="mt-1 text-xs text-muted-foreground">Last 24 hours</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Audit Logs</CardTitle>
              <CardDescription>
                {total.toLocaleString()} total entries
              </CardDescription>
            </div>
            <Button onClick={exportToCSV} variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export CSV
            </Button>
          </div>
        </CardHeader>
        <CardContent>
        {/* Search and Filters */}
        <div className="space-y-4 mb-6">
          {/* Search Bar */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search audit logs..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>

          {/* Filter Inputs */}

          <div className="grid grid-cols-1 md:grid-cols-4 gap-2">
            <Input
              placeholder="Filter by user email"
              value={filters.user_email || ''}
              onChange={(e) => setFilters({ ...filters, user_email: e.target.value })}
            />
            <Input
              placeholder="Filter by action"
              value={filters.action || ''}
              onChange={(e) => setFilters({ ...filters, action: e.target.value })}
            />
            <Input
              placeholder="Filter by resource type"
              value={filters.resource_type || ''}
              onChange={(e) => setFilters({ ...filters, resource_type: e.target.value })}
            />
            <Input
              placeholder="Filter by IP address"
              value={filters.ip_address || ''}
              onChange={(e) => setFilters({ ...filters, ip_address: e.target.value })}
            />
          </div>

          <div className="flex gap-2">
            <div className="flex items-center gap-2 flex-1">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              <Input
                type="date"
                placeholder="Start date"
                value={filters.start_date || ''}
                onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
              />
            </div>
            <div className="flex items-center gap-2 flex-1">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              <Input
                type="date"
                placeholder="End date"
                value={filters.end_date || ''}
                onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
              />
            </div>
            <Button
              variant="outline"
              onClick={() => {
                setFilters({});
                setSearchQuery('');
                setPage(0);
              }}
            >
              Clear Filters
            </Button>
          </div>
        </div>

        {/* Table */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-muted-foreground">Loading audit logs...</div>
          </div>
        ) : (
          <>
            <div className="rounded-md border">
              <TableProvider columns={columns} data={filteredLogs}>
                <TableHeader>
                  {({ headerGroup }) => (
                    <TableHeaderGroup headerGroup={headerGroup}>
                      {({ header }) => <TableHead header={header} />}
                    </TableHeaderGroup>
                  )}
                </TableHeader>
                <TableBody>
                  {({ row }) => (
                    <TableRow row={row}>
                      {({ cell }) => <TableCell cell={cell} />}
                    </TableRow>
                  )}
                </TableBody>
              </TableProvider>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between mt-4">
              <div className="text-sm text-muted-foreground">
                Showing {page * pageSize + 1} - {Math.min((page + 1) * pageSize, total)} of {total}
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(p => Math.max(0, p - 1))}
                  disabled={page === 0}
                >
                  <ChevronLeft className="h-4 w-4 mr-1" />
                  Previous
                </Button>
                <div className="flex items-center px-3 text-sm">
                  Page {page + 1} of {totalPages}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                  disabled={page >= totalPages - 1}
                >
                  Next
                  <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
    </div>
  );
}
