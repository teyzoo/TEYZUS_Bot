from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Task, User

from database.repositories.tasks import (
    create_completion,
    get_last_completion,
    get_task,
    get_user_task_completion_count,
    global_limit_reached,
    increment_task_completions,
    user_limit_reached,
)


# =========================================================
# TIME
# =========================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# =========================================================
# RESULT
# =========================================================

class TaskResult:
    def __init__(
        self,
        success: bool,
        message: str,
        reward_type: Optional[str] = None,
        reward_amount: int = 0,
        premium_days: int = 0,
    ):
        self.success = success
        self.message = message
        self.reward_type = reward_type
        self.reward_amount = reward_amount
        self.premium_days = premium_days


# =========================================================
# PREMIUM
# =========================================================

def is_premium_active(
    user: User,
) -> bool:

    if not user.premium_active:
        return False

    if not user.premium_until:
        return True

    return (
        user.premium_until
        > utc_now()
    )


# =========================================================
# PREMIUM REWARD
# =========================================================

def add_premium(
    user: User,
    days: int,
) -> None:

    if days <= 0:
        return

    now = utc_now()

    if (
        user.premium_active
        and user.premium_until
        and user.premium_until > now
    ):
        start = user.premium_until
    else:
        start = now

    user.premium_active = True

    user.premium_until = (
        start
        + timedelta(days=days)
    )


# =========================================================
# REWARD
# =========================================================

def apply_reward(
    user: User,
    reward_type: str,
    amount: int,
    premium_days: int,
) -> None:

    reward = reward_type.lower().strip()

    # -----------------------------------------------------
    # STARS
    # -----------------------------------------------------

    if reward in {
        "stars",
        "star",
        "telegram_stars",
    }:
        user.stars_balance += max(
            0,
            amount,
        )
        return

    # -----------------------------------------------------
    # RUB
    # -----------------------------------------------------

    if reward in {
        "rub",
        "balance",
        "balance_rub",
        "money",
    }:
        user.balance_rub += max(
            0,
            amount,
        )
        return

    # -----------------------------------------------------
    # SEARCHES
    # -----------------------------------------------------

    if reward in {
        "search",
        "searches",
        "bonus_searches",
    }:
        user.bonus_searches += max(
            0,
            amount,
        )
        return

    # -----------------------------------------------------
    # TRAPS
    # -----------------------------------------------------

    if reward in {
        "trap",
        "traps",
        "bonus_traps",
    }:
        user.bonus_traps += max(
            0,
            amount,
        )
        return

    # -----------------------------------------------------
    # DISCOUNT
    # -----------------------------------------------------

    if reward in {
        "discount",
        "discount_percent",
    }:
        user.discount_percent = min(
            100,
            max(
                0,
                user.discount_percent
                + amount,
            ),
        )
        return

    # -----------------------------------------------------
    # PREMIUM
    # -----------------------------------------------------

    if reward in {
        "premium",
        "premium_days",
    }:
        add_premium(
            user,
            premium_days or amount,
        )
        return


# =========================================================
# CHECK TASK ACCESS
# =========================================================

def check_task_access(
    task: Task,
    user: User,
) -> TaskResult:

    now = utc_now()

    # -----------------------------------------------------
    # ACTIVE
    # -----------------------------------------------------

    if not task.is_active:
        return TaskResult(
            False,
            "❌ Это задание отключено.",
        )

    # -----------------------------------------------------
    # START
    # -----------------------------------------------------

    if (
        task.starts_at
        and task.starts_at > now
    ):
        return TaskResult(
            False,
            "⏳ Это задание ещё не началось.",
        )

    # -----------------------------------------------------
    # EXPIRE
    # -----------------------------------------------------

    if (
        task.expires_at
        and task.expires_at < now
    ):
        return TaskResult(
            False,
            "⌛ Срок выполнения задания истёк.",
        )

    # -----------------------------------------------------
    # PREMIUM ONLY
    # -----------------------------------------------------

    if task.only_premium:
        if not is_premium_active(user):
            return TaskResult(
                False,
                "💎 Это задание доступно только пользователям TEYZUS Premium.",
            )

    # -----------------------------------------------------
    # GLOBAL LIMIT
    # -----------------------------------------------------

    if global_limit_reached(task):
        return TaskResult(
            False,
            "🚫 Лимит выполнений этого задания уже достигнут.",
        )

    return TaskResult(
        True,
        "OK",
    )


# =========================================================
# COMPLETE TASK
# =========================================================

async def complete_task(
    session: AsyncSession,
    *,
    task_id: int,
    user: User,
) -> TaskResult:

    # -----------------------------------------------------
    # TASK
    # -----------------------------------------------------

    task = await get_task(
        session,
        task_id,
    )

    if task is None:
        return TaskResult(
            False,
            "❌ Задание не найдено.",
        )

    # -----------------------------------------------------
    # ACCESS
    # -----------------------------------------------------

    access = check_task_access(
        task,
        user,
    )

    if not access.success:
        return access

    # -----------------------------------------------------
    # USER LIMIT
    # -----------------------------------------------------

    completion_count = (
        await get_user_task_completion_count(
            session,
            user_id=user.id,
            task_id=task.id,
        )
    )

    if (
        not task.repeatable
        and completion_count > 0
    ):
        return TaskResult(
            False,
            "✅ Ты уже выполнил это задание.",
        )

    if user_limit_reached(
        task,
        completion_count,
    ):
        return TaskResult(
            False,
            "🚫 Ты достиг личного лимита выполнения этого задания.",
        )

    # -----------------------------------------------------
    # CREATE COMPLETION
    # -----------------------------------------------------

    completion = await create_completion(
        session,
        task=task,
        user_id=user.id,
        telegram_id=user.telegram_id,
    )

    # -----------------------------------------------------
    # REWARD
    # -----------------------------------------------------

    apply_reward(
        user,
        task.reward_type,
        task.reward_amount,
        task.premium_days,
    )

    # -----------------------------------------------------
    # COUNTER
    # -----------------------------------------------------

    await increment_task_completions(
        session,
        task,
    )

    await session.commit()

    # -----------------------------------------------------
    # MESSAGE
    # -----------------------------------------------------

    reward_text = format_reward(
        task.reward_type,
        task.reward_amount,
        task.premium_days,
    )

    return TaskResult(
        True,
        (
            "🎉 <b>Задание выполнено!</b>\n\n"
            f"🎁 Награда: {reward_text}"
        ),
        reward_type=task.reward_type,
        reward_amount=task.reward_amount,
        premium_days=task.premium_days,
    )


# =========================================================
# FORMAT REWARD
# =========================================================

def format_reward(
    reward_type: str,
    amount: int,
    premium_days: int,
) -> str:

    reward = reward_type.lower().strip()

    if reward in {
        "stars",
        "star",
        "telegram_stars",
    }:
        return f"⭐ +{amount} Stars"

    if reward in {
        "rub",
        "balance",
        "balance_rub",
        "money",
    }:
        return f"💰 +{amount:,} ₽".replace(
            ",",
            " ",
        )

    if reward in {
        "search",
        "searches",
        "bonus_searches",
    }:
        return f"🔎 +{amount} поисков"

    if reward in {
        "trap",
        "traps",
        "bonus_traps",
    }:
        return f"🎯 +{amount} ловушек"

    if reward in {
        "discount",
        "discount_percent",
    }:
        return f"🏷️ +{amount}% скидки"

    if reward in {
        "premium",
        "premium_days",
    }:
        days = premium_days or amount
        return f"💎 Premium на {days} дн."

    return f"🎁 {amount}"
