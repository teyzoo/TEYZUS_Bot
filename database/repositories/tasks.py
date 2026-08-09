from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Task, TaskCompletion


# =========================================================
# TIME
# =========================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# =========================================================
# TASK PERIOD
# =========================================================

def get_task_period(task: Task) -> str:
    """
    Определяет период задания.

    Если даты настроены через starts_at/expires_at,
    период дополнительно можно определить по длительности.

    Основные значения:
        daily
        weekly
        monthly
        permanent
    """

    if not task.starts_at or not task.expires_at:
        return "permanent"

    delta = task.expires_at - task.starts_at

    seconds = delta.total_seconds()

    if seconds <= 86400:
        return "daily"

    if seconds <= 86400 * 7:
        return "weekly"

    if seconds <= 86400 * 31:
        return "monthly"

    return "custom"


# =========================================================
# ACTIVE TASKS
# =========================================================

async def get_active_tasks(
    session: AsyncSession,
    *,
    premium: bool = False,
) -> list[Task]:
    """
    Возвращает активные задания.

    Обычный пользователь:
        получает обычные задания.

    Premium:
        получает обычные задания +
        отдельные Premium-задания.
    """

    now = utc_now()

    conditions = [
        Task.is_active.is_(True),
        or_date_condition(now),
    ]

    if premium:
        # Premium видит всё.
        pass
    else:
        # Обычный пользователь не видит
        # задания только для Premium.
        conditions.append(
            Task.only_premium.is_(False)
        )

    query = (
        select(Task)
        .where(
            and_(*conditions)
        )
        .order_by(
            Task.sort_order.asc(),
            Task.id.asc(),
        )
    )

    result = await session.execute(query)

    return list(result.scalars().all())


def or_date_condition(now: datetime):
    """
    SQL условие:
    starts_at отсутствует ИЛИ уже наступил
    И
    expires_at отсутствует ИЛИ ещё не истёк.
    """

    from sqlalchemy import or_

    return and_(
        or_(
            Task.starts_at.is_(None),
            Task.starts_at <= now,
        ),
        or_(
            Task.expires_at.is_(None),
            Task.expires_at >= now,
        ),
    )


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
# USER COMPLETIONS
# =========================================================

async def get_user_task_completions(
    session: AsyncSession,
    *,
    user_id: int,
    task_id: int,
) -> list[TaskCompletion]:

    result = await session.execute(
        select(TaskCompletion)
        .where(
            and_(
                TaskCompletion.user_id == user_id,
                TaskCompletion.task_id == task_id,
            )
        )
        .order_by(
            TaskCompletion.completed_at.desc()
        )
    )

    return list(result.scalars().all())


# =========================================================
# COMPLETION COUNT
# =========================================================

async def get_user_task_completion_count(
    session: AsyncSession,
    *,
    user_id: int,
    task_id: int,
) -> int:

    result = await session.execute(
        select(
            func.count(TaskCompletion.id)
        ).where(
            and_(
                TaskCompletion.user_id == user_id,
                TaskCompletion.task_id == task_id,
            )
        )
    )

    return int(result.scalar() or 0)


# =========================================================
# LAST COMPLETION
# =========================================================

async def get_last_completion(
    session: AsyncSession,
    *,
    user_id: int,
    task_id: int,
) -> Optional[TaskCompletion]:

    result = await session.execute(
        select(TaskCompletion)
        .where(
            and_(
                TaskCompletion.user_id == user_id,
                TaskCompletion.task_id == task_id,
            )
        )
        .order_by(
            TaskCompletion.completed_at.desc()
        )
        .limit(1)
    )

    return result.scalar_one_or_none()


# =========================================================
# CREATE COMPLETION
# =========================================================

async def create_completion(
    session: AsyncSession,
    *,
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
    )

    session.add(completion)

    return completion


# =========================================================
# INCREMENT TASK COMPLETIONS
# =========================================================

async def increment_task_completions(
    session: AsyncSession,
    task: Task,
) -> None:

    task.completions_count = (
        task.completions_count + 1
    )


# =========================================================
# CHECK GLOBAL LIMIT
# =========================================================

def has_global_limit(
    task: Task,
) -> bool:

    return (
        task.max_completions is not None
    )


def global_limit_reached(
    task: Task,
) -> bool:

    if task.max_completions is None:
        return False

    return (
        task.completions_count
        >= task.max_completions
    )


# =========================================================
# CHECK USER LIMIT
# =========================================================

def user_limit_reached(
    task: Task,
    completion_count: int,
) -> bool:

    if task.max_completions_per_user is None:
        return False

    return (
        completion_count
        >= task.max_completions_per_user
    )
