/**
 * Dhruva.AI V2 — College & Higher Education Institution Types
 */

export interface College {
  id: string;
  name: string;
  code?: string | null;
  institution_type: string;
  affiliated_university?: string | null;
  location: string;
  district: string;
  state: string;
  website?: string | null;
  accreditation?: string | null;
  status: 'ACTIVE' | 'INACTIVE';
  created_at?: string;
  updated_at?: string;
}

export interface CollegeRequest {
  id: string;
  user_id?: string | null;
  requester_name: string;
  requester_email: string;
  college_name: string;
  institution_type?: string | null;
  location?: string | null;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  admin_notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CollegeAnalytics {
  college_id: string;
  college_name: string;
  college_code?: string | null;
  institution_type: string;
  location: string;
  district: string;
  enrolled_students: number;
  career_readiness_avg: number;
  assessment_completion_rate: number;
}

export interface CollegeSubmitPayload {
  college_name: string;
  requester_name: string;
  requester_email: string;
  institution_type?: string;
  location?: string;
}

export interface CollegeCreatePayload {
  name: string;
  code?: string;
  institution_type: string;
  affiliated_university?: string;
  location: string;
  district?: string;
  state?: string;
  website?: string;
  accreditation?: string;
  status?: string;
}

