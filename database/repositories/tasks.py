from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    Task,
    TaskCompletion,
)


class TaskRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    # =====================================================
    # TASK
    # =====================================================

    async def get_task(
        self,
        task_id: int,
    ) -> Task | None:

        result = await self.session.execute(
            select(Task).where(
                Task.id == task_id
            )
        )

        return result.scalar_one_or_none()

    async def get_active_tasks(
        self,
    ) -> list[Task]:

        result = await self.session.execute(
            select(Task)
            .where(
                Task.is_active
                == True
            )
            .order_by(
                Task.sort_order.asc(),
                Task.id.asc(),
            )
        )

        return list(
            result.scalars().all()
        )

    async def get_tasks_by_period(
        self,
        period_type: str,
    ) -> list[Task]:

        result = await self.session.execute(
            select(Task)
            .where(
                Task.is_active
                == True,
                Task.period_type
                == period_type,
            )
            .order_by(
                Task.sort_order.asc()
            )
        )

        return list(
            result.scalars().all()
        )

    async def create_task(
        self,
        **kwargs,
    ) -> Task:

        task = Task(
            **kwargs
        )

        self.session.add(
            task
        )

        await self.session.flush()

        return task

    async def update_task(
        self,
        task: Task,
        **kwargs,
    ) -> Task:

        for key, value in kwargs.items():

            if hasattr(task, key):
                setattr(
                    task,
                    key,
                    value,
                )

        await self.session.flush()

        return task

    async def delete_task(
        self,
        task: Task,
    ) -> None:

        await self.session.delete(
            task
        )

        await self.session.flush()

    # =====================================================
    # COMPLETION
    # =====================================================

    async def get_completion(
        self,
        task_id: int,
        user_id: int,
        period_key: str | None,
    ) -> TaskCompletion | None:

        query = select(
            TaskCompletion
        ).where(
            TaskCompletion.task_id
            == task_id,
            TaskCompletion.user_id
            == user_id,
        )

        if period_key is None:

            query = query.where(
                TaskCompletion.period_key
                .is_(None)
            )

        else:

            query = query.where(
                TaskCompletion.period_key
                == period_key
            )

        result = await self.session.execute(
            query
        )

        return result.scalar_one_or_none()

    async def get_user_completions(
        self,
        user_id: int,
        task_id: int,
    ) -> list[TaskCompletion]:

        result = await self.session.execute(
            select(TaskCompletion)
            .where(
                TaskCompletion.user_id
                == user_id,
                TaskCompletion.task_id
                == task_id,
            )
            .order_by(
                TaskCompletion.completed_at.desc()
            )
        )

        return list(
            result.scalars().all()
        )

    async def count_user_completions(
        self,
        user_id: int,
        task_id: int,
    ) -> int:

        result = await self.session.execute(
            select(
                func.count(
                    TaskCompletion.id
                )
            )
            .where(
                TaskCompletion.user_id
                == user_id,
                TaskCompletion.task_id
                == task_id,
            )
        )

        return int(
            result.scalar_one()
        )

    async def create_completion(
        self,
        **kwargs,
    ) -> TaskCompletion:

        completion = TaskCompletion(
            **kwargs
        )

        self.session.add(
            completion
        )

        await self.session.flush()

        return completion
