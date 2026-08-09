from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    PromoActivation,
    PromoCode,
    User,
)


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
            PromoCode.code == code.upper().strip()
        )
    )

    return result.scalar_one_or_none()


# =========================================================
# COUNT USER ACTIVATIONS
# =========================================================

async def count_user_promo_activations(
    session: AsyncSession,
    promo_id: int,
    user_id: int,
) -> int:

    result = await session.execute(
        select(
            func.count(PromoActivation.id)
        ).where(
            PromoActivation.promo_id == promo_id,
            PromoActivation.user_id == user_id,
        )
    )

    return int(result.scalar_one() or 0)


# =========================================================
# ACTIVATE PROMO
# =========================================================

async def activate_promo(
    session: AsyncSession,
    promo: PromoCode,
    user: User,
) -> PromoActivation:

    # -----------------------------------------------------
    # LOCK PROMO ROW
    # -----------------------------------------------------

    result = await session.execute(
        select(PromoCode)
        .where(
            PromoCode.id == promo.id
        )
        .with_for_update()
    )

    promo = result.scalar_one_or_none()

    if promo is None:
        raise ValueError(
            "Промокод не найден."
        )

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
                "Лимит активаций промокода исчерпан."
            )

    # -----------------------------------------------------
    # USER LIMIT
    # -----------------------------------------------------

    user_activations = (
        await count_user_promo_activations(
            session=session,
            promo_id=promo.id,
            user_id=user.id,
        )
    )

    if (
        promo.max_activations_per_user
        is not None
        and user_activations
        >= promo.max_activations_per_user
    ):
        raise ValueError(
            "Ты уже использовал этот промокод "
            "максимальное количество раз."
        )

    # -----------------------------------------------------
    # PREMIUM ONLY
    # -----------------------------------------------------

    if promo.only_premium:

        premium_active = user.premium_active

        if user.premium_until is not None:

            premium_until = user.premium_until

            if premium_until.tzinfo is None:
                premium_until = (
                    premium_until.replace(
                        tzinfo=timezone.utc
                    )
                )

            premium_active = (
                premium_active
                and premium_until > now
            )

        if not premium_active:
            raise ValueError(
                "Этот промокод доступен только "
                "Premium пользователям."
            )

    # -----------------------------------------------------
    # NEW USERS
    # -----------------------------------------------------

    if promo.only_new_users:

        # Пользователь считается новым,
        # если он зарегистрирован менее 24 часов назад.

        created_at = user.created_at

        if created_at.tzinfo is None:
            created_at = created_at.replace(
                tzinfo=timezone.utc
            )

        age_seconds = (
            now - created_at
        ).total_seconds()

        if age_seconds > 24 * 60 * 60:
            raise ValueError(
                "Этот промокод доступен только "
                "новым пользователям."
            )

    # -----------------------------------------------------
    # ALLOWED USERS
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
                "Этот промокод недоступен "
                "твоему аккаунту."
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
    # INCREMENT COUNTER
    # -----------------------------------------------------

    promo.activations_count += 1

    # -----------------------------------------------------
    # APPLY REWARD
    # -----------------------------------------------------

    if promo.reward_type == "premium":

        if promo.premium_days <= 0:
            raise ValueError(
                "Неверное количество дней Premium."
            )

        if (
            user.premium_until is not None
            and user.premium_until > now
        ):

            user.premium_until = (
                user.premium_until
                + __import__(
                    "datetime"
                ).timedelta(
                    days=promo.premium_days
                )
            )

        else:

            user.premium_until = (
                now
                + __import__(
                    "datetime"
                ).timedelta(
                    days=promo.premium_days
                )
            )

        user.premium_active = True

    elif promo.reward_type == "stars":

        if promo.reward_amount <= 0:
            raise ValueError(
                "Неверное количество Stars."
            )

        user.stars_balance += (
            promo.reward_amount
        )

    elif promo.reward_type == "balance_rub":

        if promo.reward_amount <= 0:
            raise ValueError(
                "Неверная сумма рублей."
            )

        user.balance_rub += (
            promo.reward_amount
        )

    elif promo.reward_type == "searches":

        if promo.reward_amount <= 0:
            raise ValueError(
                "Неверное количество поисков."
            )

        user.successful_searches_today += (
            promo.reward_amount
        )

    elif promo.reward_type == "traps":

        if promo.reward_amount <= 0:
            raise ValueError(
                "Неверное количество ловушек."
            )

        # Пока в User нет поля trap_balance.
        # Поэтому эта награда требует отдельного
        # поля/таблицы ловушек.

        raise ValueError(
            "Система ловушек ещё не подключена."
        )

    else:

        raise ValueError(
            "Неизвестный тип награды."
        )

    await session.commit()

    await session.refresh(
        activation
    )

    return activation


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
                "Количество дней Premium "
                "должно быть больше 0."
            )

    else:

        if reward_amount <= 0:
            raise ValueError(
                "Количество награды "
                "должно быть больше 0."
            )

    existing = await get_promo_by_code(
        session=session,
        code=code,
    )

    if existing is not None:
        raise ValueError(
            "Такой промокод уже существует."
        )

    if (
        max_activations is not None
        and max_activations <= 0
    ):
        raise ValueError(
            "Общий лимит должен быть больше 0."
        )

    if (
        max_activations_per_user is not None
        and max_activations_per_user <= 0
    ):
        raise ValueError(
            "Лимит на пользователя "
            "должен быть больше 0."
        )

    if (
        starts_at is not None
        and expires_at is not None
        and expires_at <= starts_at
    ):
        raise ValueError(
            "Дата окончания должна быть "
            "позже даты начала."
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
# DEACTIVATE
# =========================================================

async def deactivate_promo(
    session: AsyncSession,
    promo_id: int,
) -> bool:

    result = await session.execute(
        select(PromoCode).where(
            PromoCode.id == promo_id
        )
    )

    promo = (
        result.scalar_one_or_none()
    )

    if promo is None:
        return False

    promo.is_active = False

    await session.commit()

    return True
