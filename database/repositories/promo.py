from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    PromoActivation,
    PromoCode,
    User,
)


# =========================================================
# TIME
# =========================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# =========================================================
# GET PROMO
# =========================================================

async def get_promo_by_code(
    session: AsyncSession,
    code: str,
) -> PromoCode | None:

    result = await session.execute(
        select(PromoCode).where(
            PromoCode.code == code.strip().upper()
        )
    )

    return result.scalar_one_or_none()


async def get_promo_by_id(
    session: AsyncSession,
    promo_id: int,
) -> PromoCode | None:

    result = await session.execute(
        select(PromoCode).where(
            PromoCode.id == promo_id
        )
    )

    return result.scalar_one_or_none()


# =========================================================
# LIST PROMOS
# =========================================================

async def list_promos(
    session: AsyncSession,
) -> list[PromoCode]:

    result = await session.execute(
        select(PromoCode)
        .order_by(
            PromoCode.created_at.desc()
        )
    )

    return list(
        result.scalars().all()
    )


# =========================================================
# CREATE PROMO
# =========================================================

async def create_promo(
    session: AsyncSession,
    code: str,
    reward_type: str,
    reward_amount: int = 0,
    premium_days: int = 0,
    max_activations: int | None = None,
    max_activations_per_user: int | None = None,
    starts_at: datetime | None = None,
    expires_at: datetime | None = None,
    only_new_users: bool = False,
    only_premium: bool = False,
    allowed_user_ids: str | None = None,
    created_by: int = 0,
) -> PromoCode:

    code = code.strip().upper()

    if not code:
        raise ValueError(
            "Промокод не может быть пустым."
        )

    if len(code) > 128:
        raise ValueError(
            "Максимальная длина промокода — 128 символов."
        )

    allowed_rewards = {
        "premium",
        "stars",
        "balance_rub",
        "searches",
        "traps",
    }

    if reward_type not in allowed_rewards:
        raise ValueError(
            "Неизвестный тип награды."
        )

    if reward_type == "premium":
        if premium_days <= 0:
            raise ValueError(
                "Количество дней Premium должно быть больше 0."
            )

        reward_amount = 0

    else:
        if reward_amount <= 0:
            raise ValueError(
                "Количество награды должно быть больше 0."
            )

        premium_days = 0

    if (
        max_activations is not None
        and max_activations <= 0
    ):
        raise ValueError(
            "Общий лимит активаций должен быть больше 0."
        )

    if (
        max_activations_per_user is not None
        and max_activations_per_user <= 0
    ):
        raise ValueError(
            "Лимит на пользователя должен быть больше 0."
        )

    if (
        starts_at is not None
        and expires_at is not None
        and expires_at <= starts_at
    ):
        raise ValueError(
            "Дата окончания должна быть позже даты начала."
        )

    existing_result = await session.execute(
        select(PromoCode).where(
            PromoCode.code == code
        )
    )

    existing = (
        existing_result.scalar_one_or_none()
    )

    if existing is not None:
        raise ValueError(
            "Такой промокод уже существует."
        )

    promo = PromoCode(
        code=code,
        reward_type=reward_type,
        reward_amount=reward_amount,
        premium_days=premium_days,
        max_activations=max_activations,
        max_activations_per_user=(
            max_activations_per_user
        ),
        activations_count=0,
        starts_at=starts_at,
        expires_at=expires_at,
        only_new_users=only_new_users,
        only_premium=only_premium,
        allowed_user_ids=allowed_user_ids,
        is_active=True,
        created_by=created_by,
    )

    session.add(promo)

    await session.commit()
    await session.refresh(promo)

    return promo


# =========================================================
# DEACTIVATE
# =========================================================

async def deactivate_promo(
    session: AsyncSession,
    promo_id: int,
) -> bool:

    promo = await get_promo_by_id(
        session=session,
        promo_id=promo_id,
    )

    if promo is None:
        return False

    promo.is_active = False

    await session.commit()

    return True


# =========================================================
# USER ACTIVATION COUNT
# =========================================================

