'use client';

/**
 * Admin Training Management Page
 * Displays training module kanban board for assignment and tracking
 */

import React from 'react';
import { RecommendedTraining } from '@/components/admin';
import { RequireRole } from '@/contexts/AuthContext';
import { toast } from 'sonner';
import type { TrainingModule } from '@/lib/types';

export default function TrainingPage() {
  const handleModuleUpdate = (module: TrainingModule) => {
    // Handle module status update
    toast.success(`Training module "${module.title}" updated to ${module.status.replace('_', ' ')}`);

    // Here you would typically make an API call to persist the change
    // Example:
    // await fetch(`/api/admin/training/${module.id}`, {
    //   method: 'PATCH',
    //   body: JSON.stringify({ status: module.status })
    // });
  };

  return (
    <RequireRole
      roles={['admin', 'people_ops']}
      fallback={
        <div className="container mx-auto py-8">
          <div className="text-center">
            <h1 className="text-2xl font-bold mb-4">Access Denied</h1>
            <p className="text-muted-foreground">
              You do not have permission to view training management. This page is only accessible to administrators and people operations.
            </p>
          </div>
        </div>
      }
    >
      <div className="container mx-auto py-8 space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Training Module Management</h1>
          <p className="text-muted-foreground mt-2">
            Assign and track training modules to improve tutor performance
          </p>
        </div>

        <RecommendedTraining onModuleUpdate={handleModuleUpdate} />
      </div>
    </RequireRole>
  );
}
