from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    Task,
    User,
    TaskCompletion,
)

from database.repositories.tasks import (
    TaskRepository,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TaskService:
    """
    Основная бизнес-логика системы заданий.

    Поддерживает:

    - обычные задания;
    - Premium-задания;
    - лимиты;
    - повторяемость;
    - сроки;
    - лимит общего количества выполнений;
    - лимит выполнений одним пользователем;
    - награды.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:

        self.session = session

        self.repository = TaskRepository(
            session
        )

    # =====================================================
    # GET TASKS
    # =====================================================

    async def get_available_tasks(
        self,
        user: User,
    ) -> list[Task]:

        tasks = (
            await self.repository
            .get_active_tasks()
        )

        available: list[Task] = []

        for task in tasks:

            if not self._user_allowed(
                task,
                user,
            ):
                continue

            if (
                task.max_completions
                is not None
                and task.completions_count
                >= task.max_completions
            ):
                continue

            count = (
                await self.repository
                .get_user_completion_count(
                    task_id=task.id,
                    user_id=user.id,
                )
            )

            if (
                not task.repeatable
                and count > 0
            ):
                continue

            if (
                task.max_completions_per_user
                is not None
                and count
                >= task.max_completions_per_user
            ):
                continue

            available.append(
                task
            )

        return available

    # =====================================================
    # USER FILTER
    # =====================================================

    def _user_allowed(
        self,
        task: Task,
        user: User,
    ) -> bool:

        # -------------------------------------------------
        # PREMIUM
        # -------------------------------------------------

        if (
            task.only_premium
            and not user.premium_active
        ):
            return False

        # -------------------------------------------------
        # NEW USER
        # -------------------------------------------------

        if task.only_new_users:

            # Пользователь считается новым
            # в течение первых 24 часов.

            now = utc_now()

            created_at = user.created_at

            if created_at.tzinfo is None:

                created_at = created_at.replace(
                    tzinfo=timezone.utc
                )

            age = (
                now - created_at
            ).total_seconds()

            if age > 86400:

                return False

        return True

    # =====================================================
    # COMPLETE
    # =====================================================

    async def complete_task(
        self,
        *,
        task: Task,
        user: User,
        telegram_id: int,
    ) -> tuple[
        bool,
        Optional[TaskCompletion],
        str,
    ]:

        # -------------------------------------------------
        # ACTIVE
        # -------------------------------------------------

        if not task.is_active:

            return (
                False,
                None,
                "Задание отключено.",
            )

        # -------------------------------------------------
        # START DATE
        # -------------------------------------------------

        now = utc_now()

        if (
            task.starts_at
            is not None
        ):

            starts_at = task.starts_at

            if starts_at.tzinfo is None:

                starts_at = starts_at.replace(
                    tzinfo=timezone.utc
                )

            if now < starts_at:

                return (
                    False,
                    None,
                    "Задание ещё не началось.",
                )

        # -------------------------------------------------
        # END DATE
        # -------------------------------------------------

        if (
            task.expires_at
            is not None
        ):

            expires_at = task.expires_at

            if expires_at.tzinfo is None:

                expires_at = expires_at.replace(
                    tzinfo=timezone.utc
                )

            if now > expires_at:

                return (
                    False,
                    None,
                    "Срок выполнения задания истёк.",
                )

        # -------------------------------------------------
        # USER FILTER
        # -------------------------------------------------

        if not self._user_allowed(
            task,
            user,
        ):

            return (
                False,
                None,
                "Это задание недоступно для вашего аккаунта.",
            )

        # -------------------------------------------------
        # GLOBAL LIMIT
        # -------------------------------------------------

        if (
            task.max_completions
            is not None
            and task.completions_count
            >= task.max_completions
        ):

            return (
                False,
                None,
                "Лимит выполнений задания исчерпан.",
            )

        # -------------------------------------------------
        # USER LIMIT
        # -------------------------------------------------

        user_count = (
            await self.repository
            .get_user_completion_count(
                task_id=task.id,
                user_id=user.id,
            )
        )

        # Одноразовое задание.

        if (
            not task.repeatable
            and user_count > 0
        ):

            return (
                False,
                None,
                "Вы уже выполняли это задание.",
            )

        # -------------------------------------------------
        # MAX PER USER
        # -------------------------------------------------

        if (
            task.max_completions_per_user
            is not None
            and user_count
            >= task.max_completions_per_user
        ):

            return (
                False,
                None,
                "Вы достигли лимита выполнения этого задания.",
            )

        # -------------------------------------------------
        # CREATE COMPLETION
        # -------------------------------------------------

        completion = (
            await self.repository
            .create_completion(
                task=task,
                user_id=user.id,
                telegram_id=telegram_id,
            )
        )

        # -------------------------------------------------
        # REWARD
        # -------------------------------------------------

        reward_message = (
            await self._give_reward(
                task=task,
                user=user,
            )
        )

        return (
            True,
            completion,
            reward_message,
        )

    # =====================================================
    # REWARD
    # =====================================================

    async def _give_reward(
        self,
        *,
        task: Task,
        user: User,
    ) -> str:

        reward_type = (
            task.reward_type
            .strip()
            .lower()
        )

        amount = (
            task.reward_amount
        )

        # -------------------------------------------------
        # STARS
        # -------------------------------------------------

        if reward_type == "stars":

            user.stars_balance += amount

            await self.session.flush()

            return (
                f"⭐ Вы получили "
                f"{amount} Stars."
            )

        # -------------------------------------------------
        # RUB
        # -------------------------------------------------

        if reward_type in (
            "rub",
            "balance",
            "money",
        ):

            user.balance_rub += amount

            await self.session.flush()

            return (
                f"💰 Вы получили "
                f"{amount} ₽."
            )

        # -------------------------------------------------
        # SEARCHES
        # -------------------------------------------------

        if reward_type in (
            "search",
            "searches",
            "bonus_searches",
        ):

            user.bonus_searches += amount

            await self.session.flush()

            return (
                f"🔎 Вы получили "
                f"{amount} дополнительных поисков."
            )

        # -------------------------------------------------
        # TRAPS
        # -------------------------------------------------

        if reward_type in (
            "trap",
            "traps",
            "bonus_traps",
        ):

            user.bonus_traps += amount

            await self.session.flush()

            return (
                f"🎯 Вы получили "
                f"{amount} дополнительных ловушек."
            )

        # -------------------------------------------------
        # DISCOUNT
        # -------------------------------------------------

        if reward_type in (
            "discount",
            "discount_percent",
        ):

            user.discount_percent += amount

            if user.discount_percent > 100:

                user.discount_percent = 100

            await self.session.flush()

            return (
                f"🏷 Вы получили "
                f"{amount}% скидки."
            )

        # -------------------------------------------------
        # PREMIUM
        # -------------------------------------------------

        if reward_type in (
            "premium",
            "premium_days",
        ):

            days = (
                task.premium_days
                or amount
            )

            current_until = (
                user.premium_until
            )

            if (
                current_until is None
                or current_until < utc_now()
            ):

                current_until = utc_now()

            user.premium_until = (
                current_until
                + __import__(
                    "datetime"
                ).timedelta(
                    days=days
                )
            )

            user.premium_active = True

            await self.session.flush()

            return (
                f"💎 Вы получили "
                f"TEYZUS Premium "
                f"на {days} дней."
            )

        # -------------------------------------------------
        # UNKNOWN
        # -------------------------------------------------

        return (
            "🎁 Задание выполнено. "
            "Награда будет обработана системой."
        )
