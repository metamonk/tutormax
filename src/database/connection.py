"""
Database connection management for TutorMax.
Provides async SQLAlchemy engine and session management.
"""

from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.database.models import Base


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # PostgreSQL connection parameters
    postgres_user: str = "tutormax"
    postgres_password: str = "tutormax_dev"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "tutormax"

    # SQLAlchemy settings
    db_echo: bool = False  # Set to True for SQL query logging
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600

    @property
    def database_url(self) -> str:
        """Construct async PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def sync_database_url(self) -> str:
        """Construct sync PostgreSQL connection URL (for Alembic migrations)."""
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


# Global engine and session factory
_engine: Optional[AsyncEngine] = None
_async_session_factory: Optional[async_sessionmaker[AsyncSession]] = None
_settings: Optional[DatabaseSettings] = None


def get_settings() -> DatabaseSettings:
    """Get database settings (singleton)."""
    global _settings
    if _settings is None:
        _settings = DatabaseSettings()
    return _settings


def get_engine(echo: bool = False) -> AsyncEngine:
    """
    Get or create the async SQLAlchemy engine.

    Args:
        echo: Enable SQL query logging

    Returns:
        Async SQLAlchemy engine
    """
    global _engine

    if _engine is None:
        settings = get_settings()

        _engine = create_async_engine(
            settings.database_url,
            echo=echo or settings.db_echo,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_timeout=settings.db_pool_timeout,
            pool_recycle=settings.db_pool_recycle,
            pool_pre_ping=True,  # Verify connections before using
        )

    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Get or create the async session factory.

    Returns:
        Async session factory
    """
    global _async_session_factory

    if _async_session_factory is None:
        engine = get_engine()
        _async_session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,  # Don't expire objects after commit
            autoflush=False,  # Manual flush control
            autocommit=False,  # Manual commit control
        )

    return _async_session_factory


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get an async database session with automatic cleanup.

    Usage:
        async with get_session() as session:
            result = await session.execute(select(Tutor))
            tutors = result.scalars().all()

    Yields:
        Async database session
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db(drop_all: bool = False) -> None:
    """
    Initialize the database by creating all tables.

    Args:
        drop_all: If True, drop all tables before creating (WARNING: destructive)

    Note:
        In production, use Alembic migrations instead of this function.
    """
    engine = get_engine()

    async with engine.begin() as conn:
        if drop_all:
            print("WARNING: Dropping all database tables...")
            await conn.run_sync(Base.metadata.drop_all)

        print("Creating database tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("Database tables created successfully.")


async def close_db() -> None:
    """
    Close database connections and dispose of the engine.
    Call this during application shutdown.
    """
    global _engine, _async_session_factory

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_factory = None
        print("Database connections closed.")


# Dependency injection for FastAPI
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions.

    Usage in FastAPI routes:
        @app.get("/tutors")
        async def get_tutors(db: AsyncSession = Depends(get_db_session)):
            result = await db.execute(select(Tutor))
            return result.scalars().all()
    """
    async with get_session() as session:
        yield session
