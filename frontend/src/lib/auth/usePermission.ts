'use client';

/**
 * Dhruva.AI V2 — RBAC Permission & Role Evaluation Hook
 */

import { useAuth } from '@/lib/auth/AuthContext';
import { SystemRole } from '@/types/auth';

export function usePermission() {
  const { user } = useAuth();

  const hasRole = (role: SystemRole): boolean => {
    if (!user) return false;
    if (user.roles.includes('SUPER_ADMIN')) return true;
    return user.roles.includes(role);
  };

  const hasAnyRole = (roles: SystemRole[]): boolean => {
    if (!user) return false;
    if (user.roles.includes('SUPER_ADMIN')) return true;
    return roles.some((r) => user.roles.includes(r));
  };

  const hasPermission = (permissionCode: string): boolean => {
    if (!user) return false;
    if (user.roles.includes('SUPER_ADMIN')) return true;
    return user.permissions.includes(permissionCode);
  };

  return {
    hasRole,
    hasAnyRole,
    hasPermission,
    userRole: user?.roles[0] || null,
    isSuperAdmin: user?.roles.includes('SUPER_ADMIN') || false,
  };
}
