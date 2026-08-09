from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Task, TaskCompletion


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def get_active_tasks(
    session: AsyncSession,
    premium: bool = False,
) -> list[Task]:
    now = utc_now()

    query = (
        select(Task)
        .where(
            Task.is_active.is_(True),
            (Task.starts_at.is_(None) | (Task.starts_at <= now)),
            (Task.expires_at.is_(None) | (Task.expires_at >= now)),
        )
        .order_by(
            Task.sort_order.asc(),
            Task.id.desc(),
        )
    )

    result = await session.execute(query)
    tasks = list(result.scalars().all())

    available: list[Task] = []

    for task in tasks:
        if task.only_premium and not premium:
            continue

        available.append(task)

    return available


async def get_task_by_id(
    session: AsyncSession,
    task_id: int,
) -> Optional[Task]:
    result = await session.execute(
        select(Task).where(Task.id == task_id)
    )

    return result.scalar_one_or_none()


async def get_user_task_completions(
    session: AsyncSession,
    task_id: int,
    user_id: int,
) -> int:
    result = await session.execute(
        select(func.count(TaskCompletion.id))
        .where(
            TaskCompletion.task_id == task_id,
            TaskCompletion.user_id == user_id,
        )
    )

    return int(result.scalar_one() or 0)


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
    )

    session.add(completion)

    task.completions_count += 1

    await session.commit()
    await session.refresh(completion)

    return completion
