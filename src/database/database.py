"""
Database configuration and async session management.
Provides database dependencies for FastAPI-Users and the application.
"""

from typing import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from ..api.config import settings


# Construct async database URL from settings
# Format: postgresql+asyncpg://user:password@host:port/database
DATABASE_URL = f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=settings.db_echo,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_recycle=settings.db_pool_recycle,
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.

    Usage:
        @app.get("/items")
        async def get_items(session: AsyncSession = Depends(get_async_session)):
            result = await session.execute(select(Item))
            return result.scalars().all()

    Yields:
        AsyncSession: Database session
    """
    async with async_session_maker() as session:
        yield session


# Alias for backward compatibility
get_db = get_async_session


async def create_db_and_tables():
    """
    Create all database tables.
    Only use this for initial setup or testing.
    For production, use Alembic migrations.
    """
    from .models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """
    Close database engine.
    Call this on application shutdown.
    """
    await engine.dispose()


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for getting database sessions outside of FastAPI dependencies.

    Usage:
        async with get_db_session() as session:
            result = await session.execute(select(Item))
            return result.scalars().all()

    Yields:
        AsyncSession: Database session
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
