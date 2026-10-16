"""Dhruva.AI V2 — Placement, Projects & Portfolios Application Service.

Coordinates:
- Student Project Studio & Faculty Verification lifecycle.
- Portfolio curation, privacy controls, and publication gating.
- Deterministic Career Readiness calculation with gap analysis.
- Placement Officer Talent Discovery Pool & Institutional Analytics.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.application.placement.readiness_engine import DeterministicReadinessEngine
from src.core.errors import (
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from src.domain.identity.models import User
from src.domain.mastery.models import LearningEvidence, MasteryRecord, Skill
from src.domain.placement.models import (
    CareerGoal,
    CareerReadiness,
    Portfolio,
    Project,
    ProjectEvidence,
    ProjectSkill,
)
from src.infrastructure.persistence.postgres.base import utc_now


class PlacementService:
    """Application service for student projects, portfolios, and placement talent discovery."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # =========================================================================
    # 1. STUDENT PROJECT STUDIO
    # =========================================================================
    async def create_project(
        self,
        institution_id: uuid.UUID,
        student_user_id: uuid.UUID,
        title: str,
        description: str = "",
        project_type: str = "COURSE_PROJECT",
        repository_url: str = "",
        deployment_url: str = "",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        contribution_details: str = "",
        skill_ids: Optional[List[uuid.UUID]] = None,
    ) -> Project:
        """Create a new project deliverable in DRAFT status."""
        valid_types = {"CAPSTONE", "COURSE_PROJECT", "RESEARCH", "HACKATHON", "OPEN_SOURCE"}
        p_type = project_type.upper().strip()
        if p_type not in valid_types:
            raise ValidationError(f"Invalid project_type '{project_type}'. Valid: {sorted(valid_types)}")

        if not title or len(title.strip()) < 2:
            raise ValidationError("Project title must be at least 2 characters.")

        project = Project(
            id=uuid.uuid4(),
            institution_id=institution_id,
            student_user_id=student_user_id,
            title=title.strip(),
            description=description.strip(),
            project_type=p_type,
            status="DRAFT",
            repository_url=repository_url.strip(),
            deployment_url=deployment_url.strip(),
            start_date=start_date,
            end_date=end_date,
            contribution_details=contribution_details.strip(),
        )
        self.session.add(project)

        if skill_ids:
            for s_id in skill_ids:
                ps = ProjectSkill(
                    id=uuid.uuid4(),
                    institution_id=institution_id,
                    project_id=project.id,
                    skill_id=s_id,
                    contribution_weight=1.0,
                )
                self.session.add(ps)

        await self.session.commit()
        await self.session.refresh(project)
        return project

    async def update_project(
        self,
        institution_id: uuid.UUID,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        title: Optional[str] = None,
        description: Optional[str] = None,
        project_type: Optional[str] = None,
        repository_url: Optional[str] = None,
        deployment_url: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        contribution_details: Optional[str] = None,
    ) -> Project:
        """Update permitted project fields while in DRAFT or REJECTED status."""
        project = await self.get_project(institution_id, project_id)
        if project.student_user_id != user_id:
            raise PermissionDeniedError("Cannot modify another student's project.")

        if project.status == "VERIFIED":
            raise ConflictError("Cannot directly edit a verified project. Request verification review or revoke first.")

        if title is not None:
            if len(title.strip()) < 2:
                raise ValidationError("Title must be at least 2 characters.")
            project.title = title.strip()
        if description is not None:
            project.description = description.strip()
        if project_type is not None:
            p_type = project_type.upper().strip()
            valid_types = {"CAPSTONE", "COURSE_PROJECT", "RESEARCH", "HACKATHON", "OPEN_SOURCE"}
            if p_type not in valid_types:
                raise ValidationError(f"Invalid project type '{project_type}'.")
            project.project_type = p_type
        if repository_url is not None:
            project.repository_url = repository_url.strip()
        if deployment_url is not None:
            project.deployment_url = deployment_url.strip()
        if start_date is not None:
            project.start_date = start_date
        if end_date is not None:
            project.end_date = end_date
        if contribution_details is not None:
            project.contribution_details = contribution_details.strip()

        await self.session.commit()
        await self.session.refresh(project)
        return project

    async def submit_project(
        self,
        institution_id: uuid.UUID,
        project_id: uuid.UUID,
        student_user_id: uuid.UUID,
    ) -> Project:
        """Submit a project for faculty evaluation and verification."""
        project = await self.get_project(institution_id, project_id)
        if project.student_user_id != student_user_id:
            raise PermissionDeniedError("Cannot submit another student's project.")

        if project.status not in ["DRAFT", "REJECTED"]:
            raise ConflictError(f"Cannot submit project in status '{project.status}'. Must be DRAFT or REJECTED.")

        project.status = "SUBMITTED"
        await self.session.commit()
        await self.session.refresh(project)
        return project

    async def link_skill_to_project(
        self,
        institution_id: uuid.UUID,
        project_id: uuid.UUID,
        skill_id: uuid.UUID,
        user_id: uuid.UUID,
        weight: float = 1.0,
    ) -> ProjectSkill:
        """Associate an institutional competency with a student project."""
        project = await self.get_project(institution_id, project_id)
        if project.student_user_id != user_id:
            raise PermissionDeniedError("Cannot alter skills for another student's project.")

        # Check existing link
        stmt = select(ProjectSkill).where(
            and_(
                ProjectSkill.institution_id == institution_id,
                ProjectSkill.project_id == project_id,
                ProjectSkill.skill_id == skill_id,
            )
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()
        if existing:
            existing.contribution_weight = weight
            await self.session.commit()
            return existing

        ps = ProjectSkill(
            id=uuid.uuid4(),
            institution_id=institution_id,
            project_id=project_id,
            skill_id=skill_id,
            contribution_weight=weight,
        )
        self.session.add(ps)
        await self.session.commit()
        await self.session.refresh(ps)
        return ps

    async def link_evidence_to_project(
        self,
        institution_id: uuid.UUID,
        project_id: uuid.UUID,
        evidence_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ProjectEvidence:
        """Link a verified learning evidence artifact to this project."""
        project = await self.get_project(institution_id, project_id)
        if project.student_user_id != user_id:
            raise PermissionDeniedError("Cannot link evidence to another student's project.")

        # Verify evidence ownership
        ev_stmt = select(LearningEvidence).where(
            and_(
                LearningEvidence.id == evidence_id,
                LearningEvidence.institution_id == institution_id,
            )
        )
        evidence = (await self.session.execute(ev_stmt)).scalar_one_or_none()
        if not evidence:
            raise NotFoundError(f"Learning evidence '{evidence_id}' not found.")
        if evidence.student_user_id != user_id:
            raise PermissionDeniedError("Cannot attach another student's evidence.")

        # Check existing
        link_stmt = select(ProjectEvidence).where(
            and_(
                ProjectEvidence.project_id == project_id,
                ProjectEvidence.evidence_id == evidence_id,
            )
        )
        existing = (await self.session.execute(link_stmt)).scalar_one_or_none()
        if existing:
            return existing

        pe = ProjectEvidence(
            id=uuid.uuid4(),
            institution_id=institution_id,
            project_id=project_id,
            evidence_id=evidence_id,
        )
        self.session.add(pe)
        await self.session.commit()
        await self.session.refresh(pe)
        return pe

    async def verify_project(
        self,
        institution_id: uuid.UUID,
        project_id: uuid.UUID,
        verifier_user_id: uuid.UUID,
        is_verified: bool,
        verification_notes: str = "",
    ) -> Project:
        """Faculty or HOD review and verification of submitted student projects."""
        project = await self.get_project(institution_id, project_id)
        if project.status not in ["SUBMITTED", "DRAFT"]:
            raise ConflictError(f"Cannot verify project in status '{project.status}'. Must be SUBMITTED.")

        now = utc_now()
        if is_verified:
            project.status = "VERIFIED"
            project.verified_by = verifier_user_id
            project.verified_at = now
            project.verification_notes = verification_notes.strip()
            # Clear revocation if previously revoked
            project.revoked_by = None
            project.revoked_at = None
            project.revocation_reason = ""
        else:
            project.status = "REJECTED"
            project.verified_by = verifier_user_id
            project.verified_at = now
            project.verification_notes = verification_notes.strip()

        await self.session.commit()
        await self.session.refresh(project)
        return project

    async def revoke_project_verification(
        self,
        institution_id: uuid.UUID,
        project_id: uuid.UUID,
        revoker_user_id: uuid.UUID,
        revocation_reason: str,
    ) -> Project:
        """Authorized faculty or admin revocation of a previously verified project."""
        if not revocation_reason or len(revocation_reason.strip()) < 5:
            raise ValidationError("A clear revocation reason (minimum 5 characters) must be documented.")

        project = await self.get_project(institution_id, project_id)
        if project.status != "VERIFIED":
            raise ConflictError(f"Cannot revoke project in status '{project.status}'. Only VERIFIED projects can be revoked.")

        project.status = "REVOKED"
        project.revoked_by = revoker_user_id
        project.revoked_at = utc_now()
        project.revocation_reason = revocation_reason.strip()

        await self.session.commit()
        await self.session.refresh(project)
        return project

    async def get_project(self, institution_id: uuid.UUID, project_id: uuid.UUID) -> Project:
        """Retrieve a project by ID with strict tenant boundary enforcement."""
        stmt = (
            select(Project)
            .options(
                selectinload(Project.skills).selectinload(ProjectSkill.skill),
                selectinload(Project.evidences).selectinload(ProjectEvidence.evidence),
            )
            .where(
                and_(
                    Project.id == project_id,
                    Project.institution_id == institution_id,
                )
            )
        )
        project = (await self.session.execute(stmt)).scalar_one_or_none()
        if not project:
            raise NotFoundError(f"Project '{project_id}' not found in this institution.")
        return project

    async def list_student_projects(
        self,
        institution_id: uuid.UUID,
        student_user_id: uuid.UUID,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Project]:
        """List all projects authored by a specific student."""
        stmt = (
            select(Project)
            .options(
                selectinload(Project.skills).selectinload(ProjectSkill.skill),
                selectinload(Project.evidences).selectinload(ProjectEvidence.evidence),
            )
            .where(
                and_(
                    Project.institution_id == institution_id,
                    Project.student_user_id == student_user_id,
                )
            )
        )
        if status:
            stmt = stmt.where(Project.status == status.upper().strip())

        stmt = stmt.order_by(Project.created_at.desc()).limit(limit).offset(offset)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    # =========================================================================
    # 2. PORTFOLIO BUILDER & PRIVACY GATING
    # =========================================================================
    async def get_or_create_portfolio(
        self,
        institution_id: uuid.UUID,
        student_user: User,
    ) -> Portfolio:
        """Get or initialize student portfolio profile."""
        stmt = select(Portfolio).where(
            and_(
                Portfolio.institution_id == institution_id,
                Portfolio.student_user_id == student_user.id,
            )
        )
        portfolio = (await self.session.execute(stmt)).scalar_one_or_none()
        if portfolio:
            return portfolio

        # Generate unique slug from student name or email prefix
        base_slug = f"{student_user.first_name}-{student_user.last_name}".lower().replace(" ", "-")
        slug = f"{base_slug}-{str(student_user.id)[:6]}"

        portfolio = Portfolio(
            id=uuid.uuid4(),
            institution_id=institution_id,
            student_user_id=student_user.id,
            slug=slug,
            headline=f"Student Portfolio — {student_user.first_name} {student_user.last_name}",
            bio="",
            visibility="PRIVATE",
            is_published=False,
            curated_project_ids=[],
            featured_skill_ids=[],
            social_links={},
        )
        self.session.add(portfolio)
        await self.session.commit()
        await self.session.refresh(portfolio)
        return portfolio

    async def update_portfolio(
        self,
        institution_id: uuid.UUID,
        student_user_id: uuid.UUID,
        headline: Optional[str] = None,
        bio: Optional[str] = None,
        visibility: Optional[str] = None,
        curated_project_ids: Optional[List[str]] = None,
        featured_skill_ids: Optional[List[str]] = None,
        social_links: Optional[Dict[str, Any]] = None,
        custom_domain: Optional[str] = None,
    ) -> Portfolio:
        """Update portfolio details and curated projects."""
        stmt = select(Portfolio).where(
            and_(
                Portfolio.institution_id == institution_id,
                Portfolio.student_user_id == student_user_id,
            )
        )
        portfolio = (await self.session.execute(stmt)).scalar_one_or_none()
        if not portfolio:
            raise NotFoundError("Portfolio does not exist for this student.")

        if headline is not None:
            portfolio.headline = headline.strip()
        if bio is not None:
            portfolio.bio = bio.strip()
        if visibility is not None:
            v = visibility.upper().strip()
            if v not in {"PRIVATE", "INSTITUTION", "PUBLIC"}:
                raise ValidationError("Visibility must be PRIVATE, INSTITUTION, or PUBLIC.")
            portfolio.visibility = v
        if curated_project_ids is not None:
            portfolio.curated_project_ids = curated_project_ids
        if featured_skill_ids is not None:
            portfolio.featured_skill_ids = featured_skill_ids
        if social_links is not None:
            portfolio.social_links = social_links
        if custom_domain is not None:
            portfolio.custom_domain = custom_domain.strip() or None

        await self.session.commit()
        await self.session.refresh(portfolio)
        return portfolio

    async def publish_portfolio(
        self,
        institution_id: uuid.UUID,
        student_user_id: uuid.UUID,
        publish: bool,
    ) -> Portfolio:
        """Publish or unpublish student portfolio."""
        stmt = select(Portfolio).where(
            and_(
                Portfolio.institution_id == institution_id,
                Portfolio.student_user_id == student_user_id,
            )
        )
        portfolio = (await self.session.execute(stmt)).scalar_one_or_none()
        if not portfolio:
            raise NotFoundError("Portfolio does not exist.")

        portfolio.is_published = publish
        portfolio.published_at = utc_now() if publish else None

        await self.session.commit()
        await self.session.refresh(portfolio)
        return portfolio

    async def get_portfolio_by_slug(
        self,
        institution_id: uuid.UUID,
        slug: str,
        viewer_user: Optional[User] = None,
    ) -> Dict[str, Any]:
        """Retrieve portfolio by slug respecting strict visibility boundaries.

        Rules:
        - PUBLIC + is_published: Visible to all.
        - INSTITUTION + is_published: Visible only if viewer belongs to same institution.
        - PRIVATE: Visible only to the owner student, or staff with placement/admin roles.
        """
        stmt = select(Portfolio).where(
            and_(
                Portfolio.institution_id == institution_id,
                Portfolio.slug == slug.strip(),
            )
        )
        portfolio = (await self.session.execute(stmt)).scalar_one_or_none()
        if not portfolio:
            raise NotFoundError(f"Portfolio '{slug}' not found.")

        # Privacy Enforcement
        is_owner = viewer_user and (viewer_user.id == portfolio.student_user_id)
        is_staff = viewer_user and any(
            r in ["SUPER_ADMIN", "INSTITUTION_ADMIN", "HOD", "PLACEMENT_OFFICER"]
            for r in [ur.role.name for ur in getattr(viewer_user, "user_roles", [])]
        )

        if not portfolio.is_published and not (is_owner or is_staff):
            raise PermissionDeniedError("This portfolio is currently in private draft mode.")

        if portfolio.visibility == "PRIVATE" and not (is_owner or is_staff):
            raise PermissionDeniedError("This portfolio is configured as PRIVATE.")

        if portfolio.visibility == "INSTITUTION":
            if not viewer_user or viewer_user.institution_id != institution_id:
                raise PermissionDeniedError("This portfolio is restricted to members of this institution.")

        # Load curated projects (only verified/approved projects appear in public portfolio)
        curated_projects = []
        if portfolio.curated_project_ids:
            try:
                curated_uuids = [uuid.UUID(pid) for pid in portfolio.curated_project_ids]
                p_stmt = (
                    select(Project)
                    .options(selectinload(Project.skills).selectinload(ProjectSkill.skill))
                    .where(
                        and_(
                            Project.id.in_(curated_uuids),
                            Project.institution_id == institution_id,
                            # Public portfolios only expose VERIFIED projects, owner/staff can see all curated
                            or_(Project.status == "VERIFIED", is_owner, is_staff),
                        )
                    )
                )
                p_res = await self.session.execute(p_stmt)
                curated_projects = list(p_res.scalars().all())
            except Exception:
                curated_projects = []

        # Load student user info safely (excluding password hashes, sensitive tokens)
        u_stmt = select(User).where(User.id == portfolio.student_user_id)
        student = (await self.session.execute(u_stmt)).scalar_one()

        return {
            "id": str(portfolio.id),
            "institution_id": str(portfolio.institution_id),
            "student_name": f"{student.first_name} {student.last_name}",
            "student_email": student.email if (is_owner or is_staff) else "",
            "slug": portfolio.slug,
            "headline": portfolio.headline,
            "bio": portfolio.bio,
            "visibility": portfolio.visibility,
            "is_published": portfolio.is_published,
            "published_at": portfolio.published_at.isoformat() if portfolio.published_at else None,
            "curated_projects": [
                {
                    "id": str(p.id),
                    "title": p.title,
                    "description": p.description,
                    "project_type": p.project_type,
                    "status": p.status,
                    "repository_url": p.repository_url,
                    "deployment_url": p.deployment_url,
                    "contribution_details": p.contribution_details,
                    "skills": [
                        {"id": str(ps.skill.id), "code": ps.skill.code, "name": ps.skill.name}
                        for ps in p.skills
                        if ps.skill
                    ],
                }
                for p in curated_projects
            ],
            "social_links": portfolio.social_links,
            "custom_domain": portfolio.custom_domain,
        }

    # =========================================================================
    # 3. CAREER GOALS & DETERMINISTIC CAREER READINESS
    # =========================================================================
    async def create_or_update_career_goal(
        self,
        institution_id: uuid.UUID,
        student_user_id: uuid.UUID,
        target_role: str,
        target_industry: str = "",
        target_companies: Optional[List[str]] = None,
        required_skill_ids: Optional[List[str]] = None,
    ) -> CareerGoal:
        """Create or update target career objective for a student."""
        if not target_role or len(target_role.strip()) < 2:
            raise ValidationError("Target role must be at least 2 characters.")

        stmt = select(CareerGoal).where(
            and_(
                CareerGoal.institution_id == institution_id,
                CareerGoal.student_user_id == student_user_id,
                CareerGoal.status == "ACTIVE",
            )
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()

        if existing:
            existing.target_role = target_role.strip()
            existing.target_industry = target_industry.strip()
            existing.target_companies = target_companies or []
            existing.required_skill_ids = required_skill_ids or []
            await self.session.commit()
            await self.session.refresh(existing)
            return existing

        goal = CareerGoal(
            id=uuid.uuid4(),
            institution_id=institution_id,
            student_user_id=student_user_id,
            target_role=target_role.strip(),
            target_industry=target_industry.strip(),
            target_companies=target_companies or [],
            required_skill_ids=required_skill_ids or [],
            status="ACTIVE",
        )
        self.session.add(goal)
        await self.session.commit()
        await self.session.refresh(goal)
        return goal

    async def get_student_career_goal(
        self,
        institution_id: uuid.UUID,
        student_user_id: uuid.UUID,
    ) -> Optional[CareerGoal]:
        """Fetch active career goal for a student."""
        stmt = (
            select(CareerGoal)
            .options(selectinload(CareerGoal.readiness_records))
            .where(
                and_(
                    CareerGoal.institution_id == institution_id,
                    CareerGoal.student_user_id == student_user_id,
                    CareerGoal.status == "ACTIVE",
                )
            )
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def compute_career_readiness(
        self,
        institution_id: uuid.UUID,
        student_user_id: uuid.UUID,
        career_goal_id: Optional[uuid.UUID] = None,
    ) -> CareerReadiness:
        """Deterministically evaluates career readiness from persisted verified records."""
        # 1. Resolve career goal
        if career_goal_id:
            g_stmt = select(CareerGoal).where(
                and_(
                    CareerGoal.id == career_goal_id,
                    CareerGoal.institution_id == institution_id,
                    CareerGoal.student_user_id == student_user_id,
                )
            )
        else:
            g_stmt = select(CareerGoal).where(
                and_(
                    CareerGoal.institution_id == institution_id,
                    CareerGoal.student_user_id == student_user_id,
                    CareerGoal.status == "ACTIVE",
                )
            )
        goal = (await self.session.execute(g_stmt)).scalar_one_or_none()
        if not goal:
            raise NotFoundError("Active career goal not found for this student.")

        # Parse required skill UUIDs
        required_uuids: List[uuid.UUID] = []
        for s_str in goal.required_skill_ids:
            try:
                required_uuids.append(uuid.UUID(s_str))
            except (ValueError, TypeError):
                continue

        # 2. Fetch Skill definitions
        skills_by_id: Dict[uuid.UUID, Skill] = {}
        if required_uuids:
            s_stmt = select(Skill).where(
                and_(
                    Skill.id.in_(required_uuids),
                    Skill.institution_id == institution_id,
                )
            )
            s_res = await self.session.execute(s_stmt)
            for skill in s_res.scalars().all():
                skills_by_id[skill.id] = skill

        # 3. Fetch Student Mastery Records
        mastery_by_skill_id: Dict[uuid.UUID, MasteryRecord] = {}
        if required_uuids:
            m_stmt = select(MasteryRecord).where(
                and_(
                    MasteryRecord.student_user_id == student_user_id,
                    MasteryRecord.institution_id == institution_id,
                    MasteryRecord.skill_id.in_(required_uuids),
                )
            )
            m_res = await self.session.execute(m_stmt)
            for m in m_res.scalars().all():
                mastery_by_skill_id[m.skill_id] = m

        # 4. Fetch Verified Project Skills for student
        p_stmt = (
            select(ProjectSkill.skill_id)
            .join(Project, Project.id == ProjectSkill.project_id)
            .where(
                and_(
                    Project.student_user_id == student_user_id,
                    Project.institution_id == institution_id,
                    Project.status == "VERIFIED",
                )
            )
        )
        p_res = await self.session.execute(p_stmt)
        verified_project_skills: List[uuid.UUID] = list(p_res.scalars().all())

        # 5. Evaluate using DeterministicReadinessEngine
        eval_result = DeterministicReadinessEngine.evaluate_career_readiness(
            target_role=goal.target_role,
            required_skill_ids=required_uuids,
            skills_by_id=skills_by_id,
            mastery_by_skill_id=mastery_by_skill_id,
            verified_project_skill_ids=verified_project_skills,
        )

        # 6. Upsert CareerReadiness record
        existing_stmt = select(CareerReadiness).where(
            and_(
                CareerReadiness.institution_id == institution_id,
                CareerReadiness.student_user_id == student_user_id,
                CareerReadiness.career_goal_id == goal.id,
            )
        )
        readiness = (await self.session.execute(existing_stmt)).scalar_one_or_none()

        now = utc_now()
        if readiness:
            readiness.target_role = goal.target_role
            readiness.readiness_score = eval_result["readiness_score"]
            readiness.matching_skills_count = eval_result["matching_skills_count"]
            readiness.total_required_skills = eval_result["total_required_skills"]
            readiness.target_gap_analysis = eval_result["target_gap_analysis"]
            readiness.rule_version = eval_result["calculation_provenance"]["rule_version"]
            readiness.calculated_at = now
            readiness.calculation_provenance = eval_result["calculation_provenance"]
        else:
            readiness = CareerReadiness(
                id=uuid.uuid4(),
                institution_id=institution_id,
                student_user_id=student_user_id,
                career_goal_id=goal.id,
                target_role=goal.target_role,
                readiness_score=eval_result["readiness_score"],
                matching_skills_count=eval_result["matching_skills_count"],
                total_required_skills=eval_result["total_required_skills"],
                target_gap_analysis=eval_result["target_gap_analysis"],
                rule_version=eval_result["calculation_provenance"]["rule_version"],
                calculated_at=now,
                calculation_provenance=eval_result["calculation_provenance"],
            )
            self.session.add(readiness)

        await self.session.commit()
        await self.session.refresh(readiness)
        return readiness

    # =========================================================================
    # 4. PLACEMENT OFFICER TALENT DISCOVERY & ANALYTICS
    # =========================================================================
    async def search_talent_pool(
        self,
        institution_id: uuid.UUID,
        min_readiness: Optional[float] = None,
        target_role: Optional[str] = None,
        skill_id: Optional[uuid.UUID] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Restricted talent discovery search for authorized Placement Officers."""
        stmt = (
            select(
                User.id.label("student_id"),
                User.first_name,
                User.last_name,
                User.email,
                CareerReadiness.readiness_score,
                CareerReadiness.target_role,
                CareerReadiness.matching_skills_count,
                CareerReadiness.total_required_skills,
                Portfolio.slug.label("portfolio_slug"),
                Portfolio.visibility.label("portfolio_visibility"),
                Portfolio.is_published.label("portfolio_published"),
            )
            .join(CareerReadiness, CareerReadiness.student_user_id == User.id)
            .outerjoin(Portfolio, and_(Portfolio.student_user_id == User.id, Portfolio.institution_id == institution_id))
            .where(User.institution_id == institution_id)
        )

        if min_readiness is not None:
            stmt = stmt.where(CareerReadiness.readiness_score >= min_readiness)

        if target_role:
            stmt = stmt.where(CareerReadiness.target_role.ilike(f"%{target_role.strip()}%"))

        if skill_id:
            # Subquery to filter students with verified mastery in this skill
            sub = select(MasteryRecord.student_user_id).where(
                and_(
                    MasteryRecord.institution_id == institution_id,
                    MasteryRecord.skill_id == skill_id,
                    MasteryRecord.mastery_score >= 0.70,
                )
            )
            stmt = stmt.where(User.id.in_(sub))

        stmt = stmt.order_by(CareerReadiness.readiness_score.desc()).limit(limit).offset(offset)
        res = await self.session.execute(stmt)

        results = []
        for row in res.all():
            results.append({
                "student_id": str(row.student_id),
                "full_name": f"{row.first_name} {row.last_name}",
                "email": row.email,
                "target_role": row.target_role,
                "readiness_score": round(row.readiness_score, 3),
                "matching_skills_count": row.matching_skills_count,
                "total_required_skills": row.total_required_skills,
                "portfolio_slug": row.portfolio_slug,
                "portfolio_accessible": bool(row.portfolio_published and row.portfolio_visibility in ["PUBLIC", "INSTITUTION"]),
            })
        return results

    async def get_placement_readiness_analytics(
        self,
        institution_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """Aggregated institutional career readiness distribution and deficit analytics."""
        stmt = select(CareerReadiness).where(CareerReadiness.institution_id == institution_id)
        records = list((await self.session.execute(stmt)).scalars().all())

        total_evaluated = len(records)
        if total_evaluated == 0:
            return {
                "total_evaluated_students": 0,
                "average_readiness_score": 0.0,
                "distribution": {
                    "high_readiness_90_plus": 0,
                    "proficient_70_89": 0,
                    "developing_40_69": 0,
                    "deficit_under_40": 0,
                },
                "top_target_roles": [],
            }

        scores = [r.readiness_score for r in records]
        avg_score = round(sum(scores) / total_evaluated, 3)

        high = sum(1 for s in scores if s >= 0.90)
        proficient = sum(1 for s in scores if 0.70 <= s < 0.90)
        developing = sum(1 for s in scores if 0.40 <= s < 0.70)
        deficit = sum(1 for s in scores if s < 0.40)

        # Count target roles
        role_counts: Dict[str, int] = {}
        for r in records:
            role_counts[r.target_role] = role_counts.get(r.target_role, 0) + 1

        top_roles = [
            {"role": k, "student_count": v}
            for k, v in sorted(role_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

        return {
            "total_evaluated_students": total_evaluated,
            "average_readiness_score": avg_score,
            "distribution": {
                "high_readiness_90_plus": high,
                "proficient_70_89": proficient,
                "developing_40_69": developing,
                "deficit_under_40": deficit,
            },
            "top_target_roles": top_roles,
        }
