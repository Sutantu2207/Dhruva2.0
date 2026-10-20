/**
 * Dhruva.AI V2 — Phase 8 Interventions, Notification Hub & Institutional Analytics TypeScript Definitions.
 *
 * Models:
 * - Intervention (Early Warning & Academic Support Management)
 * - Notification (In-App & Email Multi-Tenant Notification Hub)
 * - AtRiskStudent (Deterministic Early Warning Engine Output)
 * - InstitutionalAnalytics & DepartmentalAnalytics (Rollups & Health Metrics)
 */

export type InterventionType =
  | 'ACADEMIC_TUTORING'
  | 'ATTENDANCE_COUNSELING'
  | 'MENTOR_CHECKIN'
  | 'STUDY_PLAN_REVISION'
  | 'PSYCHOLOGICAL_COUNSELING';

export type InterventionStatus =
  | 'ASSIGNED'
  | 'IN_PROGRESS'
  | 'COMPLETED'
  | 'ESCALATED'
  | 'DISMISSED';

export type RiskLevel = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'MODERATE' | 'LOW' | 'NORMAL' | 'NONE';

export interface Intervention {
  id: string;
  institution_id: string;
  student_user_id: string;
  faculty_user_id?: string | null;
  intervention_type: InterventionType;
  trigger_reason: string;
  status: InterventionStatus;
  action_plan: string;
  notes: string;
  outcome_notes: string;
  assigned_at: string;
  due_date?: string | null;
  completed_at?: string | null;
  created_at: string;
  updated_at: string;
  student?: {
    id: string;
    full_name: string;
    email: string;
    roll_number?: string;
  } | null;
  faculty?: {
    id: string;
    full_name: string;
    email: string;
  } | null;
}

export interface InterventionCreateInput {
  student_user_id: string;
  faculty_user_id?: string | null;
  intervention_type: string;
  trigger_reason: string;
  action_plan?: string;
  notes?: string;
  due_date?: string | null;
}

export interface InterventionUpdateInput {
  status?: InterventionStatus;
  action_plan?: string;
  outcome_notes?: string;
}

export interface DetectedRiskRule {
  rule_id: string;
  name: string;
  severity: RiskLevel;
  metric: string;
  actual_value: number;
  threshold_value: number;
  description: string;
}

export interface AtRiskStudent {
  student_id: string;
  full_name: string;
  email: string;
  roll_number: string;
  risk_level: RiskLevel;
  detected_rules: DetectedRiskRule[];
  recommended_intervention_type: InterventionType;
  trigger_reason: string;
  metrics_summary: {
    average_mastery?: number;
    assessment_fail_count?: number;
    decayed_skills_count?: number;
    attendance_rate?: number;
    [key: string]: any;
  };
}

export interface NotificationItem {
  id: string;
  institution_id: string;
  recipient_user_id: string;
  actor_user_id?: string | null;
  notification_type: string;
  title: string;
  message: string;
  link_url?: string;
  is_read: boolean;
  read_at?: string | null;
  metadata_json?: Record<string, any>;
  created_at: string;
}

export interface DepartmentalMetric {
  department_id: string;
  department_name: string;
  department_code: string;
  enrolled_students: number;
  at_risk_students: number;
  active_interventions: number;
  average_mastery: number;
  passing_rate: number;
  retention_index: number;
}

export interface InstitutionalAnalytics {
  institution_id: string;
  computed_at: string;
  active_students: number;
  at_risk_count: number;
  active_interventions: number;
  overall_passing_rate: number;
  average_mastery_index: number;
  total_assessments_taken: number;
  departments: DepartmentalMetric[];
  skill_distribution: {
    mastery: number;
    proficient: number;
    developing: number;
    novice: number;
  };
  interventions_by_status: Record<InterventionStatus, number>;
  interventions_by_type: Record<InterventionType, number>;
}
