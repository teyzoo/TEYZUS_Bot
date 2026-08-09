from __future__ import annotations
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from config import settings
from database.base import Base
# =========================================================
# DATABASE ENGINE
# =========================================================
engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=1800,
)
# =========================================================
# SESSION FACTORY
# =========================================================
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)
# =========================================================
# SESSION CONTEXT
# =========================================================
@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """
    Создаёт AsyncSession и автоматически закрывает её
    после завершения работы.
    Использование:
        async with get_session() as session:
            ...
    """
    session = async_session_factory()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
# =========================================================
# INITIALIZE DATABASE
# =========================================================
async def init_database() -> None:
    from database.models import User
    async with engine.begin() as connection:
        await connection.run_sync(
            Base.metadata.create_all
        )
# =========================================================
# CLOSE DATABASE
# =========================================================
async def close_database() -> None:
    await engine.dispose()