async def get_user_promo_activation_count(
    session: AsyncSession,
    promo_id: int,
    user_id: int,
) -> int:

    result = await session.execute(
        select(PromoActivation).where(
            PromoActivation.promo_id == promo_id,
            PromoActivation.user_id == user_id,
        )
    )

    activations = list(
        result.scalars().all()
    )

    return len(activations)


# =========================================================
# ACTIVATE PROMO
# =========================================================

async def activate_promo(
    session: AsyncSession,
    promo: PromoCode,
    user: User,
) -> PromoActivation:

    # -----------------------------------------------------
    # Refresh promo/user
    # -----------------------------------------------------

    await session.refresh(promo)
    await session.refresh(user)

    # -----------------------------------------------------
    # Active
    # -----------------------------------------------------

    if not promo.is_active:
        raise ValueError(
            "Промокод отключён."
        )

    # -----------------------------------------------------
    # Global limit
    # -----------------------------------------------------

    if (
        promo.max_activations is not None
        and promo.activations_count
        >= promo.max_activations
    ):
        raise ValueError(
            "Лимит активаций промокода исчерпан."
        )

    # -----------------------------------------------------
    # User limit
    # -----------------------------------------------------

    user_activation_count = (
        await get_user_promo_activation_count(
            session=session,
            promo_id=promo.id,
            user_id=user.id,
        )
    )

    if (
        promo.max_activations_per_user is not None
        and user_activation_count
        >= promo.max_activations_per_user
    ):
        raise ValueError(
            "Ты уже использовал этот промокод максимально разрешённое количество раз."
        )

    # -----------------------------------------------------
    # New users
    # -----------------------------------------------------

    if promo.only_new_users:

        existing_result = await session.execute(
            select(PromoActivation.id)
            .where(
                PromoActivation.user_id == user.id
            )
            .limit(1)
        )

        existing_activation = (
            existing_result.scalar_one_or_none()
        )

        if existing_activation is not None:
            raise ValueError(
                "Этот промокод доступен только новым пользователям."
            )

    # -----------------------------------------------------
    # Allowed users
    # -----------------------------------------------------

    if promo.allowed_user_ids:

        allowed_ids = set()

        for item in promo.allowed_user_ids.split(","):

            item = item.strip()

            if not item:
                continue

            try:
                allowed_ids.add(
                    int(item)
                )
            except ValueError:
                continue

        if user.telegram_id not in allowed_ids:
            raise ValueError(
                "Этот промокод недоступен для твоего Telegram ID."
            )

    # -----------------------------------------------------
    # Apply reward
    # -----------------------------------------------------

    if promo.reward_type == "premium":

        now = utc_now()

        current_until = user.premium_until

        if (
            current_until is None
            or current_until < now
            or not user.premium_active
        ):
            base_date = now
        else:
            base_date = current_until

        from datetime import timedelta

        user.premium_until = (
            base_date
            + timedelta(
                days=promo.premium_days
            )
        )

        user.premium_active = True

    elif promo.reward_type == "stars":

        user.stars_balance += (
            promo.reward_amount
        )

    elif promo.reward_type == "balance_rub":

        user.balance_rub += (
            promo.reward_amount
        )

    elif promo.reward_type == "searches":

        user.successful_searches_today += (
            promo.reward_amount
        )

    elif promo.reward_type == "traps":

        # В текущей модели User отдельного
        # trap-баланса ещё нет.
        #
        # Поэтому эту награду пока нельзя
        # корректно сохранить.
        #
        # Не создаём активацию, чтобы пользователь
        # не потерял награду.

        raise ValueError(
            "Награда «ловушки» пока не подключена к базе данных."
        )

    else:

        raise ValueError(
            "Неизвестный тип награды."
        )

    # -----------------------------------------------------
    # Activation
    # -----------------------------------------------------

    activation = PromoActivation(
        promo_id=promo.id,
        user_id=user.id,
        telegram_id=user.telegram_id,
        reward_type=promo.reward_type,
        reward_amount=promo.reward_amount,
        premium_days=promo.premium_days,
    )

    session.add(activation)

    # -----------------------------------------------------
    # Counter
    # -----------------------------------------------------

    promo.activations_count += 1

    # -----------------------------------------------------
    # Commit
    # -----------------------------------------------------

    await session.commit()

    await session.refresh(
        activation
    )

    return activation
