'use client';

/**
 * Intervention Detail Page
 *
 * Detailed view of a single intervention with workflow tracking,
 * SLA timer, and outcome recording capabilities.
 */

import React from 'react';
import { useParams, useRouter } from 'next/navigation';
import { WorkflowTracker } from '@/components/interventions/WorkflowTracker';
import { SLATimer } from '@/components/interventions/SLATimer';
import { OutcomeRecordingDialog } from '@/components/interventions/OutcomeRecordingDialog';
import { AssignInterventionDialog } from '@/components/interventions/AssignInterventionDialog';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  ArrowLeft,
  User,
  Calendar,
  FileText,
  Edit,
  UserPlus,
} from 'lucide-react';
import { InterventionAPI } from '@/lib/api/interventions';
import type { Intervention, InterventionStatus, InterventionOutcome } from '@/types/intervention';
import { formatInterventionType, getInterventionTypeBadgeColor } from '@/types/intervention';
import { toast } from 'sonner';
import { format, parseISO } from 'date-fns';

export default function InterventionDetailPage() {
  const params = useParams();
  const router = useRouter();
  const interventionId = params.id as string;

  const [intervention, setIntervention] = React.useState<Intervention | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [outcomeDialogOpen, setOutcomeDialogOpen] = React.useState(false);
  const [assignDialogOpen, setAssignDialogOpen] = React.useState(false);

  // Fetch intervention
  const fetchIntervention = React.useCallback(async () => {
    setLoading(true);
    try {
      const data = await InterventionAPI.getIntervention(interventionId);
      setIntervention(data);
    } catch (error) {
      console.error('Failed to fetch intervention:', error);
      toast.error('Failed to load intervention');
    } finally {
      setLoading(false);
    }
  }, [interventionId]);

  React.useEffect(() => {
    fetchIntervention();
  }, [fetchIntervention]);

  // Handle status update
  const handleUpdateStatus = async (status: InterventionStatus) => {
    if (!intervention) return;

    try {
      await InterventionAPI.updateStatus(intervention.intervention_id, { status });
      toast.success('Status updated successfully');
      fetchIntervention();
    } catch (error) {
      console.error('Failed to update status:', error);
      toast.error('Failed to update status');
    }
  };

  // Handle outcome recording
  const handleRecordOutcome = async (
    interventionId: string,
    outcome: InterventionOutcome,
    notes?: string
  ) => {
    try {
      await InterventionAPI.recordOutcome(interventionId, { outcome, notes });
      toast.success('Outcome recorded successfully');
      fetchIntervention();
    } catch (error) {
      console.error('Failed to record outcome:', error);
      toast.error('Failed to record outcome');
      throw error;
    }
  };

  // Handle assignment
  const handleAssign = async (interventionId: string, assignedTo: string) => {
    try {
      await InterventionAPI.assignIntervention(interventionId, { assigned_to: assignedTo });
      toast.success('Intervention assigned successfully');
      fetchIntervention();
    } catch (error) {
      console.error('Failed to assign intervention:', error);
      toast.error('Failed to assign intervention');
      throw error;
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
        </div>
      </div>
    );
  }

  if (!intervention) {
    return (
      <div className="container mx-auto p-6">
        <Card>
          <CardContent className="p-12 text-center">
            <p className="text-muted-foreground">Intervention not found</p>
            <Button className="mt-4" onClick={() => router.push('/interventions')}>
              Back to Interventions
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.push('/interventions')}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold">Intervention Details</h1>
            <p className="text-muted-foreground">ID: {intervention.intervention_id}</p>
          </div>
        </div>
        <div className="flex gap-2">
          {intervention.status !== 'completed' && intervention.status !== 'cancelled' && (
            <Button
              variant="outline"
              onClick={() => setOutcomeDialogOpen(true)}
            >
              <Edit className="h-4 w-4 mr-2" />
              Record Outcome
            </Button>
          )}
          {!intervention.assigned_to && (
            <Button onClick={() => setAssignDialogOpen(true)}>
              <UserPlus className="h-4 w-4 mr-2" />
              Assign
            </Button>
          )}
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column - Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Intervention Information */}
          <Card>
            <CardHeader>
              <CardTitle>Intervention Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Tutor */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <User className="h-4 w-4" />
                  <span className="text-sm font-medium">Tutor</span>
                </div>
                <div className="text-right">
                  <div className="font-medium">{intervention.tutor_name || 'Unknown'}</div>
                  <div className="text-sm text-muted-foreground">{intervention.tutor_id}</div>
                </div>
              </div>

              <Separator />

              {/* Type */}
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Intervention Type</span>
                <Badge
                  variant="outline"
                  className={getInterventionTypeBadgeColor(intervention.intervention_type)}
                >
                  {formatInterventionType(intervention.intervention_type)}
                </Badge>
              </div>

              <Separator />

              {/* Assigned To */}
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Assigned To</span>
                <div className="flex items-center gap-2">
                  {intervention.assigned_to ? (
                    <>
                      <User className="h-4 w-4 text-muted-foreground" />
                      <span>{intervention.assigned_to}</span>
                    </>
                  ) : (
                    <span className="text-muted-foreground">Unassigned</span>
                  )}
                </div>
              </div>

              <Separator />

              {/* Dates */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Created</span>
                  <div className="flex items-center gap-2 text-sm">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    {format(parseISO(intervention.created_at), 'MMM d, yyyy h:mm a')}
                  </div>
                </div>

                {intervention.due_date && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Due Date</span>
                    <div className="flex items-center gap-2 text-sm">
                      <Calendar className="h-4 w-4 text-muted-foreground" />
                      {format(parseISO(intervention.due_date), 'MMM d, yyyy h:mm a')}
                    </div>
                  </div>
                )}

                {intervention.completed_date && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Completed</span>
                    <div className="flex items-center gap-2 text-sm">
                      <Calendar className="h-4 w-4 text-muted-foreground" />
                      {format(parseISO(intervention.completed_date), 'MMM d, yyyy h:mm a')}
                    </div>
                  </div>
                )}
              </div>

              {/* Trigger Reason */}
              {intervention.trigger_reason && (
                <>
                  <Separator />
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <FileText className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm font-medium">Trigger Reason</span>
                    </div>
                    <p className="text-sm text-muted-foreground bg-muted p-3 rounded-lg">
                      {intervention.trigger_reason}
                    </p>
                  </div>
                </>
              )}

              {/* Notes */}
              {intervention.notes && (
                <>
                  <Separator />
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <FileText className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm font-medium">Notes</span>
                    </div>
                    <p className="text-sm text-muted-foreground bg-muted p-3 rounded-lg whitespace-pre-wrap">
                      {intervention.notes}
                    </p>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {/* Workflow Tracker */}
          <WorkflowTracker
            intervention={intervention}
            onUpdateStatus={handleUpdateStatus}
          />
        </div>

        {/* Right Column - SLA & Actions */}
        <div className="space-y-6">
          {/* SLA Timer */}
          <SLATimer intervention={intervention} showAlert />

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => router.push(`/tutor/${intervention.tutor_id}`)}
              >
                <User className="h-4 w-4 mr-2" />
                View Tutor Profile
              </Button>

              {intervention.status !== 'completed' && intervention.status !== 'cancelled' && (
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => setOutcomeDialogOpen(true)}
                >
                  <Edit className="h-4 w-4 mr-2" />
                  Record Outcome
                </Button>
              )}

              {!intervention.assigned_to && (
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => setAssignDialogOpen(true)}
                >
                  <UserPlus className="h-4 w-4 mr-2" />
                  Assign Intervention
                </Button>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Dialogs */}
      <OutcomeRecordingDialog
        open={outcomeDialogOpen}
        onOpenChange={setOutcomeDialogOpen}
        intervention={intervention}
        onRecordOutcome={handleRecordOutcome}
      />

      <AssignInterventionDialog
        open={assignDialogOpen}
        onOpenChange={setAssignDialogOpen}
        intervention={intervention}
        onAssign={handleAssign}
      />
    </div>
  );
}
