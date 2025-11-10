'use client';

/**
 * Admin Compliance Reports Page
 * Displays FERPA, COPPA, and GDPR compliance dashboards
 */

import React from 'react';
import { ComplianceReports } from '@/components/admin';
import { RequireRole } from '@/contexts/AuthContext';

export default function CompliancePage() {
  return (
    <RequireRole
      roles={['admin']}
      fallback={
        <div className="container mx-auto py-8">
          <div className="text-center">
            <h1 className="text-2xl font-bold mb-4">Access Denied</h1>
            <p className="text-muted-foreground">
              You do not have permission to view compliance reports. This page is only accessible to administrators.
            </p>
          </div>
        </div>
      }
    >
      <div className="container mx-auto py-8 space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Compliance Dashboard</h1>
          <p className="text-muted-foreground mt-2">
            Monitor FERPA, COPPA, and GDPR compliance across the platform
          </p>
        </div>

        <ComplianceReports />
      </div>
    </RequireRole>
  );
}
