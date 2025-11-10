/**
 * TypeScript type definitions for TutorMax Dashboard
 */

export interface TutorMetrics {
  tutor_id: string;
  tutor_name: string;
  window: '7day' | '30day' | '90day';
  calculation_date: string;
  sessions_completed: number;
  avg_rating: number;
  first_session_success_rate: number;
  reschedule_rate: number;
  no_show_count: number;
  engagement_score: number;
  learning_objectives_met_pct: number;
  performance_tier: 'Needs Support' | 'Developing' | 'Strong' | 'Exemplary';
}

export interface Alert {
  id: string;
  tutor_id: string;
  tutor_name: string;
  alert_type: 'critical' | 'warning' | 'info';
  severity: 'high' | 'medium' | 'low';
  title: string;
  message: string;
  timestamp: string;
  resolved: boolean;
  metrics?: Partial<TutorMetrics>;
}

export interface InterventionTask {
  id: string;
  tutor_id: string;
  tutor_name: string;
  task_type: 'coaching' | 'training' | 'review' | 'followup';
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  status: 'pending' | 'in_progress' | 'completed';
  created_at: string;
  due_date: string;
  assigned_to?: string;
}

export interface PerformanceAnalytics {
  total_tutors: number;
  active_tutors: number;
  performance_distribution: {
    'Needs Support': number;
    'Developing': number;
    'Strong': number;
    'Exemplary': number;
  };
  avg_rating: number;
  avg_engagement_score: number;
  total_sessions_7day: number;
  total_sessions_30day: number;
  alerts_count: {
    critical: number;
    warning: number;
    info: number;
  };
}

export interface WebSocketMessage {
  type: 'metrics_update' | 'alert' | 'intervention' | 'analytics_update';
  data: TutorMetrics | Alert | InterventionTask | PerformanceAnalytics;
  timestamp: string;
}

export interface DashboardState {
  tutorMetrics: TutorMetrics[];
  alerts: Alert[];
  interventionTasks: InterventionTask[];
  analytics: PerformanceAnalytics | null;
  connected: boolean;
  lastUpdate: string | null;
}

// Tutor Portal Types
export interface TutorProfile {
  tutor_id: string;
  name: string;
  email: string;
  onboarding_date: string;
  status: string;
  subjects: string[];
  education_level?: string;
  location?: string;
}

export interface TutorPerformanceData {
  success: boolean;
  tutor_id: string;
  tutor_name: string;
  window: '7day' | '30day' | '90day';
  calculation_date?: string;
  message?: string;
  metrics?: {
    performance_tier: 'Exemplary' | 'Strong' | 'Developing' | 'Needs Attention' | 'At Risk' | null;
    sessions_completed: number;
    avg_rating: number | null;
    first_session_success_rate: number | null;
    reschedule_rate: number | null;
    no_show_count: number;
    engagement_score: number | null;
    learning_objectives_met_pct: number | null;
    response_time_avg_minutes: number | null;
  } | null;
  timestamp: string;
}

export interface TutorSession {
  session_id: string;
  student_id: string;
  session_number: number;
  scheduled_start: string;
  actual_start: string | null;
  duration_minutes: number;
  subject: string;
  session_type: '1-on-1' | 'group';
  engagement_score: number | null;
  learning_objectives_met: boolean | null;
  no_show: boolean;
  rating: number | null;
  feedback_text: string | null;
  would_recommend: boolean | null;
}

export interface TutorSessionsResponse {
  success: boolean;
  tutor_id: string;
  sessions: TutorSession[];
  pagination: {
    total: number;
    limit: number;
    offset: number;
    has_more: boolean;
  };
  timestamp: string;
}

export interface TrainingRecommendation {
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low' | 'assigned';
  category: string;
  estimated_time?: string;
  status?: string;
  assigned_date?: string;
  due_date?: string;
}

export interface TutorRecommendationsResponse {
  success: boolean;
  tutor_id: string;
  tutor_name: string;
  performance_tier: string | null;
  recommendations: TrainingRecommendation[];
  growth_areas: string[];
  message: string;
  timestamp: string;
}

// Tutor Profile Detail Types

export interface ChurnPredictionWindow {
  window: string;
  churn_score: number;
  risk_level: string;
  prediction_date: string;
}

