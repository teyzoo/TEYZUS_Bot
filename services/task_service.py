from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, Task, TaskCompletion
from database.repositories.tasks import TaskRepository
from services.tasks import (
    task_reward_service,
)


class TaskService:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session
        self.repository = TaskRepository(
            session
        )

    # =====================================================
    # GET USER TASKS
    # =====================================================

    async def get_user_tasks(
        self,
        user: User,
    ) -> list[Task]:

        return await (
            self.repository
            .get_tasks_for_user(user)
        )

    # =====================================================
    # CHECK
    # =====================================================

    async def check_task(
        self,
        task: Task,
        user: User,
    ) -> tuple[bool, str]:

        return await (
            self.repository
            .can_complete(
                task,
                user,
            )
        )

    # =====================================================
    # COMPLETE
    # =====================================================

    async def complete_task(
        self,
        *,
        task: Task,
        user: User,
    ) -> tuple[
        bool,
        str,
        TaskCompletion | None,
    ]:

        allowed, reason = (
            await self.repository
            .can_complete(
                task,
                user,
            )
        )

        if not allowed:

            return (
                False,
                reason,
                None,
            )

        # =================================================
        # CREATE COMPLETION
        # =================================================

        completion = (
            await self.repository
            .create_completion(
                task=task,
                user=user,
            )
        )

        # =================================================
        # GIVE REWARD
        # =================================================

        reward_text = (
            await task_reward_service
            .give_reward(
                self.session,
                user,
                task,
            )
        )

        return (
            True,
            reward_text,
            completion,
        )
