/**
 * Dhruva.AI V2 — Phase 7 Projects, Portfolios & Placement TypeScript Definitions.
 *
 * Models:
 * - Project & ProjectSkill & ProjectEvidence (Student Project Studio)
 * - Portfolio (Portfolio Builder & Privacy Gating)
 * - CareerGoal (Career Objectives & Required Competencies)
 * - CareerReadiness (Deterministic Readiness Alignment Index)
 * - TalentCandidate & PlacementAnalytics (Placement Officer Talent Discovery)
 */

export type ProjectType =
  | 'CAPSTONE'
  | 'COURSE_PROJECT'
  | 'RESEARCH'
  | 'HACKATHON'
  | 'OPEN_SOURCE';

export type ProjectStatus =
  | 'DRAFT'
  | 'SUBMITTED'
  | 'VERIFIED'
  | 'REJECTED'
  | 'REVOKED';

export type PortfolioVisibility =
  | 'PRIVATE'
  | 'INSTITUTION'
  | 'PUBLIC';

export interface ProjectSkillItem {
  id: string;
  skill_id: string;
  contribution_weight: number;
  skill?: {
    id: string;
    code: string;
    name: string;
    category: string;
  } | null;
}

export interface ProjectEvidenceItem {
  id: string;
  evidence_id: string;
  evidence?: {
    id: string;
    title: string;
    evidence_type: string;
    artifact_url: string;
    verification_status: string;
  } | null;
}

export interface Project {
  id: string;
  institution_id: string;
  student_user_id: string;
  title: string;
  description: string;
  project_type: ProjectType;
  status: ProjectStatus;
  repository_url: string;
  deployment_url: string;
  start_date?: string | null;
  end_date?: string | null;
  contribution_details: string;
  verified_by?: string | null;
  verified_at?: string | null;
  verification_notes: string;
  revoked_by?: string | null;
  revoked_at?: string | null;
  revocation_reason: string;
  skills?: ProjectSkillItem[];
  evidences?: ProjectEvidenceItem[];
  created_at: string;
  updated_at: string;
}

export interface Portfolio {
  id: string;
  institution_id: string;
  student_user_id: string;
  slug: string;
  headline: string;
  bio: string;
  visibility: PortfolioVisibility;
  is_published: boolean;
  published_at?: string | null;
  curated_project_ids: string[];
  featured_skill_ids: string[];
  social_links: {
    github?: string;
    linkedin?: string;
    website?: string;
    twitter?: string;
    [key: string]: string | undefined;
  };
  custom_domain?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PublicPortfolio {
  id: string;
  institution_id: string;
  student_name: string;
  student_email: string;
  slug: string;
  headline: string;
  bio: string;
  visibility: PortfolioVisibility;
  is_published: boolean;
  published_at?: string | null;
  curated_projects: Array<{
    id: string;
    title: string;
    description: string;
    project_type: ProjectType;
    status: ProjectStatus;
    repository_url: string;
    deployment_url: string;
    contribution_details: string;
    skills: Array<{ id: string; code: string; name: string }>;
  }>;
  social_links: Record<string, string>;
  custom_domain?: string | null;
}

export interface CareerGoal {
  id: string;
  institution_id: string;
  student_user_id: string;
  target_role: string;
  target_industry: string;
  target_companies: string[];
  required_skill_ids: string[];
  status: 'ACTIVE' | 'ARCHIVED';
  created_at: string;
  updated_at: string;
}

export type SkillGapStatus = 'MET' | 'PARTIAL' | 'DEFICIT' | 'MISSING_EVIDENCE';

export interface SkillGapItem {
  skill_id: string;
  code: string;
  name: string;
  category: string;
  status: SkillGapStatus;
  score: number;
  confidence_score: number;
  decay_factor: number;
  has_verified_project: boolean;
  gap_note: string;
}

export interface TargetGapAnalysis {
  skills_breakdown: SkillGapItem[];
  met_skills: string[];
  partial_skills: string[];
  deficit_skills: string[];
  met_count: number;
  partial_count: number;
  deficit_count: number;
  summary?: string;
}

export interface CareerReadiness {
  id: string;
  institution_id: string;
  student_user_id: string;
  career_goal_id: string;
  target_role: string;
  readiness_score: number;
  matching_skills_count: number;
  total_required_skills: number;
  target_gap_analysis: TargetGapAnalysis;
  rule_version: string;
  calculated_at: string;
  calculation_provenance: {
    rule_version: string;
    algorithm: string;
    explanation: string;
    evaluated_at: string;
  };
}

export interface TalentCandidate {
  student_id: string;
  full_name: string;
  email: string;
  target_role: string;
  readiness_score: number;
  matching_skills_count: number;
  total_required_skills: number;
  portfolio_slug?: string | null;
  portfolio_accessible: boolean;
}

export interface PlacementAnalytics {
  total_evaluated_students: number;
  average_readiness_score: number;
  distribution: {
    high_readiness_90_plus: number;
    proficient_70_89: number;
    developing_40_69: number;
    deficit_under_40: number;
  };
  top_target_roles: Array<{
    role: string;
    student_count: number;
  }>;
}
