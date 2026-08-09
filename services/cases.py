from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    Case,
    CaseReward,
    CaseOpen,
    User,
)


# =========================================================
# TIME
# =========================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# =========================================================
# GET CASE
# =========================================================

async def get_case(
    session: AsyncSession,
    case_id: int,
) -> Case | None:

    result = await session.execute(
        select(Case).where(
            Case.id == case_id,
            Case.is_active.is_(True),
        )
    )

    return result.scalar_one_or_none()


# =========================================================
# GET REWARDS
# =========================================================

async def get_case_rewards(
    session: AsyncSession,
    case_id: int,
) -> list[CaseReward]:

    result = await session.execute(
        select(CaseReward)
        .where(
            CaseReward.case_id == case_id,
            CaseReward.is_active.is_(True),
        )
        .order_by(
            CaseReward.sort_order.asc(),
            CaseReward.id.asc(),
        )
    )

    return list(result.scalars().all())


# =========================================================
# VALIDATE CHANCES
# =========================================================

def validate_chances(
    rewards: list[CaseReward],
) -> tuple[bool, float]:

    total = sum(
        float(reward.chance)
        for reward in rewards
    )

    return (
        abs(total - 100.0) < 0.0001,
        total,
    )


# =========================================================
# RANDOM REWARD
# =========================================================

def choose_reward(
    rewards: list[CaseReward],
) -> CaseReward:

    if not rewards:
        raise ValueError(
            "У кейса нет наград."
        )

    valid, total = validate_chances(
        rewards
    )

    if not valid:
        raise ValueError(
            f"Сумма шансов должна быть 100%. "
            f"Сейчас: {total:.2f}%"
        )

    value = random.uniform(
        0,
        100,
    )

    current = 0.0

    for reward in rewards:
        current += float(
            reward.chance
        )

        if value <= current:
            return reward

    return rewards[-1]


# =========================================================
# APPLY REWARD
# =========================================================

async def apply_reward(
    user: User,
    reward: CaseReward,
) -> None:

    reward_type = (
        reward.reward_type
        .strip()
        .lower()
    )

    amount = int(
        reward.reward_amount
    )

    # -----------------------------------------------------
    # STARS
    # -----------------------------------------------------

    if reward_type == "stars":

        user.stars_balance += amount

    # -----------------------------------------------------
    # RUB
    # -----------------------------------------------------

    elif reward_type == "balance":

        user.balance_rub += amount

    # -----------------------------------------------------
    # SEARCHES
    # -----------------------------------------------------

    elif reward_type == "searches":

        user.bonus_searches += amount

    # -----------------------------------------------------
    # TRAPS
    # -----------------------------------------------------

    elif reward_type == "traps":

        user.bonus_traps += amount

    # -----------------------------------------------------
    # DISCOUNT
    # -----------------------------------------------------

    elif reward_type == "discount":

        user.discount_percent = min(
            100,
            user.discount_percent + amount,
        )

    # -----------------------------------------------------
    # PREMIUM
    # -----------------------------------------------------

    elif reward_type == "premium":

        days = int(
            reward.premium_days
        )

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
            + timedelta(days=days)
        )

        user.premium_active = True

    else:

        raise ValueError(
            f"Неизвестный тип награды: "
            f"{reward.reward_type}"
        )


# =========================================================
# OPEN CASE
# =========================================================

async def open_case(
    session: AsyncSession,
    user: User,
    case_id: int,
) -> CaseOpen:

    case = await get_case(
        session,
        case_id,
    )

    if case is None:
        raise ValueError(
            "Кейс не найден или отключён."
        )

    rewards = await get_case_rewards(
        session,
        case.id,
    )

    if not rewards:
        raise ValueError(
            "В кейсе пока нет наград."
        )

    valid, total = validate_chances(
        rewards
    )

    if not valid:
        raise ValueError(
            f"Ошибка настроек кейса: "
            f"сумма шансов {total:.2f}%, "
            f"а должна быть 100%."
        )

    if case.price_stars <= 0:
        raise ValueError(
            "Цена кейса настроена неправильно."
        )

    # -----------------------------------------------------
    # CHECK BALANCE
    # -----------------------------------------------------

    if user.stars_balance < case.price_stars:
        raise ValueError(
            "Недостаточно Stars для открытия кейса."
        )

    # -----------------------------------------------------
    # CHARGE
    # -----------------------------------------------------

    user.stars_balance -= (
        case.price_stars
    )

    # -----------------------------------------------------
    # CHOOSE
    # -----------------------------------------------------

    reward = choose_reward(
        rewards
    )

    # -----------------------------------------------------
    # APPLY
    # -----------------------------------------------------

    await apply_reward(
        user,
        reward,
    )

    # -----------------------------------------------------
    # HISTORY
    # -----------------------------------------------------

    opened = CaseOpen(
        case_id=case.id,
        reward_id=reward.id,
        user_id=user.id,
        telegram_id=user.telegram_id,
        reward_type=reward.reward_type,
        reward_title=reward.title,
        reward_amount=reward.reward_amount,
        premium_days=reward.premium_days,
        reward_chance=reward.chance,
    )

    session.add(opened)

    await session.commit()

    await session.refresh(
        opened
    )

    return opened
