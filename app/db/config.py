from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlalchemy.ext.asyncio import create_async_engine
import asyncpg
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.core.settings import settings

# Create async engine with connection pooling


# async_engine = create_async_engine(
#     url=f"postgresql+asyncpg://{settings.SUPABASE_USER}:{settings.SUPABASE_PASSWORD}@"
#         f"{settings.SUPABASE_HOST}:{settings.SUPABASE_PORT}/{settings.SUPABASE_DB_NAME}",
#     echo=True,
#     pool_pre_ping=True,  # Checks connection health
#     # Reduced pool size since Supabase/PgBouncer handles connection pooling
#     # pool_size=5,
#     # max_overflow=5,
#     connect_args={
#         "ssl": "require",
#         "statement_cache_size": 0,  # CRITICAL: Disable prepared statement cache for PgBouncer
#         "server_settings": {
#             "application_name": "sign_language_app",
#         }
#     }
# )
async_engine = create_async_engine(
    f"postgresql+asyncpg://{settings.SUPABASE_USER}:{settings.SUPABASE_PASSWORD}@"
        f"{settings.SUPABASE_HOST}:{settings.SUPABASE_PORT}/{settings.SUPABASE_DB_NAME}",
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
    connect_args={
        "ssl": "require",
        "statement_cache_size": 0,  # مهم جداً مع PgBouncer
        "server_settings": {
            "application_name": "sign_language_app",
        }
    },
)

    


# Session factory should be created once
AsyncSessionLocal = sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)


@asynccontextmanager
async def init_db(app: FastAPI):
    # Initialize database tables
    if settings.ENVIRONMENT == "development":
        async with async_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    yield  # App runs here

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
        finally:
            await session.close()

