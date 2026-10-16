/**
 * Dhruva.AI V2 — Phase 6 Mastery, Skills & Learning Evidence TypeScript Definitions.
 *
 * Models:
 * - Concept & ConceptPrerequisite (Academic Knowledge Hierarchy)
 * - LearningOutcome (Bloom's Taxonomy)
 * - Skill & ConceptSkillLink (Institutional Competency Model)
 * - LearningEvidence (Student Portfolio & Artifact Verification)
 * - MasteryRecord (Deterministic Blended Mastery Profile)
 * - ReviewSchedule (SuperMemo SM-2 Spaced Repetition)
 */

export type BloomLevel =
  | 'REMEMBER'
  | 'UNDERSTAND'
  | 'APPLY'
  | 'ANALYZE'
  | 'EVALUATE'
  | 'CREATE';

export type CompetencyLevel =
  | 'NOVICE'
  | 'DEVELOPING'
  | 'PROFICIENT'
  | 'MASTERY';

export type EvidenceType =
  | 'PROJECT_DELIVERABLE'
  | 'CERTIFICATE'
  | 'LAB_REPORT'
  | 'CODE_REPOSITORY'
  | 'RESEARCH_NOTE';

export type VerificationStatus =
  | 'SUBMITTED'
  | 'VERIFIED'
  | 'REJECTED';

export type QualityRating = 0 | 1 | 2 | 3 | 4 | 5;

export interface Concept {
  id: string;
  institution_id: string;
  department_id?: string | null;
  course_id?: string | null;
  parent_concept_id?: string | null;
  code: string;
  name: string;
  description: string;
  bloom_level: BloomLevel;
  created_at: string;
  updated_at: string;
}

export interface ConceptPrerequisite {
  id: string;
  institution_id: string;
  concept_id: string;
  prerequisite_concept_id: string;
  created_at: string;
  updated_at: string;
}

export interface LearningOutcome {
  id: string;
  institution_id: string;
  course_id?: string | null;
  code: string;
  statement: string;
  bloom_level: BloomLevel;
  concept_id?: string | null;
  skill_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Skill {
  id: string;
  institution_id: string;
  code: string;
  name: string;
  category: string;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface ConceptSkillLink {
  concept_id: string;
  skill_id: string;
  weight: number;
}

export interface LearningEvidence {
  id: string;
  institution_id: string;
  student_user_id: string;
  skill_id: string;
  concept_id?: string | null;
  evidence_type: EvidenceType;
  title: string;
  description: string;
  artifact_url: string;
  file_size_bytes?: number | null;
  verification_status: VerificationStatus;
  verified_by?: string | null;
  verified_at?: string | null;
  verification_notes: string;
  source_assessment_id?: string | null;
  source_submission_id?: string | null;
  source_question_id?: string | null;
  source_result_id?: string | null;
  awarded_score?: number | null;
  max_score?: number | null;
  rule_version: string;
  idempotency_key?: string | null;
  is_finalized: boolean;
  created_at: string;
  updated_at: string;
}

export interface CalculationProvenance {
  assessment_component: number;
  evidence_component: number;
  assessment_weight: number;
  evidence_weight: number;
  raw_blended_score: number;
  decay_factor: number;
  days_since_assessment: number;
  decay_half_life_days: number;
  final_mastery_score: number;
  confidence_score: number;
  competency_level: CompetencyLevel;
  rule_version: string;
}

export interface MasteryRecord {
  id: string;
  institution_id: string;
  student_user_id: string;
  skill_id: string;
  skill?: Skill | null;
  mastery_score: number;
  confidence_score: number;
  competency_level: CompetencyLevel;
  assessment_count: intNumber;
  evidence_count: intNumber;
  decay_factor: number;
  rule_version: string;
  calculation_provenance: CalculationProvenance;
  is_stale: boolean;
  last_assessed_at?: string | null;
  created_at: string;
  updated_at: string;
}

type intNumber = number;

export interface ReviewSchedule {
  id: string;
  institution_id: string;
  student_user_id: string;
  concept_id: string;
  concept?: Concept | null;
  interval_days: number;
  repetition_number: number;
  ease_factor: number;
  scheduled_for: string;
  last_reviewed_at?: string | null;
  is_completed: boolean;
}
