from __future__ import annotations

from datetime import datetime, timezone, timedelta
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    Task,
    TaskCompletion,
    User,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# =========================================================
# TASK PERIOD
# =========================================================

def get_period_start(
    period: str,
    now: datetime | None = None,
) -> datetime:
    now = now or utc_now()

    if period == "daily":
        return now.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

    if period == "weekly":
        start = now - timedelta(
            days=now.weekday()
        )

        return start.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

    if period == "monthly":
        return now.replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

    return datetime.min.replace(
        tzinfo=timezone.utc
    )


# =========================================================
# ACTIVE TASK
# =========================================================

def task_is_active(
    task: Task,
    now: datetime | None = None,
) -> bool:
    now = now or utc_now()

    if not task.is_active:
        return False

    if task.starts_at:
        starts = task.starts_at

        if starts.tzinfo is None:
            starts = starts.replace(
                tzinfo=timezone.utc
            )

        if now < starts:
            return False

    if task.expires_at:
        expires = task.expires_at

        if expires.tzinfo is None:
            expires = expires.replace(
                tzinfo=timezone.utc
            )

        if now > expires:
            return False

    if (
        task.max_completions is not None
        and task.completions_count
        >= task.max_completions
    ):
        return False

    return True


# =========================================================
# USER CAN SEE TASK
# =========================================================

def user_can_see_task(
    user: User,
    task: Task,
) -> bool:

    # Premium-only
    if task.only_premium:
        if not user.premium_active:
            return False

    # New users
    if task.only_new_users:
        if user.created_at is None:
            return False

    return True


# =========================================================
# COMPLETION COUNT
# =========================================================

async def get_user_completion_count(
    session: AsyncSession,
    user_id: int,
    task: Task,
) -> int:

    query = select(
        TaskCompletion
    ).where(
        TaskCompletion.user_id
        == user_id,
        TaskCompletion.task_id
        == task.id,
    )

    result = await session.execute(
        query
    )

    completions = result.scalars().all()

    if task.repeatable:
        period_start = get_period_start(
            task.period
        )

        count = 0

        for completion in completions:

            completed_at = (
                completion.completed_at
            )

            if completed_at.tzinfo is None:
                completed_at = (
                    completed_at.replace(
                        tzinfo=timezone.utc
                    )
                )

            if completed_at >= period_start:
                count += 1

        return count

    return len(completions)


# =========================================================
# CAN COMPLETE
# =========================================================

async def can_complete_task(
    session: AsyncSession,
    user: User,
    task: Task,
) -> tuple[bool, str]:

    if not task_is_active(task):
        return (
            False,
            "Задание сейчас недоступно.",
        )

    if not user_can_see_task(
        user,
        task,
    ):
        return (
            False,
            "Это задание доступно только Premium.",
        )

    count = await get_user_completion_count(
        session,
        user.id,
        task,
    )

    limit = (
        task.max_completions_per_user
    )

    if limit is not None:

        if count >= limit:
            if task.repeatable:
                return (
                    False,
                    "Ты уже выполнил это задание за текущий период.",
                )

            return (
                False,
                "Ты уже выполнил это задание.",
            )

    return True, ""


# =========================================================
# REWARD
# =========================================================

async def give_reward(
    session: AsyncSession,
    user: User,
    reward_type: str,
    amount: int,
    premium_days: int,
) -> str:

    if reward_type == "balance":
        user.balance_rub += amount

        return (
            f"💰 +{amount:,} ₽".replace(
                ",",
                " ",
            )
        )

    if reward_type == "stars":
        user.stars_balance += amount

        return (
            f"⭐ +{amount} Stars"
        )

    if reward_type == "searches":
        user.bonus_searches += amount

        return (
            f"🔎 +{amount} поисков"
        )

    if reward_type == "traps":
        user.bonus_traps += amount

        return (
            f"🎯 +{amount} ловушек"
        )

    if reward_type == "discount":
        user.discount_percent = min(
            100,
            user.discount_percent
            + amount,
        )

        return (
            f"🏷 +{amount}% скидки"
        )

    if reward_type == "premium":

        now = utc_now()

        if (
            user.premium_until
            and user.premium_until > now
        ):
            start = user.premium_until
        else:
            start = now

        user.premium_until = (
            start
            + timedelta(
                days=premium_days
            )
        )

        user.premium_active = True

        return (
            f"💎 Premium на "
            f"{premium_days} дн."
        )

    return "🎁 Награда получена"


# =========================================================
# COMPLETE TASK
# =========================================================

async def complete_task(
    session: AsyncSession,
    user: User,
    task: Task,
) -> tuple[bool, str]:

    allowed, reason = (
        await can_complete_task(
            session,
            user,
            task,
        )
    )

    if not allowed:
        return False, reason

    # Snapshot награды
    reward_type = (
        task.reward_type
    )

    reward_amount = (
        task.reward_amount
    )

    premium_days = (
        task.premium_days
    )

    # Выдаём награду
    reward_text = await give_reward(
        session=session,
        user=user,
        reward_type=reward_type,
        amount=reward_amount,
        premium_days=premium_days,
    )

    # Записываем выполнение
    completion = TaskCompletion(
        task_id=task.id,
        user_id=user.id,
        telegram_id=user.telegram_id,
        reward_type=reward_type,
        reward_amount=reward_amount,
        premium_days=premium_days,
    )

    session.add(completion)

    task.completions_count += 1

    await session.commit()

    return (
        True,
        reward_text,
    )
