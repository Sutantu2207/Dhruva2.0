/**
 * Dhruva.AI V2 — Academic Hierarchy Domain Types
 */

export interface Department {
  id: string;
  institution_id: string;
  code: string;
  name: string;
  hod_user_id?: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Program {
  id: string;
  institution_id: string;
  department_id: string;
  code: string;
  name: string;
  degree_level: string;
  total_semesters: number;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface AcademicYear {
  id: string;
  institution_id: string;
  code: string;
  name: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
  created_at: string;
  updated_at: string;
}

export interface Semester {
  id: string;
  institution_id: string;
  academic_year_id: string;
  term_number: number;
  name: string;
  start_date: string;
  end_date: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Batch {
  id: string;
  institution_id: string;
  program_id: string;
  name: string;
  admission_year: number;
  graduation_year: number;
  created_at: string;
  updated_at: string;
}

export interface Section {
  id: string;
  institution_id: string;
  batch_id: string;
  name: string;
  capacity: number;
  created_at: string;
  updated_at: string;
}

export interface Course {
  id: string;
  institution_id: string;
  department_id: string;
  code: string;
  title: string;
  credits: number;
  course_type: string;
  course_metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface CourseOffering {
  id: string;
  institution_id: string;
  course_id: string;
  academic_year_id: string;
  semester_id: string;
  section_id?: string | null;
  status: string;
  start_date?: string | null;
  end_date?: string | null;
  created_at: string;
  updated_at: string;
}

export interface TeachingAssignment {
  id: string;
  course_offering_id: string;
  faculty_user_id: string;
  role_type: string;
  assigned_at: string;
}

export interface StudentEnrollment {
  id: string;
  institution_id: string;
  course_offering_id: string;
  student_user_id: string;
  enrollment_status: string;
  enrolled_at: string;
  final_grade?: number | null;
}
