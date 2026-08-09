from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Task, User
from database.repositories.tasks import (
    create_task_completion,
    get_user_task_completions,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def can_complete_task(
    session: AsyncSession,
    task: Task,
    user: User,
) -> tuple[bool, str]:
    now = utc_now()

    if not task.is_active:
        return False, "Это задание больше недоступно."

    if task.starts_at and task.starts_at > now:
        return False, "Это задание ещё не началось."

    if task.expires_at and task.expires_at < now:
        return False, "Срок выполнения задания закончился."

    if task.only_premium and not user.premium_active:
        return False, "Это задание доступно только TEYZUS Premium."

    if (
        task.max_completions is not None
        and task.completions_count >= task.max_completions
    ):
        return False, "Лимит выполнения этого задания исчерпан."

    user_completions = await get_user_task_completions(
        session,
        task.id,
        user.id,
    )

    if task.max_completions_per_user is not None:
        if user_completions >= task.max_completions_per_user:
            return False, "Вы уже выполнили это задание максимальное количество раз."

    if not task.repeatable and user_completions > 0:
        return False, "Это задание можно выполнить только один раз."

    return True, ""


async def reward_user(
    session: AsyncSession,
    user: User,
    task: Task,
) -> None:
    reward_type = task.reward_type.lower()

    if reward_type == "stars":
        user.stars_balance += task.reward_amount

    elif reward_type == "rub":
        user.balance_rub += task.reward_amount

    elif reward_type == "searches":
        user.bonus_searches += task.reward_amount

    elif reward_type == "traps":
        user.bonus_traps += task.reward_amount

    elif reward_type == "discount":
        user.discount_percent = min(
            100,
            user.discount_percent + task.reward_amount,
        )

    elif reward_type == "premium":
        days = max(task.premium_days, 0)

        if days > 0:
            if (
                user.premium_until
                and user.premium_until > utc_now()
            ):
                base_date = user.premium_until
            else:
                base_date = utc_now()

            user.premium_until = (
                base_date + timedelta(days=days)
            )

            user.premium_active = True


async def complete_task(
    session: AsyncSession,
    task: Task,
    user: User,
) -> tuple[bool, str]:
    allowed, reason = await can_complete_task(
        session,
        task,
        user,
    )

    if not allowed:
        return False, reason

    await reward_user(
        session,
        user,
        task,
    )

    await create_task_completion(
        session,
        task,
        user.id,
        user.telegram_id,
    )

    return True, "Задание выполнено! Награда начислена."
