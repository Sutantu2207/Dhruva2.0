"""Dhruva.AI V2 — Automated Database Schema Initialization & Foundational Seeder.

Ensures:
1. All PostgreSQL extensions ("uuid-ossp", "vector") and 54 tables exist.
2. Idempotent seeding of all foundational system roles and permissions.
3. Seeding of primary institution (IIT Bombay) and default personas:
   - superadmin@dhruva.ai (Super Admin)
   - admin@iitb.ac.in (Institution Admin)
   - hod.cse@iitb.ac.in (HOD)
   - prof.verma@iitb.ac.in (Faculty)
   - rahul.k@iitb.ac.in (Student)
   - placement@iitb.ac.in (Placement Officer)
   (Default password for all seeded accounts: SecurePass123!)
4. Seeding of Academic Hierarchy, Curriculums, Courses, Offerings, and Enrollments.
5. Seeding of Question Banks, Assessments, and Mastery Concepts.
"""

import logging
import os
from typing import Optional
import uuid
from datetime import date, datetime, timedelta, timezone
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

# Import all domain modules to register tables in Base.metadata
import src.domain.identity.models
import src.domain.audit.models
import src.domain.academic.models
import src.domain.curriculum.models
import src.domain.ingestion.models
import src.domain.assessment.models
import src.domain.mastery.models
import src.domain.placement.models
import src.domain.analytics.models
import src.domain.ai.models
import src.domain.college.models

from src.core.logging import logger
from src.core.security import hash_password
from src.domain.college.models import College, CollegeRequest
from src.infrastructure.coimbatore_colleges import COIMBATORE_COLLEGES
from src.domain.academic.models import (
    AcademicYear,
    Batch,
    Course,
    CourseOffering,
    Department,
    FacultyProfile,
    Program,
    Section,
    Semester,
    StudentEnrollment,
    StudentProfile,
    TeachingAssignment,
)
from src.domain.assessment.models import (
    Assessment,
    AssessmentQuestion,
    Question,
    QuestionBank,
)
from src.domain.curriculum.models import (
    Curriculum,
    LearningResource,
    Lesson,
    Module,
)
from src.domain.identity.models import Institution, Role, User, UserRole
from src.domain.identity.roles import SystemRole, get_permissions_for_role
from src.domain.mastery.models import (
    Concept,
    ConceptSkill,
    Skill,
)
from src.infrastructure.persistence.postgres.base import Base, utc_now

DEFAULT_SEED_PASSWORD = os.environ.get("DEFAULT_SEED_PASSWORD", "SecurePass123!")


async def init_schema(engine: AsyncEngine) -> None:
    """Safely initialize schema tables on the target database."""
    async with engine.begin() as conn:
        if conn.dialect.name == "postgresql":
            try:
                await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
            except Exception as e:
                logger.warning(f"Note: uuid-ossp extension check: {e}")
            try:
                await conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector;'))
            except Exception as e:
                logger.warning(f"Note: vector extension check: {e}")

        # Create all tables defined across the domain models
        await conn.run_sync(Base.metadata.create_all)

        # Ensure college_id column exists on users and students for SQLite and PostgreSQL
        if conn.dialect.name == "sqlite":
            try:
                await conn.execute(text("ALTER TABLE users ADD COLUMN college_id CHAR(32);"))
            except Exception:
                pass
            try:
                await conn.execute(text("ALTER TABLE students ADD COLUMN college_id CHAR(32);"))
            except Exception:
                pass
        elif conn.dialect.name == "postgresql":
            try:
                await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS college_id UUID REFERENCES colleges(id) ON DELETE SET NULL;"))
            except Exception:
                pass
            try:
                await conn.execute(text("ALTER TABLE students ADD COLUMN IF NOT EXISTS college_id UUID REFERENCES colleges(id) ON DELETE SET NULL;"))
            except Exception:
                pass
    logger.info("Database schema verification and table creation complete.")


