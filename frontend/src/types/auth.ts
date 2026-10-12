/**
 * Dhruva.AI V2 — Authentication & Multi-Tenant Types
 */

export type SystemRole =
  | 'SUPER_ADMIN'
  | 'INSTITUTION_ADMIN'
  | 'HOD'
  | 'FACULTY'
  | 'STUDENT'
  | 'PLACEMENT_OFFICER';

export interface Institution {
  id: string;
  slug: string;
  legal_name: string;
  domain?: string | null;
  status: 'ACTIVE' | 'SUSPENDED' | 'PROVISIONING';
  settings: Record<string, unknown>;
  created_at: string;
}

export interface User {
  id: string;
  institution_id?: string | null;
  institution_slug?: string | null;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  phone?: string | null;
  status: 'ACTIVE' | 'SUSPENDED' | 'LOCKED';
  roles: SystemRole[];
  permissions: string[];
  last_login_at?: string | null;
  created_at: string;
}

export interface LoginResponseData {
  user: User;
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface AuthState {
  user: User | null;
  institution: Institution | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}
