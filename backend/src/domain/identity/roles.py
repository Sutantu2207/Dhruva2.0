"""Dhruva.AI V2 — System Roles & Permission Mapping.

Defines the six primary platform roles and their default permission sets:
- SUPER_ADMIN
- INSTITUTION_ADMIN
- HOD
- FACULTY
- STUDENT
- PLACEMENT_OFFICER
"""

from enum import Enum
from typing import Dict, Set
from src.domain.identity.permissions import Permission


class SystemRole(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    INSTITUTION_ADMIN = "INSTITUTION_ADMIN"
    HOD = "HOD"
    FACULTY = "FACULTY"
    STUDENT = "STUDENT"
    PLACEMENT_OFFICER = "PLACEMENT_OFFICER"


# Default permission matrix mapping based on Master Architecture Section 8.2
DEFAULT_ROLE_PERMISSIONS: Dict[SystemRole, Set[Permission]] = {
    SystemRole.SUPER_ADMIN: {
        Permission.PLATFORM_MANAGE,
        Permission.PLATFORM_HEALTH_READ,
        Permission.INSTITUTION_SETTINGS_READ,
        Permission.INSTITUTION_SETTINGS_UPDATE,
        Permission.INSTITUTION_ROLES_MANAGE,
        Permission.INSTITUTION_USERS_MANAGE,
        Permission.DATA_CENTER_READ,
        Permission.DATA_CENTER_STAGE,
        Permission.DATA_CENTER_APPROVE,
        Permission.DATA_CENTER_PUBLISH,
        Permission.CURRICULUM_READ,
        Permission.AUDIT_READ_GLOBAL,
    },
    SystemRole.INSTITUTION_ADMIN: {
        Permission.INSTITUTION_SETTINGS_READ,
        Permission.INSTITUTION_SETTINGS_UPDATE,
        Permission.INSTITUTION_ROLES_MANAGE,
        Permission.INSTITUTION_USERS_MANAGE,
        Permission.DATA_CENTER_READ,
        Permission.DATA_CENTER_STAGE,
        Permission.DATA_CENTER_APPROVE,
        Permission.DATA_CENTER_PUBLISH,
        Permission.CURRICULUM_READ,
        Permission.CURRICULUM_APPROVE,
        Permission.ASSESSMENT_READ,
        Permission.ASSESSMENT_AUDIT,
        Permission.MASTERY_READ_ALL,
        Permission.PORTFOLIO_READ_ALL,
        Permission.PLACEMENT_MANAGE,
        Permission.AUDIT_READ_INSTITUTION,
    },
    SystemRole.HOD: {
        Permission.INSTITUTION_SETTINGS_READ,
        Permission.DATA_CENTER_READ,
        Permission.DATA_CENTER_STAGE,
        Permission.CURRICULUM_READ,
        Permission.CURRICULUM_EDIT,
        Permission.CURRICULUM_APPROVE,
        Permission.ASSESSMENT_READ,
        Permission.ASSESSMENT_AUDIT,
        Permission.MASTERY_READ_DEPT,
        Permission.PORTFOLIO_READ_ALL,
        Permission.AUDIT_READ_DEPT,
    },
    SystemRole.FACULTY: {
        Permission.CURRICULUM_READ,
        Permission.CURRICULUM_SUGGEST,
        Permission.ASSESSMENT_READ,
        Permission.ASSESSMENT_CREATE,
        Permission.ASSESSMENT_GRADE,
        Permission.MASTERY_EDIT,
        Permission.PROJECT_VERIFY,
    },
    SystemRole.STUDENT: {
        Permission.CURRICULUM_READ,
        Permission.ASSESSMENT_READ,
        Permission.ASSESSMENT_SUBMIT,
        Permission.MASTERY_READ_OWN,
        Permission.PORTFOLIO_CREATE,
        Permission.PLACEMENT_READ_OWN,
    },
    SystemRole.PLACEMENT_OFFICER: {
        Permission.CURRICULUM_READ,
        Permission.ASSESSMENT_READ,
        Permission.MASTERY_READ_ALL,
        Permission.PORTFOLIO_READ_ALL,
        Permission.PLACEMENT_MANAGE,
    },
}


def get_permissions_for_role(role: SystemRole) -> Set[str]:
    """Return default set of permission strings for a given role."""
    perms = DEFAULT_ROLE_PERMISSIONS.get(role, set())
    return {p.value for p in perms}
