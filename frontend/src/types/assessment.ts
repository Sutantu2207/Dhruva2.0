/**
 * Dhruva.AI V2 — Assessment, Question Bank & Grading Types
 */

export type QuestionType = 'MCQ' | 'MULTI_SELECT' | 'NUMERICAL' | 'STRUCTURED_TEXT';
export type AssessmentType = 'QUIZ' | 'ASSIGNMENT' | 'MIDTERM' | 'FINAL_EXAM';
export type AssessmentStatus = 'DRAFT' | 'PUBLISHED' | 'CLOSED';
export type DifficultyLevel = 'EASY' | 'MEDIUM' | 'HARD';
export type SubmissionStatus = 'SUBMITTED' | 'AUTOGRADED' | 'PENDING_MANUAL' | 'GRADED';

export interface QuestionOption {
  id: string;
  text: string;
}

export interface QuestionAdmin {
  id: string;
  institution_id: string;
  question_bank_id: string;
  question_type: QuestionType;
  prompt_text: string;
  options: QuestionOption[];
  answer_key: Record<string, unknown>;
  points: number;
  difficulty: DifficultyLevel;
  explanation: string;
  concept_id?: string | null;
  skill_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface QuestionStudent {
  id: string;
  question_type: QuestionType;
  prompt_text: string;
  options: QuestionOption[];
  points: number;
  difficulty: DifficultyLevel;
}

export interface QuestionBank {
  id: string;
  institution_id: string;
  department_id?: string | null;
  course_id?: string | null;
  title: string;
  description: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  questions?: QuestionAdmin[];
}

export interface AssessmentQuestion {
  id: string;
  question_id: string;
  points: number;
  sort_order: number;
  question: QuestionAdmin;
}

export interface AssessmentStudentQuestion {
  id: string;
  question_id: string;
  points: number;
  sort_order: number;
  question: QuestionStudent;
}

export interface Assessment {
  id: string;
  institution_id: string;
  course_offering_id: string;
  title: string;
  instructions: string;
  assessment_type: AssessmentType;
  status: AssessmentStatus;
  publish_at: string;
  due_at: string;
  duration_minutes?: number | null;
  total_points: number;
  passing_percentage: number;
  max_attempts: number;
  created_by?: string | null;
  questions?: AssessmentQuestion[];
  created_at: string;
  updated_at: string;
}

export interface AssessmentStudentDetail {
  id: string;
  course_offering_id: string;
  title: string;
  instructions: string;
  assessment_type: AssessmentType;
  status: AssessmentStatus;
  publish_at: string;
  due_at: string;
  duration_minutes?: number | null;
  total_points: number;
  passing_percentage: number;
  max_attempts: number;
  questions: AssessmentStudentQuestion[];
}

export interface ItemizedBreakdownItem {
  question_id: string;
  question_type: QuestionType;
  max_points?: number;
  allocated_points?: number;
  awarded_points: number;
  status?: string;
  is_correct?: boolean | null;
  grading_method?: 'DETERMINISTIC_AUTOGRADE' | 'MANUAL_EVALUATION' | string;
  feedback?: string;
  manual_evaluated?: boolean;
}

export interface AssessmentResult {
  id: string;
  submission_id: string;
  raw_score: number;
  total_points: number;
  percentage: number;
  grade_letter?: string | null;
  is_passed: boolean;
  itemized_breakdown: ItemizedBreakdownItem[];
  is_finalized: boolean;
  graded_by?: string | null;
  graded_at: string;
}

export interface Submission {
  id: string;
  institution_id: string;
  assessment_id: string;
  student_user_id: string;
  attempt_number: number;
  answers_payload: Record<string, unknown>;
  status: SubmissionStatus;
  started_at: string;
  submitted_at?: string | null;
  result?: AssessmentResult | null;
}
