from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

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
    Создаёт AsyncSession.

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
# DATABASE INITIALIZATION
# =========================================================

async def init_database() -> None:
    """
    Создаёт все таблицы, описанные в SQLAlchemy-моделях.

    Важно:
    database.models импортируется внутри функции,
    чтобы модели успели зарегистрироваться
    в Base.metadata.
    """

    # =====================================================
    # IMPORT ALL MODELS
    # =====================================================

    from database.models import (
        User,
        PromoCode,
        PromoActivation,
        Task,
        TaskCompletion,
    )

    # Убираем предупреждения IDE о неиспользуемых
    # импортированных моделях.
    _ = (
        User,
        PromoCode,
        PromoActivation,
        Task,
        TaskCompletion,
    )

    # =====================================================
    # CREATE TABLES
    # =====================================================

    async with engine.begin() as connection:

        await connection.run_sync(
            Base.metadata.create_all
        )


# =========================================================
# DATABASE CLOSE
# =========================================================

async def close_database() -> None:
    """
    Полностью закрывает SQLAlchemy engine.
    """

    await engine.dispose()
