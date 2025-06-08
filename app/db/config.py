from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.core.settings import settings

# Create async engine with connection pooling
async_engine = create_async_engine(
    # url=settings.DATABASE_URL,
    url=f"postgresql+asyncpg://{settings.SUPABASE_USER}:{settings.SUPABASE_PASSWORD}@"
        f"{settings.SUPABASE_HOST}:{settings.SUPABASE_PORT}/{settings.SUPABASE_DB_NAME}",
    echo=True,
    pool_pre_ping=True,  # Checks connection health
    pool_size=20,
    max_overflow=10,
    # connect_args={
    #     "ssl": "require",  # Supabase requires SSL
    #     "statement_cache_size": 0  # Disable prepared statement cache
    # }
)
    


# Session factory should be created once
AsyncSessionLocal = sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)


@asynccontextmanager
async def init_db(app: FastAPI):
    # Initialize database tables
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

