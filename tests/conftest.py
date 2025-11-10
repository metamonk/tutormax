"""
Pytest configuration and fixtures for tests.
"""

import pytest
import pytest_asyncio
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from src.database.connection import get_settings


@pytest.fixture(scope="session")
def event_loop():
    """Override event loop fixture to use session scope."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def db_engine(event_loop):
    """Create async database engine for tests."""
    # Use the same database URL as the app
    settings = get_settings()
    database_url = settings.database_url

    engine = create_async_engine(
        database_url,
        poolclass=NullPool,  # No connection pooling for tests
        echo=False,
    )

    yield engine

    # Cleanup
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Create a fresh database session for each test."""
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()
