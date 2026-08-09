from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    Task,
    TaskCompletion,
    User,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TaskRepository:
    """
    Полная работа с заданиями.

    Отвечает за:
    - получение заданий;
    - проверку доступности;
    - получение выполнений;
    - создание выполнения;
    - статистику;
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # =====================================================
    # GET TASK
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
        *,
        is_premium: bool = False,
        include_premium: bool = True,
    ) -> list[Task]:

        now = utc_now()

        conditions = [
            Task.is_active.is_(True),
        ]

        conditions.append(
            (
                Task.starts_at.is_(None)
                | (Task.starts_at <= now)
            )
        )

        conditions.append(
            (
                Task.expires_at.is_(None)
                | (Task.expires_at >= now)
            )
        )

        if not is_premium:

            conditions.append(
                Task.only_premium.is_(False)
            )

        if not include_premium:

            conditions.append(
                Task.only_premium.is_(False)
            )

        result = await self.session.execute(
            select(Task)
            .where(*conditions)
            .order_by(
                Task.sort_order.asc(),
                Task.id.desc(),
            )
        )

        return list(
            result.scalars().all()
        )

    # =====================================================
    # TASKS FOR USER
    # =====================================================

    async def get_tasks_for_user(
        self,
        user: User,
    ) -> list[Task]:

        return await self.get_active_tasks(
            is_premium=bool(
                user.premium_active
            )
        )

    # =====================================================
    # USER COMPLETIONS
    # =====================================================

    async def get_user_completions(
        self,
        user_id: int,
    ) -> list[TaskCompletion]:

        result = await self.session.execute(
            select(TaskCompletion)
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
    # COMPLETIONS FOR TASK
    # =====================================================

    async def get_task_completions(
        self,
        task_id: int,
    ) -> list[TaskCompletion]:

        result = await self.session.execute(
            select(TaskCompletion)
            .where(
                TaskCompletion.task_id
                == task_id
            )
            .order_by(
                TaskCompletion.completed_at.desc()
            )
        )

        return list(
            result.scalars().all()
        )

    # =====================================================
    # USER TASK COMPLETION COUNT
    # =====================================================

    async def get_user_completion_count(
        self,
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
                == task_id,
                TaskCompletion.user_id
                == user_id,
            )
        )

        return int(
            result.scalar_one() or 0
        )

    # =====================================================
    # TOTAL COMPLETIONS
    # =====================================================

    async def get_completion_count(
        self,
        task_id: int,
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
        )

        return int(
            result.scalar_one() or 0
        )

    # =====================================================
    # CAN COMPLETE
    # =====================================================

    async def can_complete(
        self,
        task: Task,
        user: User,
    ) -> tuple[bool, str]:

        now = utc_now()

        if not task.is_active:
            return (
                False,
                "Задание отключено.",
            )

        if (
            task.starts_at
            and now < task.starts_at
        ):
            return (
                False,
                "Задание ещё не началось.",
            )

        if (
            task.expires_at
            and now > task.expires_at
        ):
            return (
                False,
                "Срок выполнения задания истёк.",
            )

        if (
            task.only_premium
            and not user.premium_active
        ):
            return (
                False,
                "Это задание доступно только Premium.",
            )

        if (
            task.only_new_users
            and user.created_at is not None
        ):
            # Проверка "нового пользователя"
            # выполняется отдельным сервисом.
            pass

        if (
            task.max_completions is not None
        ):
            total = (
                await self.get_completion_count(
                    task.id
                )
            )

            if total >= task.max_completions:
                return (
                    False,
                    "Лимит выполнений задания исчерпан.",
                )

        user_count = (
            await self.get_user_completion_count(
                task.id,
                user.id,
            )
        )

        max_per_user = (
            task.max_completions_per_user
        )

        if max_per_user is not None:

            if (
                user_count
                >= max_per_user
            ):
                return (
                    False,
                    "Вы уже выполнили это задание максимальное количество раз.",
                )

        if not task.repeatable and user_count > 0:

            return (
                False,
                "Вы уже выполняли это задание.",
            )

        return (
            True,
            "",
        )

    # =====================================================
    # CREATE COMPLETION
    # =====================================================

    async def create_completion(
        self,
        *,
        task: Task,
        user: User,
    ) -> TaskCompletion:

        completion = TaskCompletion(
            task_id=task.id,
            user_id=user.id,
            telegram_id=user.telegram_id,
            reward_type=task.reward_type,
            reward_amount=task.reward_amount,
            premium_days=task.premium_days,
        )

        self.session.add(
            completion
        )

        task.completions_count += 1

        await self.session.flush()

        return completion

    # =====================================================
    # CREATE TASK
    # =====================================================

    async def create_task(
        self,
        *,
        title: str,
        description: Optional[str],
        task_type: str,
        target_value: Optional[str],
        reward_type: str,
        reward_amount: int = 0,
        premium_days: int = 0,
        max_completions: Optional[int] = None,
        max_completions_per_user: Optional[int] = 1,
        repeatable: bool = False,
        only_new_users: bool = False,
        only_premium: bool = False,
        starts_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
        sort_order: int = 0,
        image_file_id: Optional[str] = None,
        created_by: int = 0,
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
            max_completions_per_user=max_completions_per_user,
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
    # UPDATE TASK
    # =====================================================

    async def update_task(
        self,
        task_id: int,
        **values,
    ) -> Optional[Task]:

        task = await self.get_by_id(
            task_id
        )

        if task is None:
            return None

        for key, value in values.items():

            if hasattr(task, key):
                setattr(
                    task,
                    key,
                    value,
                )

        await self.session.flush()

        return task

    # =====================================================
    # ENABLE / DISABLE
    # =====================================================

    async def set_active(
        self,
        task_id: int,
        active: bool,
    ) -> bool:

        result = await self.session.execute(
            update(Task)
            .where(
                Task.id == task_id
            )
            .values(
                is_active=active
            )
        )

        return result.rowcount > 0

    # =====================================================
    # DELETE
    # =====================================================

    async def delete(
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

        return True
