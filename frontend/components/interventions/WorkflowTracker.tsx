'use client';

/**
 * Workflow Tracker Component (Subtask 16.3)
 *
 * Visual workflow tracker showing intervention status progression:
 * pending → in_progress → completed
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2, Circle, Clock, XCircle } from 'lucide-react';
import type { Intervention, InterventionStatus } from '@/types/intervention';

interface WorkflowTrackerProps {
  intervention: Intervention;
  onUpdateStatus?: (status: InterventionStatus) => void;
  loading?: boolean;
}

interface WorkflowStep {
  status: InterventionStatus;
  label: string;
  icon: typeof Circle;
  description: string;
}

const WORKFLOW_STEPS: WorkflowStep[] = [
  {
    status: 'pending',
    label: 'Pending',
    icon: Circle,
    description: 'Intervention has been created and is waiting to be started',
  },
  {
    status: 'in_progress',
    label: 'In Progress',
    icon: Clock,
    description: 'Intervention is currently being worked on',
  },
  {
    status: 'completed',
    label: 'Completed',
    icon: CheckCircle2,
    description: 'Intervention has been completed',
  },
];

export function WorkflowTracker({ intervention, onUpdateStatus, loading = false }: WorkflowTrackerProps) {
  const currentStatus = intervention.status;
  const isCancelled = currentStatus === 'cancelled';

  // Get the index of the current status
  const currentStepIndex = WORKFLOW_STEPS.findIndex(
    (step) => step.status === currentStatus
  );

  const getStepState = (
    stepIndex: number
  ): 'completed' | 'active' | 'upcoming' | 'cancelled' => {
    if (isCancelled) return 'cancelled';
    if (stepIndex < currentStepIndex) return 'completed';
    if (stepIndex === currentStepIndex) return 'active';
    return 'upcoming';
  };

  const getStepColor = (state: 'completed' | 'active' | 'upcoming' | 'cancelled'): string => {
    switch (state) {
      case 'completed':
        return 'text-success bg-success/10';
      case 'active':
        return 'text-primary bg-primary/10';
      case 'cancelled':
        return 'text-destructive bg-destructive/10';
      case 'upcoming':
      default:
        return 'text-muted-foreground bg-muted';
    }
  };

  const getConnectorColor = (fromIndex: number): string => {
    if (isCancelled) return 'bg-destructive/20';
    if (fromIndex < currentStepIndex) return 'bg-success/30';
    return 'bg-border';
  };

  const canTransitionTo = (targetStatus: InterventionStatus): boolean => {
    if (isCancelled || loading) return false;

    // Define allowed transitions
    const transitions: Record<InterventionStatus, InterventionStatus[]> = {
      pending: ['in_progress', 'cancelled'],
      in_progress: ['completed', 'cancelled'],
      completed: [],
      cancelled: [],
    };

    return transitions[currentStatus]?.includes(targetStatus) || false;
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Workflow Status</CardTitle>
          {isCancelled && (
            <Badge variant="destructive" className="flex items-center gap-1">
              <XCircle className="h-3 w-3" />
              Cancelled
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Visual Workflow Steps */}
          <div className="relative">
            <div className="flex items-center justify-between">
              {WORKFLOW_STEPS.map((step, index) => {
                const state = getStepState(index);
                const StepIcon = step.icon;
                const isLast = index === WORKFLOW_STEPS.length - 1;

                return (
                  <React.Fragment key={step.status}>
                    {/* Step */}
                    <div className="flex flex-col items-center flex-1">
                      <div
                        className={`flex items-center justify-center w-12 h-12 rounded-full border-2 transition-all ${
                          state === 'active'
                            ? 'border-primary shadow-lg'
                            : state === 'completed'
                            ? 'border-success'
                            : state === 'cancelled'
                            ? 'border-destructive'
                            : 'border-border'
                        } ${getStepColor(state)}`}
                      >
                        {state === 'cancelled' ? (
                          <XCircle className="h-6 w-6" />
                        ) : (
                          <StepIcon className="h-6 w-6" />
                        )}
                      </div>
                      <div className="mt-2 text-center">
                        <div
                          className={`text-sm font-medium transition-colors ${
                            state === 'active'
                              ? 'text-primary'
                              : state === 'completed'
                              ? 'text-success'
                              : state === 'cancelled'
                              ? 'text-destructive'
                              : 'text-muted-foreground'
                          }`}
                        >
                          {step.label}
                        </div>
                        <div className="text-xs text-muted-foreground mt-1 max-w-[120px]">
                          {step.description}
                        </div>
                      </div>
                    </div>

                    {/* Connector */}
                    {!isLast && (
                      <div className="flex-1 h-1 mx-2 -mt-12">
                        <div className={`h-full rounded ${getConnectorColor(index)}`} />
                      </div>
                    )}
                  </React.Fragment>
                );
              })}
            </div>
          </div>

          {/* Action Buttons */}
          {!isCancelled && onUpdateStatus && (
            <div className="flex flex-wrap gap-2 pt-4 border-t">
              {currentStatus === 'pending' && (
                <>
                  <Button
                    onClick={() => onUpdateStatus('in_progress')}
                    disabled={!canTransitionTo('in_progress')}
                    loading={loading}
                  >
                    Start Working
                  </Button>
                  <Button
                    variant="destructive"
                    onClick={() => onUpdateStatus('cancelled')}
                    disabled={!canTransitionTo('cancelled')}
                    loading={loading}
                  >
                    Cancel
                  </Button>
                </>
              )}

              {currentStatus === 'in_progress' && (
                <>
                  <Button
                    onClick={() => onUpdateStatus('completed')}
                    disabled={!canTransitionTo('completed')}
                    loading={loading}
                  >
                    Mark as Complete
                  </Button>
                  <Button
                    variant="destructive"
                    onClick={() => onUpdateStatus('cancelled')}
                    disabled={!canTransitionTo('cancelled')}
                    loading={loading}
                  >
                    Cancel
                  </Button>
                </>
              )}
            </div>
          )}

          {/* Completion Information */}
          {intervention.completed_date && (
            <div className="bg-success/10 border border-success/20 rounded-lg p-4">
              <div className="flex items-start gap-2">
                <CheckCircle2 className="h-5 w-5 text-success mt-0.5" />
                <div>
                  <div className="text-sm font-medium text-success">
                    Completed on {new Date(intervention.completed_date).toLocaleDateString()}
                  </div>
                  {intervention.outcome && (
                    <div className="text-sm text-success/80 mt-1">
                      Outcome: {intervention.outcome.replace('_', ' ')}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Cancellation Information */}
          {isCancelled && (
            <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
              <div className="flex items-start gap-2">
                <XCircle className="h-5 w-5 text-destructive mt-0.5" />
                <div>
                  <div className="text-sm font-medium text-destructive">
                    This intervention was cancelled
                  </div>
                  {intervention.notes && (
                    <div className="text-sm text-destructive/80 mt-1">{intervention.notes}</div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
