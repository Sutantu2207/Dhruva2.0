/**
 * Dhruva.AI V2 — Curriculum, Syllabus & Learning Content Types
 */

export interface LearningResource {
  id: string;
  institution_id: string;
  lesson_id: string;
  title: string;
  resource_type: 'DOCUMENT' | 'SLIDE' | 'CODE' | 'VIDEO' | 'EXTERNAL_LINK' | 'REFERENCE';
  storage_uri?: string | null;
  external_url?: string | null;
  resource_metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface Lesson {
  id: string;
  institution_id: string;
  module_id: string;
  sequence_order: number;
  title: string;
  content_markdown?: string | null;
  lesson_type: 'THEORY' | 'LAB' | 'TUTORIAL' | 'WORKSHOP' | 'READING';
  duration_minutes: number;
  learning_resources?: LearningResource[];
  created_at: string;
  updated_at: string;
}

export interface Module {
  id: string;
  institution_id: string;
  curriculum_id: string;
  sequence_order: number;
  title: string;
  description?: string | null;
  estimated_hours: number;
  learning_outcomes: string[];
  lessons?: Lesson[];
  created_at: string;
  updated_at: string;
}

export interface Curriculum {
  id: string;
  institution_id: string;
  course_id: string;
  program_id?: string | null;
  academic_year_id?: string | null;
  title: string;
  version: number;
  status: 'DRAFT' | 'IN_REVIEW' | 'APPROVED' | 'PUBLISHED' | 'ARCHIVED';
  description?: string | null;
  learning_objectives: string[];
  approved_by?: string | null;
  approved_at?: string | null;
  provenance_id?: string | null;
  modules?: Module[];
  created_at: string;
  updated_at: string;
}
