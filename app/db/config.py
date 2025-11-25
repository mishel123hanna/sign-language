from contextlib import asynccontextmanager
from typing import AsyncGenerator
from uuid import uuid4

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.settings import settings

DATABASE_URL = (
    f"postgresql+asyncpg://{settings.SUPABASE_USER}:{settings.SUPABASE_PASSWORD}@"
    f"{settings.SUPABASE_HOST}:{settings.SUPABASE_PORT}/{settings.SUPABASE_DB_NAME}"
)

async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    # PgBouncer already does pooling; avoid double pooling
    poolclass=NullPool,
    connect_args={
        "ssl": "require",  # or an ssl.SSLContext if you prefer
        # Disable asyncpg's statement cache (recommended with PgBouncer)
        "statement_cache_size": 0,
        # Disable SQLAlchemy's asyncpg prepared-statement cache
        "prepared_statement_cache_size": 0,
        # Make every prepared statement name unique to avoid collisions in PgBouncer
        "prepared_statement_name_func": lambda: f"__asyncpg_{uuid4()}__",
        "server_settings": {
            "application_name": "sign_language_app",
        },
    },
    # you can drop execution_options here; prepared cache is handled via connect_args
)


# Session factory
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@asynccontextmanager
async def init_db(app: FastAPI):
    # Initialize database tables
    if settings.ENVIRONMENT == "development":
        async with async_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    try:
        yield  # App runs here
    finally:
        # Cleanup on shutdown
        await async_engine.dispose()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        # The context manager will close the session for you
