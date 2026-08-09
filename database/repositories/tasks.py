from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    Task,
    TaskCompletion,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TaskRepository:
    """
    Работа с заданиями.

    Здесь находится только работа с PostgreSQL.
    Проверка бизнес-логики находится в services/tasks.py.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    # =====================================================
    # CREATE
    # =====================================================

    async def create_task(
        self,
        *,
        title: str,
        description: Optional[str],
        task_type: str,
        target_value: Optional[str],
        reward_type: str,
        reward_amount: int,
        premium_days: int,
        max_completions: Optional[int],
        max_completions_per_user: Optional[int],
        repeatable: bool,
        only_new_users: bool,
        only_premium: bool,
        starts_at: Optional[datetime],
        expires_at: Optional[datetime],
        image_file_id: Optional[str],
        created_by: int,
        sort_order: int = 0,
    ) -> Task:

        task = Task(
            title=title,
            description=description,
            task_type=task_type,
            target_value=target_value,
            reward_type=reward_type,
            reward_amount=reward_amount,
            premium_days=premium_days,
            max_completions=max_completions,
            completions_count=0,
            max_completions_per_user=(
                max_completions_per_user
            ),
            repeatable=repeatable,
            only_new_users=only_new_users,
            only_premium=only_premium,
            starts_at=starts_at,
            expires_at=expires_at,
            is_active=True,
            sort_order=sort_order,
            image_file_id=image_file_id,
            created_by=created_by,
        )

        self.session.add(task)

        await self.session.flush()

        return task

    # =====================================================
    # GET BY ID
    # =====================================================

    async def get_by_id(
        self,
        task_id: int,
    ) -> Optional[Task]:

        result = await self.session.execute(
            select(Task).where(
                Task.id == task_id
            )
        )

        return result.scalar_one_or_none()

    # =====================================================
    # ACTIVE TASKS
    # =====================================================

    async def get_active_tasks(
        self,
    ) -> list[Task]:

        now = utc_now()

        result = await self.session.execute(
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

    # =====================================================
    # ALL TASKS
    # =====================================================

    async def get_all_tasks(
        self,
    ) -> list[Task]:

        result = await self.session.execute(
            select(Task)
            .order_by(
                Task.sort_order.asc(),
                Task.id.desc(),
            )
        )

        return list(
            result.scalars().all()
        )

    # =====================================================
    # USER COMPLETIONS
    # =====================================================

    async def get_user_completions(
        self,
        *,
        task_id: int,
        user_id: int,
    ) -> list[TaskCompletion]:

        result = await self.session.execute(
            select(TaskCompletion)
            .where(
                TaskCompletion.task_id
                == task_id
            )
            .where(
                TaskCompletion.user_id
                == user_id
            )
            .order_by(
                TaskCompletion.completed_at.desc()
            )
        )

        return list(
            result.scalars().all()
        )

    # =====================================================
    # COMPLETION COUNT
    # =====================================================

    async def get_user_completion_count(
        self,
        *,
        task_id: int,
        user_id: int,
    ) -> int:

        result = await self.session.execute(
            select(
                func.count(
                    TaskCompletion.id
                )
            )
            .where(
                TaskCompletion.task_id
                == task_id
            )
            .where(
                TaskCompletion.user_id
                == user_id
            )
        )

        return int(
            result.scalar_one()
        )

    # =====================================================
    # CREATE COMPLETION
    # =====================================================

    async def create_completion(
        self,
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
            completed_at=utc_now(),
        )

        self.session.add(
            completion
        )

        task.completions_count += 1

        await self.session.flush()

        return completion

    # =====================================================
    # DELETE
    # =====================================================

    async def delete_task(
        self,
        task_id: int,
    ) -> bool:

        task = await self.get_by_id(
            task_id
        )

        if task is None:
            return False

        await self.session.delete(
            task
        )

        await self.session.flush()

        return True

    # =====================================================
    # ACTIVATE / DEACTIVATE
    # =====================================================

    async def set_active(
        self,
        task_id: int,
        active: bool,
    ) -> bool:

        task = await self.get_by_id(
            task_id
        )

        if task is None:
            return False

        task.is_active = active

        await self.session.flush()

        return True

    # =====================================================
    # UPDATE SORT
    # =====================================================

    async def set_sort_order(
        self,
        task_id: int,
        sort_order: int,
    ) -> bool:

        task = await self.get_by_id(
            task_id
        )

        if task is None:
            return False

        task.sort_order = sort_order

        await self.session.flush()

        return True