export interface TutorProfilePerformanceMetrics {
  performance_tier: string;
  sessions_completed: number;
  avg_rating: number | null;
  first_session_success_rate: number | null;
  reschedule_rate: number | null;
  no_show_count: number;
  engagement_score: number | null;
  learning_objectives_met_pct: number | null;
  window: string;
}

export interface ActiveFlag {
  flag_type: string;
  severity: string;
  description: string;
  detected_date: string;
  metric_value?: number;
}

export interface InterventionHistoryItem {
  intervention_id: string;
  intervention_type: string;
  trigger_reason: string | null;
  status: string;
  recommended_date: string;
  due_date: string | null;
  completed_date: string | null;
  outcome: string | null;
  assigned_to: string | null;
  notes: string | null;
}

export interface ManagerNoteItem {
  note_id: string;
  author_name: string;
  note_text: string;
  is_important: boolean;
  created_at: string;
  updated_at: string;
}

export interface TutorBasicInfo {
  tutor_id: string;
  name: string;
  email: string;
  onboarding_date: string;
  status: string;
  subjects: string[];
  education_level: string | null;
  location: string | null;
  tenure_days: number;
}

export interface RecentFeedback {
  session_id: string;
  student_id: string;
  session_date: string;
  rating: number | null;
  feedback_text: string | null;
  would_recommend: boolean | null;
  subject: string;
}

export interface TutorProfileResponse {
  success: boolean;
  tutor_info: TutorBasicInfo;
  churn_predictions: ChurnPredictionWindow[];
  performance_metrics: TutorProfilePerformanceMetrics;
  active_flags: ActiveFlag[];
  intervention_history: InterventionHistoryItem[];
  manager_notes: ManagerNoteItem[];
  recent_feedback: RecentFeedback[];
  timestamp: string;
}

// Authentication & RBAC Types

export type UserRole = 'admin' | 'operations_manager' | 'people_ops' | 'tutor' | 'student';

export interface User {
  id: number;
  email: string;
  full_name?: string;
  roles: UserRole[];
  is_active: boolean;
  is_superuser: boolean;
  is_verified: boolean;
  oauth_provider?: string;
  tutor_id?: string;
  student_id?: string;
  created_at?: string;
  updated_at?: string;
}

export interface LoginRequest {
  username: string;  // email
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string;
  roles?: UserRole[];
}

export interface UserUpdateRequest {
  email?: string;
  full_name?: string;
  roles?: UserRole[];
  is_active?: boolean;
  password?: string;
}

export interface RolePermissions {
  role: UserRole;
  label: string;
  description: string;
  permissions: string[];
  color: string;
}

export const ROLE_DEFINITIONS: Record<UserRole, RolePermissions> = {
  admin: {
    role: 'admin',
    label: 'Administrator',
    description: 'Full system access and user management',
    permissions: [
      'Manage all users and roles',
      'Access all data and reports',
      'Configure system settings',
      'View audit logs',
      'Manage integrations'
    ],
    color: '#dc2626'
  },
  operations_manager: {
    role: 'operations_manager',
    label: 'Operations Manager',
    description: 'Oversee tutor performance and operations',
    permissions: [
      'View all tutor metrics',
      'Assign interventions',
      'Generate reports',
      'View dashboard analytics',
      'Manage alerts'
    ],
    color: '#ea580c'
  },
  people_ops: {
    role: 'people_ops',
    label: 'People Operations',
    description: 'Manage tutor development and training',
    permissions: [
      'View tutor profiles',
      'Assign training',
      'Track interventions',
      'Add manager notes',
      'View feedback'
    ],
    color: '#ca8a04'
  },
  tutor: {
    role: 'tutor',
    label: 'Tutor',
    description: 'Access own performance and development',
    permissions: [
      'View own performance metrics',
      'Access assigned training',
      'View feedback received',
      'Update profile',
      'View session history'
    ],
    color: '#16a34a'
  },
  student: {
    role: 'student',
    label: 'Student',
    description: 'Submit feedback and view sessions',
    permissions: [
      'Submit session feedback',
      'View own sessions',
      'Rate tutors'
    ],
    color: '#2563eb'
  }
};

// Student Feedback Types

export interface FeedbackTokenValidation {
  valid: boolean;
  session_id?: string;
  student_id?: string;
  tutor_id?: string;
  tutor_name?: string;
  session_date?: string;
  subject?: string;
  is_under_13?: boolean;
  requires_parent_consent?: boolean;
  expires_at?: string;
  message?: string;
}

