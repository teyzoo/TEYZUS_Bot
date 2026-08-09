from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, Task
from database.repositories.tasks import TaskRepository


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TaskRewardService:
    """
    Выдача наград за задания.

    Поддерживаемые награды:

    balance
    stars
    searches
    traps
    discount
    premium
    """

    async def give_reward(
        self,
        session: AsyncSession,
        user: User,
        task: Task,
    ) -> str:

        reward_type = (
            task.reward_type or ""
        ).lower().strip()

        amount = max(
            0,
            int(
                task.reward_amount or 0
            )
        )

        premium_days = max(
            0,
            int(
                task.premium_days or 0
            )
        )

        # =================================================
        # BALANCE
        # =================================================

        if reward_type in {
            "balance",
            "balance_rub",
            "rub",
        }:

            user.balance_rub += amount

            return (
                f"💰 +{amount} ₽"
            )

        # =================================================
        # STARS
        # =================================================

        if reward_type in {
            "stars",
            "star",
        }:

            user.stars_balance += amount

            return (
                f"⭐ +{amount} Stars"
            )

        # =================================================
        # SEARCHES
        # =================================================

        if reward_type in {
            "searches",
            "search",
            "bonus_searches",
        }:

            user.bonus_searches += amount

            return (
                f"🔎 +{amount} поисков"
            )

        # =================================================
        # TRAPS
        # =================================================

        if reward_type in {
            "traps",
            "trap",
            "bonus_traps",
        }:

            user.bonus_traps += amount

            return (
                f"🎯 +{amount} ловушек"
            )

        # =================================================
        # DISCOUNT
        # =================================================

        if reward_type in {
            "discount",
            "discount_percent",
        }:

            user.discount_percent = min(
                100,
                user.discount_percent
                + amount,
            )

            return (
                f"🏷️ +{amount}% скидки"
            )

        # =================================================
        # PREMIUM
        # =================================================

        if reward_type in {
            "premium",
            "premium_days",
        }:

            if premium_days <= 0:

                premium_days = amount

            await self._add_premium(
                user,
                premium_days,
            )

            return (
                f"💎 Premium на "
                f"{premium_days} дн."
            )

        # =================================================
        # UNKNOWN
        # =================================================

        return (
            "🎁 Награда получена."
        )

    # =====================================================
    # PREMIUM
    # =====================================================

    async def _add_premium(
        self,
        user: User,
        days: int,
    ) -> None:

        if days <= 0:
            return

        now = utc_now()

        current_until = (
            user.premium_until
        )

        if (
            current_until is not None
            and current_until > now
        ):
            start = current_until
        else:
            start = now

        user.premium_until = (
            start
            + timedelta(days=days)
        )

        user.premium_active = True


task_reward_service = TaskRewardService()
