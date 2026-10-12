"""Dhruva.AI V2 — Database Engine & Async Session Management.

Manages SQLAlchemy 2.0 async engine, connection pool lifecycle,
and provides async session dependencies with automated transaction rollback.
"""

from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, StaticPool
from src.core.config import get_settings
from src.core.logging import logger


settings = get_settings()


def build_engine(database_url: str) -> AsyncEngine:
    """Build SQLAlchemy async engine configured for target database dialect."""
    if database_url.startswith("sqlite"):
        # SQLite async configuration
        connect_args = {"check_same_thread": False}
        if ":memory:" in database_url:
            return create_async_engine(
                database_url,
                connect_args=connect_args,
                poolclass=StaticPool,
                echo=settings.DATABASE_ECHO,
            )
        return create_async_engine(
            database_url,
            connect_args=connect_args,
            poolclass=NullPool,
            echo=settings.DATABASE_ECHO,
        )

    # PostgreSQL async configuration with connection pooling
    return create_async_engine(
        database_url,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_timeout=settings.DATABASE_POOL_TIMEOUT,
        pool_pre_ping=True,
        echo=settings.DATABASE_ECHO,
    )


# Primary application engine and session factory
engine: AsyncEngine = build_engine(settings.DATABASE_URL)
AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding managed async database session."""
    async with AsyncSessionFactory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def set_db_tenant_context(session: AsyncSession, institution_id: str) -> None:
    """Set PostgreSQL session variable `app.current_institution_id` for Row-Level Security (RLS)."""
    bind = session.bind
    if bind and bind.dialect.name == "postgresql":
        await session.execute(
            text("SET LOCAL app.current_institution_id = :tenant_id"),
            {"tenant_id": str(institution_id)},
        )