export interface StudentFeedbackSubmission {
  token: string;
  overall_rating: number;
  subject_knowledge_rating?: number;
  communication_rating?: number;
  patience_rating?: number;
  engagement_rating?: number;
  helpfulness_rating?: number;
  would_recommend?: boolean;
  improvement_areas?: string[];
  free_text_feedback?: string;
  parent_consent_given?: boolean;
  parent_signature?: string;
}

export interface FeedbackSubmissionResponse {
  success: boolean;
  feedback_id: string;
  session_id: string;
  message: string;
  timestamp: string;
}

export const IMPROVEMENT_AREAS = [
  { value: 'subject_knowledge', label: 'Subject Knowledge' },
  { value: 'communication', label: 'Communication' },
  { value: 'patience', label: 'Patience' },
  { value: 'engagement', label: 'Engagement' },
  { value: 'punctuality', label: 'Punctuality' },
  { value: 'technical_skills', label: 'Technical Skills' },
  { value: 'other', label: 'Other' }
] as const;

// Admin - Audit Log Types
export interface AuditLogEntry {
  id: string;
  timestamp: string;
  user_id: number | null;
  user_email: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  ip_address: string | null;
  user_agent: string | null;
  details: Record<string, any> | null;
  status: 'success' | 'failure' | 'pending';
}

export interface AuditLogFilters {
  user_email?: string;
  action?: string;
  resource_type?: string;
  start_date?: string;
  end_date?: string;
  ip_address?: string;
}

export interface AuditLogResponse {
  success: boolean;
  logs: AuditLogEntry[];
  total: number;
  limit: number;
  offset: number;
  filters?: AuditLogFilters;
  timestamp: string;
}

// Admin - Compliance Types
export interface ComplianceReport {
  id: string;
  report_type: 'ferpa' | 'coppa' | 'gdpr';
  period_start: string;
  period_end: string;
  total_records: number;
  compliant_records: number;
  non_compliant_records: number;
  pending_records: number;
  issues: ComplianceIssue[];
  generated_at: string;
}

export interface ComplianceIssue {
  id: string;
  issue_type: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  description: string;
  affected_records: number;
  status: 'open' | 'in_progress' | 'resolved';
  detected_at: string;
  resolved_at?: string;
}

export interface ComplianceMetrics {
  ferpa_compliance_rate: number;
  coppa_consent_rate: number;
  gdpr_compliance_rate: number;
  total_data_requests: number;
  pending_data_requests: number;
  total_consent_records: number;
  active_consent_records: number;
}

export interface ComplianceDashboardResponse {
  success: boolean;
  metrics: ComplianceMetrics;
  recent_reports: ComplianceReport[];
  active_issues: ComplianceIssue[];
  timestamp: string;
}

// Admin - Training Module Types
export interface TrainingModule {
  id: string;
  title: string;
  description: string;
  category: 'pedagogy' | 'technology' | 'communication' | 'compliance' | 'subject_matter';
  priority: 'high' | 'medium' | 'low';
  estimated_duration_minutes: number;
  status: 'to_do' | 'in_progress' | 'completed';
  assigned_tutors: string[];
  completion_rate: number;
  created_at: string;
  updated_at: string;
  due_date?: string;
  prerequisites?: string[];
}

export interface TrainingAssignment {
  module_id: string;
  tutor_id: string;
  tutor_name: string;
  assigned_date: string;
  due_date?: string;
  started_date?: string;
  completed_date?: string;
  status: 'not_started' | 'in_progress' | 'completed' | 'overdue';
  progress_percentage: number;
}

export interface TrainingRecommendationResponse {
  success: boolean;
  tutor_id: string;
  tutor_name: string;
  recommended_modules: TrainingModule[];
  current_assignments: TrainingAssignment[];
  performance_gaps: string[];
  timestamp: string;
}

// Data Retention & Compliance Automation Types

export interface RetentionScanResult {
  scan_date: string;
  retention_deadline: string;
  anonymization_deadline: string;
  dry_run: boolean;
  eligible_for_archival: {
    students: EligibleStudent[];
    tutors: EligibleTutor[];
    sessions: EligibleSession[];
    feedback: EligibleFeedback[];
    audit_logs: EligibleAuditLog[];
  };
  eligible_for_anonymization: {
    students: AnonymizationCandidate[];
    audit_logs: AnonymizationCandidate[];
  };
  summary: RetentionSummary;
}

