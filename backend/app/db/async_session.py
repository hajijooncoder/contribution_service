"""
Async SQLAlchemy database session management for MAHOUNN Contribution Service.
Uses SQLAlchemy 2.0 async API with asyncpg driver for PostgreSQL.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base
from app.config import settings

# Convert sync DATABASE_URL to async if needed
def get_async_database_url() -> str:
    url = settings.DATABASE_URL
    if url.startswith("sqlite:///"):
        # SQLite with aiosqlite
        return url.replace("sqlite:///", "sqlite+aiosqlite:///")
    elif url.startswith("postgresql://"):
        # PostgreSQL with asyncpg
        return url.replace("postgresql://", "postgresql+asyncpg://")
    return url

ASYNC_DATABASE_URL = get_async_database_url()

# Create async engine
engine: AsyncEngine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_pre_ping=True,
    echo=settings.ENVIRONMENT == "development",
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

Base = declarative_base()

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for async database sessions."""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

@asynccontextmanager
async def get_async_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for async database sessions (for background tasks)."""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_async_db() -> None:
    """Initialize database tables (async version)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def close_async_db() -> None:
    """Close database connections."""
    await engine.dispose()