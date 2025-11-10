'use client';

/**
 * Admin Audit Logs Page
 * Displays searchable audit log viewer for administrators
 */

import React from 'react';
import { AuditLogViewer } from '@/components/admin';
import { RequireRole } from '@/contexts/AuthContext';

export default function AuditLogsPage() {
  return (
    <RequireRole
      roles={['admin']}
      fallback={
        <div className="container mx-auto py-8">
          <div className="text-center">
            <h1 className="text-2xl font-bold mb-4">Access Denied</h1>
            <p className="text-muted-foreground">
              You do not have permission to view audit logs. This page is only accessible to administrators.
            </p>
          </div>
        </div>
      }
    >
      <div className="container mx-auto py-8 space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Audit Logs</h1>
          <p className="text-muted-foreground mt-2">
            View and search system audit logs for security and compliance monitoring
          </p>
        </div>

        <AuditLogViewer />
      </div>
    </RequireRole>
  );
}
