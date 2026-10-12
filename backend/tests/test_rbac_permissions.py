"""Dhruva.AI V2 — Unit Tests: Role-Based Access Control (RBAC) & Permission Registry.

Tests:
- Default permission matrix completeness for all 6 system roles:
  SUPER_ADMIN, INSTITUTION_ADMIN, HOD, FACULTY, STUDENT, PLACEMENT_OFFICER
- Permission boundaries (Student cannot grade, Faculty cannot delete users, HOD restricted to dept)
- Role permission retrieval helper
"""

import pytest
from src.domain.identity.permissions import Permission
from src.domain.identity.roles import (
    DEFAULT_ROLE_PERMISSIONS,
    SystemRole,
    get_permissions_for_role,
)


class TestRBACPermissionsMatrix:
    """Validate permission boundaries and matrix enforcement."""

    def test_all_system_roles_have_permission_mappings(self):
        for role in SystemRole:
            assert role in DEFAULT_ROLE_PERMISSIONS
            perms = get_permissions_for_role(role)
            assert isinstance(perms, set)
            assert len(perms) > 0

    def test_super_admin_permissions(self):
        perms = get_permissions_for_role(SystemRole.SUPER_ADMIN)
        assert Permission.PLATFORM_MANAGE.value in perms
        assert Permission.PLATFORM_HEALTH_READ.value in perms
        assert Permission.INSTITUTION_USERS_MANAGE.value in perms
        assert Permission.AUDIT_READ_GLOBAL.value in perms

    def test_institution_admin_permissions(self):
        perms = get_permissions_for_role(SystemRole.INSTITUTION_ADMIN)
        assert Permission.INSTITUTION_SETTINGS_UPDATE.value in perms
        assert Permission.INSTITUTION_USERS_MANAGE.value in perms
        assert Permission.DATA_CENTER_APPROVE.value in perms
        assert Permission.CURRICULUM_APPROVE.value in perms
        # Cannot manage platform globally
        assert Permission.PLATFORM_MANAGE.value not in perms
        assert Permission.AUDIT_READ_GLOBAL.value not in perms

    def test_faculty_permissions_boundary(self):
        perms = get_permissions_for_role(SystemRole.FACULTY)
        # Permitted
        assert Permission.ASSESSMENT_CREATE.value in perms
        assert Permission.ASSESSMENT_GRADE.value in perms
        assert Permission.CURRICULUM_SUGGEST.value in perms
        assert Permission.PROJECT_VERIFY.value in perms
        # Forbidden
        assert Permission.INSTITUTION_USERS_MANAGE.value not in perms
        assert Permission.CURRICULUM_APPROVE.value not in perms
        assert Permission.DATA_CENTER_APPROVE.value not in perms
        assert Permission.AUDIT_READ_GLOBAL.value not in perms

    def test_student_permissions_boundary(self):
        perms = get_permissions_for_role(SystemRole.STUDENT)
        # Permitted
        assert Permission.ASSESSMENT_SUBMIT.value in perms
        assert Permission.MASTERY_READ_OWN.value in perms
        assert Permission.PORTFOLIO_CREATE.value in perms
        assert Permission.PLACEMENT_READ_OWN.value in perms
        # Forbidden
        assert Permission.ASSESSMENT_GRADE.value not in perms
        assert Permission.ASSESSMENT_CREATE.value not in perms
        assert Permission.MASTERY_READ_ALL.value not in perms
        assert Permission.INSTITUTION_SETTINGS_READ.value not in perms
        assert Permission.DATA_CENTER_STAGE.value not in perms

    def test_hod_permissions_boundary(self):
        perms = get_permissions_for_role(SystemRole.HOD)
        # Permitted
        assert Permission.CURRICULUM_EDIT.value in perms
        assert Permission.CURRICULUM_APPROVE.value in perms
        assert Permission.MASTERY_READ_DEPT.value in perms
        assert Permission.AUDIT_READ_DEPT.value in perms
        # Forbidden
        assert Permission.PLATFORM_MANAGE.value not in perms
        assert Permission.AUDIT_READ_GLOBAL.value not in perms

    def test_placement_officer_permissions_boundary(self):
        perms = get_permissions_for_role(SystemRole.PLACEMENT_OFFICER)
        # Permitted
        assert Permission.PLACEMENT_MANAGE.value in perms
        assert Permission.PORTFOLIO_READ_ALL.value in perms
        assert Permission.MASTERY_READ_ALL.value in perms
        # Forbidden
        assert Permission.ASSESSMENT_CREATE.value not in perms
        assert Permission.CURRICULUM_APPROVE.value not in perms
        assert Permission.INSTITUTION_USERS_MANAGE.value not in perms
