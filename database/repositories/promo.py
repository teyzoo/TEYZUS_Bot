from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

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
) -> Optional[PromoCode]:

    code = code.strip().upper()

    result = await session.execute(
        select(PromoCode).where(
            PromoCode.code == code
        )
    )

    return result.scalar_one_or_none()


# =========================================================
# GET PROMO BY ID
# =========================================================

async def get_promo_by_id(
    session: AsyncSession,
    promo_id: int,
) -> Optional[PromoCode]:

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
    max_activations: Optional[int] = None,
    max_activations_per_user: Optional[int] = None,
    starts_at: Optional[datetime] = None,
    expires_at: Optional[datetime] = None,
    only_new_users: bool = False,
    only_premium: bool = False,
    allowed_user_ids: Optional[str] = None,
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

    if reward_type not in {
        "premium",
        "stars",
        "balance_rub",
        "searches",
        "traps",
    }:
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

    if max_activations is not None:

        if max_activations <= 0:
            raise ValueError(
                "Общий лимит активаций должен быть больше 0."
            )

    if max_activations_per_user is not None:

        if max_activations_per_user <= 0:
            raise ValueError(
                "Лимит активаций на пользователя "
                "должен быть больше 0."
            )

    if (
        starts_at is not None
        and expires_at is not None
        and expires_at <= starts_at
    ):
        raise ValueError(
            "Дата окончания должна быть позже даты начала."
        )

    existing = await get_promo_by_code(
        session=session,
        code=code,
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
# DEACTIVATE PROMO
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
# ACTIVATE PROMO
# =========================================================

async def activate_promo(
    session: AsyncSession,
    promo: PromoCode,
    user: User,
) -> PromoActivation:

    # -----------------------------------------------------
    # ACTIVE
    # -----------------------------------------------------

    if not promo.is_active:
        raise ValueError(
            "Промокод отключён."
        )

    # -----------------------------------------------------
    # TIME
    # -----------------------------------------------------

    now = utc_now()

    if promo.starts_at is not None:

        starts_at = promo.starts_at

        if starts_at.tzinfo is None:
            starts_at = starts_at.replace(
                tzinfo=timezone.utc
            )

        if now < starts_at:
            raise ValueError(
                "Промокод ещё не активен."
            )

    if promo.expires_at is not None:

        expires_at = promo.expires_at

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(
                tzinfo=timezone.utc
            )

        if now > expires_at:
            raise ValueError(
                "Срок действия промокода истёк."
            )

    # -----------------------------------------------------
    # GLOBAL LIMIT
    # -----------------------------------------------------

    if promo.max_activations is not None:

        if (
            promo.activations_count
            >= promo.max_activations
        ):
            raise ValueError(
                "Лимит активаций исчерпан."
            )

    # -----------------------------------------------------
    # USER ACTIVATIONS
    # -----------------------------------------------------

    user_activation_result = await session.execute(
        select(PromoActivation)
        .where(
            PromoActivation.promo_id == promo.id,
            PromoActivation.user_id == user.id,
        )
        .order_by(
            PromoActivation.activated_at.asc()
        )
    )

    user_activations = list(
        user_activation_result.scalars().all()
    )

    if promo.max_activations_per_user is not None:

        if (
            len(user_activations)
            >= promo.max_activations_per_user
        ):
            raise ValueError(
                "Ты уже использовал этот промокод "
                "максимальное количество раз."
            )

    # -----------------------------------------------------
    # NEW USERS
    # -----------------------------------------------------

    if promo.only_new_users:

        if user_activations:
            raise ValueError(
                "Этот промокод доступен только новым пользователям."
            )

    # -----------------------------------------------------
    # PREMIUM ONLY
    # -----------------------------------------------------

    if promo.only_premium:

        premium_active = user.premium_active

        if user.premium_until is not None:

            premium_until = user.premium_until

            if premium_until.tzinfo is None:
                premium_until = premium_until.replace(
                    tzinfo=timezone.utc
                )

            premium_active = (
                premium_active
                and premium_until > now
            )

        if not premium_active:
            raise ValueError(
                "Этот промокод доступен только Premium пользователям."
            )

    # -----------------------------------------------------
    # ALLOWED USERS
    # -----------------------------------------------------

    if promo.allowed_user_ids:

        allowed_ids: set[int] = set()

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
                "Этот промокод недоступен тебе."
            )

    # -----------------------------------------------------
    # CREATE ACTIVATION
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
    # APPLY REWARD
    # -----------------------------------------------------

    if promo.reward_type == "stars":

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

    elif promo.reward_type == "premium":

        user.premium_active = True

        current_until = user.premium_until

        if (
            current_until is None
            or current_until < now
        ):
            current_until = now

        from datetime import timedelta

        user.premium_until = (
            current_until
            + timedelta(
                days=promo.premium_days
            )
        )

    elif promo.reward_type == "traps":

        # Поле traps будет добавлено
        # в модель пользователя отдельным этапом.
        #
        # Пока награда фиксируется
        # в PromoActivation.
        pass

    else:

        raise ValueError(
            "Неизвестный тип награды."
        )

    # -----------------------------------------------------
    # UPDATE COUNTER
    # -----------------------------------------------------

    promo.activations_count += 1

    await session.commit()
    await session.refresh(activation)
    await session.refresh(promo)
    await session.refresh(user)

    return activation
