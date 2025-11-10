'use client';

/**
 * Admin Data Retention Management Page
 *
 * Provides interface for:
 * - FERPA 7-year retention enforcement
 * - GDPR right to be forgotten
 * - Data anonymization for analytics
 * - Compliance reporting
 */

import React from 'react';
import { DataRetentionDashboard } from '@/components/admin/DataRetentionDashboard';
import { RequireRole } from '@/contexts/AuthContext';

export default function DataRetentionPage() {
  return (
    <RequireRole
      roles={['admin']}
      fallback={
        <div className="container mx-auto py-8">
          <div className="text-center">
            <h1 className="text-2xl font-bold mb-4">Access Denied</h1>
            <p className="text-muted-foreground">
              You do not have permission to view data retention management.
              This page is only accessible to administrators.
            </p>
          </div>
        </div>
      }
    >
      <div className="container mx-auto py-8 space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Data Retention Management</h1>
          <p className="text-muted-foreground mt-2">
            Manage FERPA retention, GDPR deletion requests, and data lifecycle automation
          </p>
        </div>

        <DataRetentionDashboard />
      </div>
    </RequireRole>
  );
}
