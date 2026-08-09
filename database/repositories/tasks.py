from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    Task,
    TaskCompletion,
)


# =========================================================
# TIME
# =========================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# =========================================================
# GET TASK
# =========================================================

async def get_task(
    session: AsyncSession,
    task_id: int,
) -> Optional[Task]:
    result = await session.execute(
        select(Task).where(
            Task.id == task_id
        )
    )

    return result.scalar_one_or_none()


# =========================================================
# GET ACTIVE TASKS
# =========================================================

async def get_active_tasks(
    session: AsyncSession,
) -> list[Task]:

    now = utc_now()

    result = await session.execute(
        select(Task)
        .where(
            Task.is_active.is_(True)
        )
        .where(
            (Task.starts_at.is_(None))
            | (Task.starts_at <= now)
        )
        .where(
            (Task.expires_at.is_(None))
            | (Task.expires_at >= now)
        )
        .order_by(
            Task.sort_order.asc(),
            Task.id.desc(),
        )
    )

    return list(
        result.scalars().all()
    )


# =========================================================
# GET TASK COMPLETION
# =========================================================

async def get_user_task_completions(
    session: AsyncSession,
    task_id: int,
    user_id: int,
) -> list[TaskCompletion]:

    result = await session.execute(
        select(TaskCompletion)
        .where(
            TaskCompletion.task_id == task_id
        )
        .where(
            TaskCompletion.user_id == user_id
        )
        .order_by(
            TaskCompletion.completed_at.desc()
        )
    )

    return list(
        result.scalars().all()
    )


# =========================================================
# COMPLETION COUNT
# =========================================================

async def get_user_task_completion_count(
    session: AsyncSession,
    task_id: int,
    user_id: int,
) -> int:

    result = await session.execute(
        select(
            func.count(TaskCompletion.id)
        )
        .where(
            TaskCompletion.task_id == task_id
        )
        .where(
            TaskCompletion.user_id == user_id
        )
    )

    return int(
        result.scalar() or 0
    )


# =========================================================
# CREATE COMPLETION
# =========================================================

async def create_task_completion(
    session: AsyncSession,
    task: Task,
    user_id: int,
    telegram_id: int,
) -> TaskCompletion:

    completion = TaskCompletion(
        task_id=task.id,
        user_id=user_id,
        telegram_id=telegram_id,
        reward_type=task.reward_type,
        reward_amount=task.reward_amount,
        premium_days=task.premium_days,
        completed_at=utc_now(),
    )

    session.add(completion)

    task.completions_count += 1

    await session.flush()

    return completion


# =========================================================
# DEACTIVATE TASK
# =========================================================

async def deactivate_task(
    session: AsyncSession,
    task: Task,
) -> None:

    task.is_active = False

    await session.flush()


# =========================================================
# TASKS FOR PERIOD
# =========================================================

async def get_tasks_by_period(
    session: AsyncSession,
    period: str,
) -> list[Task]:

    tasks = await get_active_tasks(
        session
    )

    return [
        task
        for task in tasks
        if get_task_period(task) == period
    ]


# =========================================================
# TASK PERIOD
# =========================================================

def get_task_period(
    task: Task,
) -> str:

    """
    Определяет период задания.

    Для совместимости со старой моделью:
    период вычисляется по target_value.

    В дальнейшем можно добавить
    отдельное поле period в Task.
    """

    value = (
        task.target_value or ""
    ).lower()

    if value.startswith(
        "daily:"
    ):
        return "daily"

    if value.startswith(
        "weekly:"
    ):
        return "weekly"

    if value.startswith(
        "monthly:"
    ):
        return "monthly"

    return "permanent"


# =========================================================
# TASK TYPE CHECK
# =========================================================

def normalize_task_type(
    task_type: str,
) -> str:

    return (
        task_type
        .strip()
        .lower()
    )


# =========================================================
# TASK REWARD CHECK
# =========================================================

def normalize_reward_type(
    reward_type: str,
) -> str:

    return (
        reward_type
        .strip()
        .lower()
    )
