from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import (
    User,
    Task,
    TaskCompletion,
)

from database.repositories.tasks import (
    get_task,
    get_active_tasks,
    get_user_task_completion_count,
    create_task_completion,
)


# =========================================================
# TIME
# =========================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# =========================================================
# TASK RESULT
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
# PREMIUM ACTIVE
# =========================================================

def is_premium_active(
    user: User,
) -> bool:

    if not user.premium_active:
        return False

    if user.premium_until is None:
        return True

    now = utc_now()

    if user.premium_until <= now:
        return False

    return True


# =========================================================
# TASK PERIOD
# =========================================================

def get_period(
    task: Task,
) -> str:

    target = (
        task.target_value or ""
    ).lower()

    if target.startswith(
        "daily:"
    ):
        return "daily"

    if target.startswith(
        "weekly:"
    ):
        return "weekly"

    if target.startswith(
        "monthly:"
    ):
        return "monthly"

    return "permanent"


# =========================================================
# TASK ACCESS
# =========================================================

def can_user_see_task(
    user: User,
    task: Task,
) -> bool:

    if not task.is_active:
        return False

    now = utc_now()

    if (
        task.starts_at is not None
        and task.starts_at > now
    ):
        return False

    if (
        task.expires_at is not None
        and task.expires_at < now
    ):
        return False

    if task.only_premium:
        if not is_premium_active(
            user
        ):
            return False

    if task.only_new_users:
        # Условие "нового пользователя"
        # можно изменить позже.
        age = (
            now - user.created_at
        )

        if age > timedelta(
            days=7
        ):
            return False

    if (
        task.max_completions
        is not None
    ):
        if (
            task.completions_count
            >= task.max_completions
        ):
            return False

    return True


# =========================================================
# CAN COMPLETE
# =========================================================

async def can_complete_task(
    session: AsyncSession,
    user: User,
    task: Task,
) -> tuple[bool, str]:

    if not can_user_see_task(
        user,
        task,
    ):
        return (
            False,
            "Это задание сейчас недоступно.",
        )

    count = (
        await get_user_task_completion_count(
            session,
            task.id,
            user.id,
        )
    )

    if not task.repeatable:

        if count > 0:
            return (
                False,
                "Ты уже выполнял это задание.",
            )

    if (
        task.max_completions_per_user
        is not None
    ):

        if (
            count
            >= task.max_completions_per_user
        ):
            return (
                False,
                "Лимит выполнения этого задания исчерпан.",
            )

    return (
        True,
        "OK",
    )


# =========================================================
# APPLY PREMIUM
# =========================================================

def apply_premium_reward(
    user: User,
    days: int,
) -> None:

    if days <= 0:
        return

    now = utc_now()

    if (
        user.premium_until is not None
        and user.premium_until > now
        and user.premium_active
    ):
        base = user.premium_until
    else:
        base = now

    user.premium_until = (
        base + timedelta(
            days=days
        )
    )

    user.premium_active = True


# =========================================================
# APPLY REWARD
# =========================================================

def apply_reward(
    user: User,
    reward_type: str,
    reward_amount: int,
    premium_days: int,
) -> None:

    reward_type = (
        reward_type
        .strip()
        .lower()
    )

    if reward_type in (
        "stars",
        "star",
        "telegram_stars",
    ):
        user.stars_balance += (
            reward_amount
        )

    elif reward_type in (
        "balance",
        "rub",
        "rubles",
        "balance_rub",
    ):
        user.balance_rub += (
            reward_amount
        )

    elif reward_type in (
        "search",
        "searches",
        "bonus_searches",
    ):
        user.bonus_searches += (
            reward_amount
        )

    elif reward_type in (
        "trap",
        "traps",
        "bonus_traps",
    ):
        user.bonus_traps += (
            reward_amount
        )

    elif reward_type in (
        "discount",
        "discount_percent",
    ):
        new_discount = (
            user.discount_percent
            + reward_amount
        )

        user.discount_percent = min(
            new_discount,
            100,
        )

    elif reward_type in (
        "premium",
        "premium_days",
    ):
        apply_premium_reward(
            user,
            premium_days
            if premium_days > 0
            else reward_amount,
        )


