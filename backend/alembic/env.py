import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# Import application configuration and models
from src.core.config import get_settings
from src.infrastructure.persistence.postgres.base import Base
import src.domain.identity.models  # registers Institution, User, Role, UserRole, RefreshToken
import src.domain.audit.models     # registers AuditLog
import src.domain.academic.models  # registers Departments, Programs, AcademicYears, Semesters, Batches, Sections, Courses, Offerings, Enrollments, Students, Faculty
import src.domain.curriculum.models  # registers Curriculums, Modules, Lessons, LearningResources
import src.domain.ingestion.models   # registers DataSource, ImportBatch, StagedRecord, ValidationResult, Approval, ProvenanceRecord
import src.domain.assessment.models  # registers QuestionBank, Question, Assessment, AssessmentQuestion, AssessmentSubmission, AssessmentResult
import src.domain.mastery.models     # registers Concept, Skill, ConceptSkill, MasteryRecord, LearningEvidence, ReviewSchedule
import src.domain.placement.models   # registers Project, ProjectSkill, ProjectEvidence, Portfolio, CareerGoal, CareerReadiness
import src.domain.analytics.models   # registers Intervention, Notification, AnalyticsRollup
import src.domain.ai.models          # registers AIConversation, AIMessage, AIAuditLog

config = context.config
settings = get_settings()

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Override sqlalchemy.url from app settings (ensuring asyncpg driver is specified for PostgreSQL)
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
config.set_main_option("sqlalchemy.url", db_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
