"""Dhruva.AI V2 — Permissions & Actions Registry.

Defines granular permission strings and action constants.
Supports resource scoping: PLATFORM, INSTITUTION, DEPARTMENT, COURSE, OWN.
"""

from enum import Enum
from typing import Set


class Permission(str, Enum):
    # Platform / Super Admin
    PLATFORM_MANAGE = "platform:manage"
    PLATFORM_HEALTH_READ = "platform:health:read"

    # Institution Administration
    INSTITUTION_SETTINGS_READ = "institution:settings:read"
    INSTITUTION_SETTINGS_UPDATE = "institution:settings:update"
    INSTITUTION_ROLES_MANAGE = "institution:roles:manage"
    INSTITUTION_USERS_MANAGE = "institution:users:manage"

    # Ingestion & Data Center
    DATA_CENTER_READ = "datacenter:read"
    DATA_CENTER_STAGE = "datacenter:stage"
    DATA_CENTER_APPROVE = "datacenter:approve"
    DATA_CENTER_PUBLISH = "datacenter:publish"

    # Academic & Curriculum
    CURRICULUM_READ = "curriculum:read"
    CURRICULUM_SUGGEST = "curriculum:suggest"
    CURRICULUM_EDIT = "curriculum:edit"
    CURRICULUM_APPROVE = "curriculum:approve"

    # Assessments & Grading
    ASSESSMENT_READ = "assessment:read"
    ASSESSMENT_CREATE = "assessment:create"
    ASSESSMENT_SUBMIT = "assessment:submit"
    ASSESSMENT_GRADE = "assessment:grade"
    ASSESSMENT_AUDIT = "assessment:audit"

    # Student Mastery & Portfolios
    MASTERY_READ_OWN = "mastery:read:own"
    MASTERY_READ_DEPT = "mastery:read:dept"
    MASTERY_READ_ALL = "mastery:read:all"
    MASTERY_EDIT = "mastery:edit"

    PORTFOLIO_CREATE = "portfolio:create"
    PORTFOLIO_READ_ALL = "portfolio:read:all"
    PROJECT_VERIFY = "project:verify"

    # Placement
    PLACEMENT_READ_OWN = "placement:read:own"
    PLACEMENT_MANAGE = "placement:manage"

    # Governance & Audit
    AUDIT_READ_DEPT = "audit:read:dept"
    AUDIT_READ_INSTITUTION = "audit:read:institution"
    AUDIT_READ_GLOBAL = "audit:read:global"


class ResourceScope(str, Enum):
    PLATFORM = "PLATFORM"
    INSTITUTION = "INSTITUTION"
    DEPARTMENT = "DEPARTMENT"
    COURSE = "COURSE"
    OWN = "OWN"
