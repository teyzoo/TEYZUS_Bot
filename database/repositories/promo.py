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

    code = code.strip().upper()

    if not code:
        return None

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
) -> PromoCode | None:

    result = await session.execute(
        select(PromoCode).where(
            PromoCode.id == promo_id
        )
    )

    return result.scalar_one_or_none()


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
        max_activations_per_user=max_activations_per_user,
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
# LIST PROMOS
# =========================================================

async def list_promos(
    session: AsyncSession,
    include_inactive: bool = True,
) -> list[PromoCode]:

    query = select(PromoCode).order_by(
        PromoCode.created_at.desc()
    )

    if not include_inactive:
        query = query.where(
            PromoCode.is_active.is_(True)
        )

    result = await session.execute(query)

    return list(
        result.scalars().all()
    )


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

    now = utc_now()

    # =====================================================
    # BASIC STATUS
    # =====================================================

    if not promo.is_active:
        raise ValueError(
            "Промокод отключён."
        )

    # =====================================================
    # START DATE
    # =====================================================

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

    # =====================================================
    # EXPIRE DATE
    # =====================================================

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

    # =====================================================
    # GLOBAL LIMIT
    # =====================================================

    if promo.max_activations is not None:

        if (
            promo.activations_count
            >= promo.max_activations
        ):
            raise ValueError(
                "Лимит активаций исчерпан."
            )

    # =====================================================
    # USER ACTIVATIONS
    # =====================================================

    user_activation_result = await session.execute(
        select(PromoActivation).where(
            PromoActivation.promo_id == promo.id,
            PromoActivation.user_id == user.id,
        )
    )

    user_activations = list(
        user_activation_result.scalars().all()
    )

    if (
        promo.max_activations_per_user is not None
        and len(user_activations)
        >= promo.max_activations_per_user
    ):
        raise ValueError(
            "Ты уже использовал этот промокод "
            "максимальное количество раз."
        )

    # =====================================================
    # NEW USERS
    # =====================================================

    if promo.only_new_users:

        if user_activations:
            raise ValueError(
                "Этот промокод доступен только новым пользователям."
            )

    # =====================================================
    # ALLOWED USERS
    # =====================================================

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

    # =====================================================
    # PREMIUM ONLY
    # =====================================================

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

    # =====================================================
    # APPLY REWARD
    # =====================================================

    if promo.reward_type == "premium":

        if promo.premium_days <= 0:
            raise ValueError(
                "Промокод содержит некорректную Premium-награду."
            )

        current_until = user.premium_until

        if (
            not user.premium_active
            or current_until is None
            or current_until < now
        ):
            current_until = now

        user.premium_until = (
            current_until
            + __import__("datetime").timedelta(
                days=promo.premium_days
            )
        )

        user.premium_active = True

    elif promo.reward_type == "stars":

        if promo.reward_amount <= 0:
            raise ValueError(
                "Некорректное количество Stars."
            )

        user.stars_balance += (
            promo.reward_amount
        )

    elif promo.reward_type == "balance_rub":

        if promo.reward_amount <= 0:
            raise ValueError(
                "Некорректное количество рублей."
            )

        user.balance_rub += (
            promo.reward_amount
        )

    elif promo.reward_type == "searches":

        if promo.reward_amount <= 0:
            raise ValueError(
                "Некорректное количество поисков."
            )

        user.successful_searches_today += (
            promo.reward_amount
        )

    elif promo.reward_type == "traps":

        if promo.reward_amount <= 0:
            raise ValueError(
                "Некорректное количество ловушек."
            )

        # Пока в User нет отдельного поля
        # для количества ловушек.
        #
        # Поэтому здесь намеренно не изменяем
        # несуществующее поле.
        #
        # Поле traps_balance добавим,
        # когда подключим полноценную Trap System.

    else:
        raise ValueError(
            "Неизвестный тип награды."
        )

    # =====================================================
    # CREATE ACTIVATION
    # =====================================================

    activation = PromoActivation(
        promo_id=promo.id,
        user_id=user.id,
        telegram_id=user.telegram_id,
        reward_type=promo.reward_type,
        reward_amount=promo.reward_amount,
        premium_days=promo.premium_days,
        activated_at=now,
    )

    session.add(activation)

    # =====================================================
    # UPDATE COUNTER
    # =====================================================

    promo.activations_count += 1

    # =====================================================
    # SAVE
    # =====================================================

    try:

        await session.commit()

    except Exception:

        await session.rollback()

        raise

    await session.refresh(activation)

    return activation