async def seed_all_data(session: AsyncSession) -> dict:
    """Idempotently seed all foundational data into the database."""
    # 1. System Roles
    logger.info("Seeding system roles...")
    role_map = {}
    for sys_role in SystemRole:
        stmt = select(Role).where(Role.code == sys_role.value)
        existing_role = (await session.execute(stmt)).scalar_one_or_none()
        if not existing_role:
            role = Role(
                id=uuid.uuid4(),
                institution_id=None,
                name=sys_role.value.replace("_", " ").title(),
                code=sys_role.value,
                description=f"System role for {sys_role.value}",
                permissions=list(get_permissions_for_role(sys_role)),
                is_system_role=True,
            )
            session.add(role)
            role_map[sys_role.value] = role
        else:
            role_map[sys_role.value] = existing_role
    await session.flush()

    # 2. Primary Institution
    logger.info("Seeding institution...")
    inst_stmt = select(Institution).where(Institution.slug == "iit-bombay")
    inst = (await session.execute(inst_stmt)).scalar_one_or_none()
    if not inst:
        inst = Institution(
            id=uuid.uuid4(),
            slug="iit-bombay",
            legal_name="Indian Institute of Technology Bombay",
            domain="iitb.ac.in",
            status="ACTIVE",
            settings={"mfa_required": False, "theme": "cosmic"},
        )
        session.add(inst)
        await session.flush()

    # 3. Comprehensive Coimbatore Colleges Directory
    logger.info("Seeding comprehensive Coimbatore colleges directory...")
    college_map = {}
    for c_data in COIMBATORE_COLLEGES:
        c_stmt = select(College).where(College.name == c_data["name"])
        existing_col = (await session.execute(c_stmt)).scalar_one_or_none()
        if not existing_col:
            col = College(
                id=uuid.uuid4(),
                name=c_data["name"],
                code=c_data.get("code"),
                institution_type=c_data["institution_type"],
                affiliated_university=c_data.get("affiliated_university"),
                location=c_data["location"],
                district=c_data.get("district", "Coimbatore"),
                state=c_data.get("state", "Tamil Nadu"),
                website=c_data.get("website"),
                accreditation=c_data.get("accreditation"),
                status=c_data.get("status", "ACTIVE"),
            )
            session.add(col)
            college_map[c_data["name"]] = col
        else:
            existing_col.code = c_data.get("code")
            existing_col.institution_type = c_data["institution_type"]
            existing_col.affiliated_university = c_data.get("affiliated_university")
            existing_col.location = c_data["location"]
            existing_col.website = c_data.get("website")
            existing_col.accreditation = c_data.get("accreditation")
            college_map[c_data["name"]] = existing_col
    await session.flush()
    logger.info(f"Seeded {len(college_map)} accredited colleges across Coimbatore district.")

    psg_tech = college_map.get("PSG College of Technology")
    cit_cbe = college_map.get("Coimbatore Institute of Technology (CIT)")
    kct_cbe = college_map.get("Kumaraguru College of Technology (KCT)")

    # 4. Core Personas with Dedicated, Role-Segregated Permissions
    logger.info("Seeding users and role mappings with dedicated permissions per persona...")
    hashed_pwd = hash_password(DEFAULT_SEED_PASSWORD)

    users_spec = [
        {
            "email": "superadmin@dhruva.ai",
            "first_name": "Super",
            "last_name": "Administrator",
            "inst_id": inst.id,
            "roles": [
                SystemRole.SUPER_ADMIN.value,
                SystemRole.INSTITUTION_ADMIN.value,
                SystemRole.HOD.value,
                SystemRole.FACULTY.value,
                SystemRole.STUDENT.value,
                SystemRole.PLACEMENT_OFFICER.value,
            ],
        },
        {
            "email": "sutantu07@gmail.com",
            "first_name": "Sutantu",
            "last_name": "Admin",
            "inst_id": inst.id,
            "roles": [
                SystemRole.SUPER_ADMIN.value,
                SystemRole.INSTITUTION_ADMIN.value,
                SystemRole.HOD.value,
                SystemRole.FACULTY.value,
                SystemRole.STUDENT.value,
                SystemRole.PLACEMENT_OFFICER.value,
            ],
        },
        {
            "email": "admin@iitb.ac.in",
            "first_name": "Rajesh",
            "last_name": "Sharma",
            "inst_id": inst.id,
            "roles": [SystemRole.INSTITUTION_ADMIN.value],
        },
        {
            "email": "admin@dhruva.ai",
            "first_name": "Rajesh",
            "last_name": "Sharma",
            "inst_id": inst.id,
            "roles": [SystemRole.INSTITUTION_ADMIN.value],
        },
        {
            "email": "hod.cse@iitb.ac.in",
            "first_name": "Anita",
            "last_name": "Desai",
            "inst_id": inst.id,
            "roles": [SystemRole.HOD.value],
        },
        {
            "email": "hod@dhruva.ai",
            "first_name": "Anita",
            "last_name": "Desai",
            "inst_id": inst.id,
            "roles": [SystemRole.HOD.value],
        },
        {
            "email": "prof.verma@iitb.ac.in",
            "first_name": "Vikram",
            "last_name": "Verma",
            "inst_id": inst.id,
            "roles": [SystemRole.FACULTY.value],
        },
        {
            "email": "faculty@dhruva.ai",
            "first_name": "Vikram",
            "last_name": "Verma",
            "inst_id": inst.id,
            "roles": [SystemRole.FACULTY.value],
        },
        {
            "email": "rahul.k@iitb.ac.in",
            "first_name": "Rahul",
            "last_name": "Kumar",
            "inst_id": inst.id,
            "roles": [SystemRole.STUDENT.value],
        },
        {
            "email": "student@dhruva.ai",
            "first_name": "Rahul",
            "last_name": "Kumar",
            "inst_id": inst.id,
            "roles": [SystemRole.STUDENT.value],
        },
        {
            "email": "placement@iitb.ac.in",
            "first_name": "Sneha",
            "last_name": "Kapoor",
            "inst_id": inst.id,
            "roles": [SystemRole.PLACEMENT_OFFICER.value],
        },
        {
            "email": "placement@dhruva.ai",
            "first_name": "Sneha",
            "last_name": "Kapoor",
            "inst_id": inst.id,
            "roles": [SystemRole.PLACEMENT_OFFICER.value],
        },
    ]

    all_roles = list(role_map.values())
    user_map = {}

    for spec in users_spec:
        user_college_id = None
        if "rahul" in spec["email"] or "student" in spec["email"] or "verma" in spec["email"] or "faculty" in spec["email"]:
            user_college_id = psg_tech.id if psg_tech else None
        elif "hod" in spec["email"]:
            user_college_id = cit_cbe.id if cit_cbe else None
        elif "admin" in spec["email"] or "placement" in spec["email"]:
            user_college_id = kct_cbe.id if kct_cbe else None

        u_stmt = select(User).where(User.email == spec["email"])
        user = (await session.execute(u_stmt)).scalar_one_or_none()
        if not user:
            user = User(
                id=uuid.uuid4(),
                institution_id=spec["inst_id"],
                college_id=user_college_id,
                email=spec["email"],
                password_hash=hashed_pwd,
                first_name=spec["first_name"],
                last_name=spec["last_name"],
                status="ACTIVE",
            )
            session.add(user)
            await session.flush()
        else:
            user.institution_id = spec["inst_id"]
            user.college_id = user_college_id
            user.password_hash = hashed_pwd
            user.status = "ACTIVE"
            await session.flush()

        # Enforce exact role mapping for this persona:
        target_role_codes = set(spec.get("roles", [SystemRole.STUDENT.value]))

        # Remove existing roles that do not belong to this persona
        existing_urs_stmt = select(UserRole).where(UserRole.user_id == user.id)
        existing_urs = (await session.execute(existing_urs_stmt)).scalars().all()
        for eur in existing_urs:
            r_stmt = select(Role).where(Role.id == eur.role_id)
            r_obj = (await session.execute(r_stmt)).scalar_one_or_none()
            if not r_obj or r_obj.code not in target_role_codes:
                await session.delete(eur)
        await session.flush()

        # Add designated roles
        for r_code in target_role_codes:
            role_obj = role_map.get(r_code)
            if not role_obj:
                continue
            ur_stmt = select(UserRole).where(
                UserRole.user_id == user.id,
                UserRole.role_id == role_obj.id,
            )
            existing_ur = (await session.execute(ur_stmt)).scalar_one_or_none()
            if not existing_ur:
                ur = UserRole(
                    id=uuid.uuid4(),
                    user_id=user.id,
                    role_id=role_obj.id,
                    institution_id=spec["inst_id"],
                )
                session.add(ur)

        user_map[spec["email"]] = user

    await session.flush()

    # 4. Academic Department & Program
    logger.info("Seeding academic hierarchy...")
    dept_stmt = select(Department).where(Department.institution_id == inst.id, Department.code == "CSE")
    dept = (await session.execute(dept_stmt)).scalar_one_or_none()
    if not dept:
        dept = Department(
            id=uuid.uuid4(),
            institution_id=inst.id,
            code="CSE",
            name="Computer Science and Engineering",
            hod_user_id=user_map["hod.cse@iitb.ac.in"].id,
            status="ACTIVE",
        )
        session.add(dept)
        await session.flush()

    prog_stmt = select(Program).where(Program.institution_id == inst.id, Program.code == "BTECH_CSE")
    prog = (await session.execute(prog_stmt)).scalar_one_or_none()
    if not prog:
        prog = Program(
            id=uuid.uuid4(),
            institution_id=inst.id,
            department_id=dept.id,
            code="BTECH_CSE",
            name="Bachelor of Technology in Computer Science and Engineering",
            degree_level="UNDERGRADUATE",
            total_semesters=8,
            status="ACTIVE",
        )
        session.add(prog)
        await session.flush()

    # 5. Academic Year & Semester
    ay_stmt = select(AcademicYear).where(AcademicYear.institution_id == inst.id, AcademicYear.code == "AY2026-27")
    ay = (await session.execute(ay_stmt)).scalar_one_or_none()
    if not ay:
        ay = AcademicYear(
            id=uuid.uuid4(),
            institution_id=inst.id,
            code="AY2026-27",
            name="2026-2027",
            start_date=date(2026, 7, 1),
            end_date=date(2027, 6, 30),
            is_current=True,
        )
        session.add(ay)
        await session.flush()

    sem_stmt = select(Semester).where(Semester.academic_year_id == ay.id, Semester.term_number == 1)
    sem = (await session.execute(sem_stmt)).scalar_one_or_none()
    if not sem:
        sem = Semester(
            id=uuid.uuid4(),
            institution_id=inst.id,
            academic_year_id=ay.id,
            term_number=1,
            name="Autumn 2026",
            start_date=date(2026, 7, 15),
            end_date=date(2026, 12, 15),
            status="ACTIVE",
        )
        session.add(sem)
        await session.flush()

    batch_stmt = select(Batch).where(Batch.institution_id == inst.id, Batch.name == "Class of 2026-2030")
    batch = (await session.execute(batch_stmt)).scalar_one_or_none()
    if not batch:
        batch = Batch(
            id=uuid.uuid4(),
            institution_id=inst.id,
            program_id=prog.id,
            name="Class of 2026-2030",
            admission_year=2026,
            graduation_year=2030,
        )
        session.add(batch)
        await session.flush()

    sec_stmt = select(Section).where(Section.batch_id == batch.id, Section.name == "Section A")
    sec = (await session.execute(sec_stmt)).scalar_one_or_none()
    if not sec:
        sec = Section(
            id=uuid.uuid4(),
            institution_id=inst.id,
            batch_id=batch.id,
            name="Section A",
            capacity=60,
        )
        session.add(sec)
        await session.flush()

    # 6. Master Course Catalog & Offering
    course_stmt = select(Course).where(Course.institution_id == inst.id, Course.code == "CS101")
    course = (await session.execute(course_stmt)).scalar_one_or_none()
    if not course:
        course = Course(
            id=uuid.uuid4(),
            institution_id=inst.id,
            department_id=dept.id,
            code="CS101",
            title="Data Structures and Algorithms",
            credits=4.0,
            course_type="THEORY",
        )
        session.add(course)
        await session.flush()

    offering_stmt = select(CourseOffering).where(
        CourseOffering.institution_id == inst.id,
        CourseOffering.course_id == course.id,
        CourseOffering.semester_id == sem.id,
    )
    offering = (await session.execute(offering_stmt)).scalar_one_or_none()
    if not offering:
        offering = CourseOffering(
            id=uuid.uuid4(),
            institution_id=inst.id,
            course_id=course.id,
            academic_year_id=ay.id,
            semester_id=sem.id,
            section_id=sec.id,
            status="ACTIVE",
        )
        session.add(offering)
        await session.flush()

    # 7. Faculty & Student Profiles & Enrollments
    for fac_email in ["prof.verma@iitb.ac.in", "faculty@dhruva.ai"]:
        fac_user = user_map.get(fac_email)
        if not fac_user:
            continue
        fac_stmt = select(FacultyProfile).where(FacultyProfile.user_id == fac_user.id)
        fac_profile = (await session.execute(fac_stmt)).scalar_one_or_none()
        if not fac_profile:
            fac_profile = FacultyProfile(
                id=uuid.uuid4(),
                user_id=fac_user.id,
                institution_id=inst.id,
                department_id=dept.id,
                designation="Associate Professor",
                employee_id=f"FAC-{str(fac_user.id)[:6].upper()}",
                status="ACTIVE",
            )
            session.add(fac_profile)

        ta_stmt = select(TeachingAssignment).where(
            TeachingAssignment.course_offering_id == offering.id,
            TeachingAssignment.faculty_user_id == fac_user.id,
        )
        if not (await session.execute(ta_stmt)).scalar_one_or_none():
            ta = TeachingAssignment(
                id=uuid.uuid4(),
                course_offering_id=offering.id,
                faculty_user_id=fac_user.id,
                role_type="PRIMARY_INSTRUCTOR",
            )
            session.add(ta)

    for idx, stud_email in enumerate(["rahul.k@iitb.ac.in", "student@dhruva.ai"], start=1):
        student_user = user_map.get(stud_email)
        if not student_user:
            continue
        stud_stmt = select(StudentProfile).where(StudentProfile.user_id == student_user.id)
        stud_profile = (await session.execute(stud_stmt)).scalar_one_or_none()
        if not stud_profile:
            stud_profile = StudentProfile(
                id=uuid.uuid4(),
                user_id=student_user.id,
                institution_id=inst.id,
                college_id=psg_tech.id if psg_tech else None,
                department_id=dept.id,
                program_id=prog.id,
                batch_id=batch.id,
                section_id=sec.id,
                roll_number=f"26CSE00{idx}",
                academic_status="ACTIVE",
            )
            session.add(stud_profile)
        else:
            stud_profile.college_id = psg_tech.id if psg_tech else None

        enr_stmt = select(StudentEnrollment).where(
            StudentEnrollment.course_offering_id == offering.id,
            StudentEnrollment.student_user_id == student_user.id,
        )
        if not (await session.execute(enr_stmt)).scalar_one_or_none():
            enr = StudentEnrollment(
                id=uuid.uuid4(),
                institution_id=inst.id,
                course_offering_id=offering.id,
                student_user_id=student_user.id,
                enrollment_status="ENROLLED",
            )
            session.add(enr)
    await session.flush()

    # 8. Curriculum, Modules & Lessons (for AI grounded tutoring)
    logger.info("Seeding curriculum & syllabus content...")
    curr_stmt = select(Curriculum).where(Curriculum.course_id == course.id)
    curriculum = (await session.execute(curr_stmt)).scalar_one_or_none()
    if not curriculum:
        curriculum = Curriculum(
            id=uuid.uuid4(),
            institution_id=inst.id,
            course_id=course.id,
            program_id=prog.id,
            academic_year_id=ay.id,
            title="CS101 Comprehensive Curriculum",
            version=1,
            status="ACTIVE",
            learning_objectives=[
                "Master fundamental data structures: arrays, linked lists, trees, graphs",
                "Analyze time and space complexity with asymptotic Big-O notation",
                "Implement shortest-path algorithms and divide-and-conquer sorting",
            ],
        )
        session.add(curriculum)
        await session.flush()

        # Module 1: Graph Algorithms
        mod1 = Module(
            id=uuid.uuid4(),
            institution_id=inst.id,
            curriculum_id=curriculum.id,
            title="Module 1: Graph Representations & Shortest Path",
            sequence_order=1,
            description="Adjacency lists, priority queues, and greedy shortest path traversal.",
        )
        session.add(mod1)
        await session.flush()

        lesson1 = Lesson(
            id=uuid.uuid4(),
            institution_id=inst.id,
            module_id=mod1.id,
            title="Dijkstra's Algorithm",
            sequence_order=1,
            content_markdown=(
                "Dijkstra's algorithm solves the single-source shortest path problem on a weighted, "
                "directed graph with non-negative edge weights. Using a binary min-heap priority queue, "
                "it achieves O((V + E) log V) time complexity and O(V) auxiliary space. "
                "The core invariant relies on greedy edge relaxation: if dist[u] + w(u, v) < dist[v], "
                "update dist[v] = dist[u] + w(u, v)."
            ),
        )
        session.add(lesson1)

        # Module 2: Sorting Algorithms
        mod2 = Module(
            id=uuid.uuid4(),
            institution_id=inst.id,
            curriculum_id=curriculum.id,
            title="Module 2: Divide and Conquer Sorting",
            sequence_order=2,
            description="Partitioning strategies and randomized algorithmic paradigms.",
        )
        session.add(mod2)
        await session.flush()

        lesson2 = Lesson(
            id=uuid.uuid4(),
            institution_id=inst.id,
            module_id=mod2.id,
            title="Quicksort Partitioning",
            sequence_order=1,
            content_markdown=(
                "Quicksort is an in-place, divide-and-conquer sorting algorithm. It selects a pivot "
                "element and partitions the array such that elements smaller than the pivot appear before it "
                "and larger elements appear after it. Average time complexity is O(n log n), while worst-case "
                "is O(n^2) when poor pivot selection occurs without randomized median sampling."
            ),
        )
        session.add(lesson2)
        await session.flush()

    # 9. Mastery Concepts & Skills
    logger.info("Seeding mastery & skills...")
    c_stmt = select(Concept).where(Concept.institution_id == inst.id, Concept.code == "CONC-DIJKSTRA")
    concept1 = (await session.execute(c_stmt)).scalar_one_or_none()
    if not concept1:
        concept1 = Concept(
            id=uuid.uuid4(),
            institution_id=inst.id,
            department_id=dept.id,
            course_id=course.id,
            code="CONC-DIJKSTRA",
            name="Dijkstra Shortest Path",
            description="Greedy single-source shortest path relaxation with min-priority queues",
            bloom_level="ANALYZE",
        )
        session.add(concept1)

    skill_stmt = select(Skill).where(Skill.institution_id == inst.id, Skill.code == "SKILL-GRAPHS")
    skill1 = (await session.execute(skill_stmt)).scalar_one_or_none()
    if not skill1:
        skill1 = Skill(
            id=uuid.uuid4(),
            institution_id=inst.id,
            code="SKILL-GRAPHS",
            name="Graph Optimization & Shortest Path",
            category="TECHNICAL",
            description="Algorithmic graph modeling and shortest-path optimization.",
        )
        session.add(skill1)
        await session.flush()

        cs = ConceptSkill(
            concept_id=concept1.id,
            skill_id=skill1.id,
            institution_id=inst.id,
            weight=1.0,
        )
        session.add(cs)

    # 10. Question Bank & Assessment
    logger.info("Seeding question bank & assessments...")
    qb_stmt = select(QuestionBank).where(QuestionBank.institution_id == inst.id, QuestionBank.title == "CS101 Master Question Bank")
    qb = (await session.execute(qb_stmt)).scalar_one_or_none()
    if not qb:
        qb = QuestionBank(
            id=uuid.uuid4(),
            institution_id=inst.id,
            department_id=dept.id,
            course_id=course.id,
            title="CS101 Master Question Bank",
            description="Core syllabus question repository with verified deterministic rubrics.",
            created_by=fac_user.id,
        )
        session.add(qb)
        await session.flush()

        q1 = Question(
            id=uuid.uuid4(),
            institution_id=inst.id,
            question_bank_id=qb.id,
            prompt_text="What is the asymptotic time complexity of Dijkstra's algorithm implemented with a binary min-heap?",
            question_type="MCQ",
            difficulty="MEDIUM",
            points=2.5,
            options=[
                {"id": "opt_a", "text": "O((V + E) log V)", "is_correct": True},
                {"id": "opt_b", "text": "O(V^2)", "is_correct": False},
                {"id": "opt_c", "text": "O(V + E)", "is_correct": False},
                {"id": "opt_d", "text": "O(log V)", "is_correct": False},
            ],
            answer_key={"correct_option_id": "opt_a"},
            explanation="With a binary min-heap, each vertex extraction takes O(log V) and edge relaxations take O(E log V), yielding O((V + E) log V).",
        )
        session.add(q1)
        await session.flush()

        # Seed sample Published Assessment
        now = utc_now()
        assessment = Assessment(
            id=uuid.uuid4(),
            institution_id=inst.id,
            course_offering_id=offering.id,
            title="Quiz 1: Shortest Path & Graph Traversal",
            instructions="Answer all multiple choice questions. Zero penalty for unanswered questions.",
            assessment_type="QUIZ",
            status="PUBLISHED",
            publish_at=now - timedelta(hours=1),
            due_at=now + timedelta(days=7),
            duration_minutes=30,
            total_points=2.5,
            passing_percentage=50.0,
            max_attempts=2,
            created_by=fac_user.id,
        )
        session.add(assessment)
        await session.flush()

        aq = AssessmentQuestion(
            id=uuid.uuid4(),
            assessment_id=assessment.id,
            question_id=q1.id,
            points=2.5,
            sort_order=1,
        )
        session.add(aq)

    await session.commit()
    logger.info("Foundational data seeding completed successfully!")
    return {
        "institution": inst.slug,
        "superadmin": "superadmin@dhruva.ai",
        "faculty": "prof.verma@iitb.ac.in",
        "student": "rahul.k@iitb.ac.in",
        "course": "CS101",
    }


async def auto_initialize_and_seed() -> None:
    """Safe startup hook verifying schema and ensuring foundational seed data & permissions."""
    from src.infrastructure.persistence.postgres.database import engine, AsyncSessionFactory

    try:
        await init_schema(engine)
        async with AsyncSessionFactory() as session:
            logger.info("Verifying and syncing foundational seed data & full permissions...")
            await seed_all_data(session)
    except Exception as e:
        logger.error(f"Auto-initialize and seed encountered error: {e}", exc_info=True)


_is_initialized = False


async def ensure_db_initialized(session: Optional[AsyncSession] = None) -> None:
    """Ensure schema tables and foundational seeds exist even if ASGI lifespan was bypassed by serverless adapters."""
    global _is_initialized
    if _is_initialized:
        return
    try:
        from src.infrastructure.persistence.postgres.database import engine, AsyncSessionFactory
        await init_schema(engine)
        if session is not None:
            await seed_all_data(session)
        else:
            async with AsyncSessionFactory() as init_session:
                await seed_all_data(init_session)
        _is_initialized = True
    except Exception as e:
        logger.warning(f"ensure_db_initialized notice: {e}")