# =========================================================
# COMPLETE TASK
# =========================================================

async def complete_task(
    session: AsyncSession,
    user: User,
    task_id: int,
) -> TaskResult:

    task = await get_task(
        session,
        task_id,
    )

    if task is None:
        return TaskResult(
            False,
            "Задание не найдено.",
        )

    allowed, message = (
        await can_complete_task(
            session,
            user,
            task,
        )
    )

    if not allowed:
        return TaskResult(
            False,
            message,
        )

    # =====================================================
    # REWARD
    # =====================================================

    apply_reward(
        user=user,
        reward_type=task.reward_type,
        reward_amount=task.reward_amount,
        premium_days=task.premium_days,
    )

    # =====================================================
    # COMPLETION
    # =====================================================

    await create_task_completion(
        session=session,
        task=task,
        user_id=user.id,
        telegram_id=user.telegram_id,
    )

    # =====================================================
    # AUTO DISABLE
    # =====================================================

    if (
        task.max_completions
        is not None
        and task.completions_count
        >= task.max_completions
    ):
        task.is_active = False

    await session.commit()

    # =====================================================
    # MESSAGE
    # =====================================================

    reward_text = (
        format_reward(
            task.reward_type,
            task.reward_amount,
            task.premium_days,
        )
    )

    return TaskResult(
        success=True,
        message=(
            "🎉 Задание выполнено!\n\n"
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

    reward_type = (
        reward_type
        .strip()
        .lower()
    )

    if reward_type in (
        "stars",
        "star",
        "telegram_stars",
    ):
        return (
            f"⭐ {amount} Stars"
        )

    if reward_type in (
        "balance",
        "rub",
        "rubles",
        "balance_rub",
    ):
        return (
            f"💰 {amount:,} ₽"
            .replace(",", " ")
        )

    if reward_type in (
        "search",
        "searches",
        "bonus_searches",
    ):
        return (
            f"🔎 +{amount} поисков"
        )

    if reward_type in (
        "trap",
        "traps",
        "bonus_traps",
    ):
        return (
            f"🎯 +{amount} ловушек"
        )

    if reward_type in (
        "discount",
        "discount_percent",
    ):
        return (
            f"🏷️ -{amount}% скидки"
        )

    if reward_type in (
        "premium",
        "premium_days",
    ):
        days = (
            premium_days
            if premium_days > 0
            else amount
        )

        return (
            f"💎 Premium на {days} дн."
        )

    return (
        f"🎁 {amount}"
    )


# =========================================================
# USER TASKS
# =========================================================

async def get_user_tasks(
    session: AsyncSession,
    user: User,
) -> list[dict]:

    tasks = await get_active_tasks(
        session
    )

    result: list[dict] = []

    for task in tasks:

        if not can_user_see_task(
            user,
            task,
        ):
            continue

        count = (
            await get_user_task_completion_count(
                session,
                task.id,
                user.id,
            )
        )

        completed = (
            count > 0
            and not task.repeatable
        )

        if (
            task.max_completions_per_user
            is not None
            and count
            >= task.max_completions_per_user
        ):
            completed = True

        result.append(
            {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "task_type": task.task_type,
                "target_value": task.target_value,
                "reward_type": task.reward_type,
                "reward_amount": task.reward_amount,
                "premium_days": task.premium_days,
                "period": get_period(task),
                "repeatable": task.repeatable,
                "completed": completed,
                "completions": count,
                "max_completions_per_user": (
                    task.max_completions_per_user
                ),
                "only_premium": task.only_premium,
                "image_file_id": task.image_file_id,
            }
        )

    return result