export interface EligibleStudent {
  student_id: string;
  name: string;
  created_at: string;
  last_activity: string;
  days_since_activity: number;
  eligible_for: string;
}

export interface EligibleTutor {
  tutor_id: string;
  name: string;
  created_at: string;
  last_activity: string;
  days_since_activity: number;
  eligible_for: string;
}

export interface EligibleSession {
  session_id: string;
  tutor_id: string;
  student_id: string;
  scheduled_start: string;
  subject: string;
  eligible_for: string;
}

export interface EligibleFeedback {
  feedback_id: string;
  session_id: string;
  tutor_id: string;
  student_id: string;
  submitted_at: string;
  eligible_for: string;
}

export interface EligibleAuditLog {
  log_id: string;
  action: string;
  timestamp: string;
  eligible_for: string;
}

export interface AnonymizationCandidate {
  student_id?: string;
  name?: string;
  created_at: string;
  eligible_for: string;
}

export interface RetentionSummary {
  total_students_for_archival: number;
  total_tutors_for_archival: number;
  total_sessions_for_archival: number;
  total_feedback_for_archival: number;
  total_audit_logs_for_archival: number;
  total_students_for_anonymization: number;
}

export interface ArchivalRequest {
  entity_type: 'student' | 'tutor';
  entity_id: string;
  reason?: string;
}

export interface ArchivalResult {
  archive_id: string;
  entity_id: string;
  archive_date: string;
  reason: string;
  performed_by: number | null;
  archived_records: {
    student_data?: any;
    sessions: any[];
    feedback: any[];
    record_counts: {
      sessions: number;
      feedback: number;
    };
  };
}

export interface AnonymizationRequest {
  entity_type: 'student' | 'tutor';
  entity_id: string;
}

export interface AnonymizationResult {
  entity_type: string;
  entity_id: string;
  anonymization_date: string;
  anonymized_fields: string[];
  retained_fields: string[];
  performed_by: number | null;
}

export interface DeletionRequest {
  user_id: number;
  deletion_reason?: string;
}

export interface DeletionResult {
  user_id: number;
  deletion_date: string;
  deletion_reason: string;
  records_deleted: Record<string, number>;
  records_anonymized: Record<string, number>;
}

export interface RetentionReport {
  report_generated_at: string;
  report_period: {
    start_date: string;
    end_date: string;
    days: number;
  };
  current_data_inventory: {
    active_students: number;
    active_tutors: number;
    total_sessions: number;
  };
  retention_actions_taken: {
    archival_operations: number;
    anonymization_operations: number;
    deletion_requests_processed: number;
  };
  archival_details: ArchivalDetail[];
  anonymization_details: AnonymizationDetail[];
  deletion_details: DeletionDetail[];
  compliance_status: {
    ferpa_retention_policy: string;
    gdpr_anonymization_eligible_after: string;
    audit_log_retention: string;
  };
}

export interface ArchivalDetail {
  timestamp: string;
  resource_type: string;
  resource_id: string;
  performed_by: number | null;
}

export interface AnonymizationDetail {
  timestamp: string;
  resource_type: string;
  resource_id: string;
  performed_by: number | null;
}

export interface DeletionDetail {
  timestamp: string;
  resource_type: string;
  resource_id: string;
  performed_by: number | null;
  reason: string | null;
}

export interface RetentionPolicy {
  ferpa: {
    framework: string;
    retention_period_years: number;
    retention_period_days: number;
    record_types: Record<string, {
      retention_days: number;
      description: string;
    }>;
    audit_logs: {
      retention_days: number;
      description: string;
    };
    notes: string[];
  };
  gdpr: {
    right_to_erasure: string;
    right_to_access: string;
    right_to_portability: string;
    anonymization_after_days: number;
  };
  automated_archival: {
    enabled: boolean;
    ferpa_retention_days: number;
    grace_period_days: number;
    audit_log_retention_days: number;
  };
  data_lifecycle: {
    stages: Array<{
      stage: string;
      description: string;
      max_age_days?: number;
      after_days?: number;
    }>;
  };
}

export interface RetentionStatusCheck {
  student_id?: string;
  exists: boolean;
  created_at?: string;
  record_age_days?: number;
  last_activity_date?: string | null;
  retention_period_days?: number;
  retention_deadline?: string;
  days_until_eligible_deletion?: number;
  eligible_for_deletion?: boolean;
  should_retain?: boolean;
  error?: string;
}
