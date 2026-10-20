"""Dhruva.AI V2 — Test Configuration & Fixtures.

Provides an isolated in-memory SQLite test database with aiosqlite,
FastAPI test client with dependency overrides, and reusable factories.
"""

import os
import uuid
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# Ensure test environment settings
os.environ["ENVIRONMENT"] = "development"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-32-bytes-minimum-length-for-security"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-32-bytes-minimum-length-security"
os.environ["DEBUG"] = "true"

from src.core.config import get_settings
from src.core.security import hash_password
from src.domain.identity.models import Institution, Role, User, UserRole
from src.domain.identity.roles import SystemRole, get_permissions_for_role
import src.domain.academic.models
import src.domain.curriculum.models
import src.domain.ingestion.models
import src.domain.assessment.models
import src.domain.mastery.models
import src.domain.placement.models
import src.domain.analytics.models
import src.domain.ai.models
from src.infrastructure.persistence.postgres.base import Base
from src.infrastructure.persistence.postgres.database import get_db_session
from src.main import app

# Test Async Engine
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_database() -> AsyncGenerator[None, None]:
    """Create all database tables before test and drop afterwards."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a fresh isolated async database session."""
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """FastAPI async test client with overridden database session."""
    async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seed_data(db_session: AsyncSession):
    """Seed foundational test institutions, roles, and users."""
    # 1. Institutions
    inst1 = Institution(
        id=uuid.uuid4(),
        slug="iit-bombay",
        legal_name="Indian Institute of Technology Bombay",
        domain="iitb.ac.in",
        status="ACTIVE",
        settings={"mfa_required": False},
    )
    inst2 = Institution(
        id=uuid.uuid4(),
        slug="bits-pilani",
        legal_name="BITS Pilani",
        domain="pilani.bits-pilani.ac.in",
        status="ACTIVE",
        settings={"mfa_required": False},
    )
    db_session.add_all([inst1, inst2])
    await db_session.flush()

    # 2. Roles for Institution 1
    roles = []
    for sys_role in SystemRole:
        role = Role(
            id=uuid.uuid4(),
            institution_id=inst1.id if sys_role != SystemRole.SUPER_ADMIN else None,
            name=sys_role.value.replace("_", " ").title(),
            code=sys_role.value,
            description=f"System role for {sys_role.value}",
            permissions=list(get_permissions_for_role(sys_role)),
            is_system_role=True,
        )
        roles.append(role)
        db_session.add(role)
    await db_session.flush()

    role_map = {r.code: r for r in roles}

    # 3. Users in Institution 1
    default_password = hash_password("SecurePass123!")

    ur_super = UserRole(id=uuid.uuid4(), role=role_map[SystemRole.SUPER_ADMIN.value], institution_id=None)
    super_admin = User(
        id=uuid.uuid4(),
        institution_id=None,
        email="superadmin@dhruva.ai",
        password_hash=default_password,
        first_name="Super",
        last_name="Administrator",
        status="ACTIVE",
        user_roles=[ur_super],
    )

    ur_admin = UserRole(id=uuid.uuid4(), role=role_map[SystemRole.INSTITUTION_ADMIN.value], institution_id=inst1.id)
    inst_admin = User(
        id=uuid.uuid4(),
        institution_id=inst1.id,
        email="admin@iitb.ac.in",
        password_hash=default_password,
        first_name="Rajesh",
        last_name="Sharma",
        status="ACTIVE",
        user_roles=[ur_admin],
    )

    ur_hod = UserRole(id=uuid.uuid4(), role=role_map[SystemRole.HOD.value], institution_id=inst1.id)
    hod_user = User(
        id=uuid.uuid4(),
        institution_id=inst1.id,
        email="hod.cse@iitb.ac.in",
        password_hash=default_password,
        first_name="Anita",
        last_name="Desai",
        status="ACTIVE",
        user_roles=[ur_hod],
    )

    ur_faculty = UserRole(id=uuid.uuid4(), role=role_map[SystemRole.FACULTY.value], institution_id=inst1.id)
    faculty_user = User(
        id=uuid.uuid4(),
        institution_id=inst1.id,
        email="prof.verma@iitb.ac.in",
        password_hash=default_password,
        first_name="Vikram",
        last_name="Verma",
        status="ACTIVE",
        user_roles=[ur_faculty],
    )

    ur_student = UserRole(id=uuid.uuid4(), role=role_map[SystemRole.STUDENT.value], institution_id=inst1.id)
    student_user = User(
        id=uuid.uuid4(),
        institution_id=inst1.id,
        email="rahul.k@iitb.ac.in",
        password_hash=default_password,
        first_name="Rahul",
        last_name="Kumar",
        status="ACTIVE",
        user_roles=[ur_student],
    )

    # User in Institution 2 (for cross-tenant tests)
    inst2_user = User(
        id=uuid.uuid4(),
        institution_id=inst2.id,
        email="student@bits-pilani.ac.in",
        password_hash=default_password,
        first_name="Arjun",
        last_name="Patel",
        status="ACTIVE",
        user_roles=[],
    )

    db_session.add_all([super_admin, inst_admin, hod_user, faculty_user, student_user, inst2_user])
    await db_session.commit()

    return {
        "inst1": inst1,
        "inst2": inst2,
        "super_admin": super_admin,
        "inst_admin": inst_admin,
        "hod_user": hod_user,
        "faculty_user": faculty_user,
        "student_user": student_user,
        "inst2_user": inst2_user,
        "role_map": role_map,
    }
