/**
 * TypeScript types for Intervention Management
 */

export type InterventionType =
  | 'automated_coaching'
  | 'training_module'
  | 'first_session_checkin'
  | 'rescheduling_alert'
  | 'manager_coaching'
  | 'peer_mentoring'
  | 'performance_improvement_plan'
  | 'retention_interview'
  | 'recognition';

export type InterventionStatus =
  | 'pending'
  | 'in_progress'
  | 'completed'
  | 'cancelled';

export type InterventionOutcome =
  | 'improved'
  | 'no_change'
  | 'declined'
  | 'churned';

export interface Intervention {
  intervention_id: string;
  tutor_id: string;
  tutor_name?: string;
  intervention_type: InterventionType;
  trigger_reason?: string;
  recommended_date: string;
  assigned_to?: string;
  status: InterventionStatus;
  due_date?: string;
  completed_date?: string;
  outcome?: InterventionOutcome;
  notes?: string;
  created_at: string;
  updated_at: string;

  // Computed fields
  days_until_due?: number;
  is_overdue: boolean;
  sla_percentage?: number;
}

export interface InterventionStats {
  total: number;
  pending: number;
  in_progress: number;
  completed: number;
  cancelled: number;
  overdue: number;
  due_today: number;
  due_this_week: number;
  by_type: Record<InterventionType, number>;
}

export interface AssignInterventionRequest {
  assigned_to: string;
}

export interface UpdateStatusRequest {
  status: InterventionStatus;
}

export interface RecordOutcomeRequest {
  outcome: InterventionOutcome;
  notes?: string;
}

// Helper function to format intervention type for display
export const formatInterventionType = (type: InterventionType): string => {
  const typeMap: Record<InterventionType, string> = {
    automated_coaching: 'Automated Coaching',
    training_module: 'Training Module',
    first_session_checkin: 'First Session Check-in',
    rescheduling_alert: 'Rescheduling Alert',
    manager_coaching: 'Manager Coaching',
    peer_mentoring: 'Peer Mentoring',
    performance_improvement_plan: 'Performance Improvement Plan',
    retention_interview: 'Retention Interview',
    recognition: 'Recognition',
  };
  return typeMap[type] || type;
};

// Helper function to get intervention type badge color
export const getInterventionTypeBadgeColor = (type: InterventionType): string => {
  const colorMap: Record<InterventionType, string> = {
    automated_coaching: 'bg-blue-100 text-blue-800',
    training_module: 'bg-purple-100 text-purple-800',
    first_session_checkin: 'bg-cyan-100 text-cyan-800',
    rescheduling_alert: 'bg-yellow-100 text-yellow-800',
    manager_coaching: 'bg-orange-100 text-orange-800',
    peer_mentoring: 'bg-green-100 text-green-800',
    performance_improvement_plan: 'bg-red-100 text-red-800',
    retention_interview: 'bg-pink-100 text-pink-800',
    recognition: 'bg-emerald-100 text-emerald-800',
  };
  return colorMap[type] || 'bg-gray-100 text-gray-800';
};

// Helper function to get status badge variant
export const getStatusBadgeVariant = (status: InterventionStatus): 'default' | 'secondary' | 'destructive' | 'outline' => {
  const variantMap: Record<InterventionStatus, 'default' | 'secondary' | 'destructive' | 'outline'> = {
    pending: 'outline',
    in_progress: 'default',
    completed: 'secondary',
    cancelled: 'destructive',
  };
  return variantMap[status] || 'default';
};
