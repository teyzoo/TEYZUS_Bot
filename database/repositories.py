from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import (
    PromoActivation,
    PromoCode,
    User,
)
# =========================================================
# 👤 USERS
# =========================================================
async def get_user(
    session: AsyncSession,
    telegram_id: int,
) -> User | None:
    result = await session.execute(
        select(User).where(
            User.telegram_id == telegram_id
        )
    )
    return result.scalar_one_or_none()
# =========================================================
# 🎟 PROMO — CREATE
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
                "Количество Premium дней должно быть больше 0."
            )
    else:
        if reward_amount <= 0:
            raise ValueError(
                "Количество награды должно быть больше 0."
            )
    if max_activations is not None:
        if max_activations <= 0:
            raise ValueError(
                "Общий лимит должен быть больше 0."
            )
    if max_activations_per_user is not None:
        if max_activations_per_user <= 0:
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
            func.lower(PromoCode.code)
            == code.lower()
        )
    )
    existing = (
        existing_result.scalar_one_or_none()
    )
    if existing:
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
# 🎟 PROMO — GET
# =========================================================
async def get_promo(
    session: AsyncSession,
    code: str,
) -> PromoCode | None:
    code = code.strip().upper()
    result = await session.execute(
        select(PromoCode).where(
            PromoCode.code == code
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
# 🎟 PROMO — LIST
# =========================================================
async def list_promos(
    session: AsyncSession,
) -> list[PromoCode]:
    result = await session.execute(
        select(PromoCode).order_by(
            PromoCode.created_at.desc()
        )
    )
    return list(
        result.scalars().all()
    )
async def list_active_promos(
    session: AsyncSession,
) -> list[PromoCode]:
    result = await session.execute(
        select(PromoCode)
        .where(
            PromoCode.is_active.is_(True)
        )
        .order_by(
            PromoCode.created_at.desc()
        )
    )
    return list(
        result.scalars().all()
    )
# =========================================================
# 🔴 PROMO — DEACTIVATE
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
# 🟢 PROMO — ACTIVATE CHECK
# =========================================================
async def validate_promo(
    session: AsyncSession,
    promo: PromoCode,
    user: User,
) -> tuple[bool, str]:
    now = datetime.now(
        timezone.utc
    )
    # -----------------------------------------------------
    # ACTIVE
    # -----------------------------------------------------
    if not promo.is_active:
        return (
            False,
            "Этот промокод отключён.",
        )
    # -----------------------------------------------------
    # START DATE
    # -----------------------------------------------------
    if (
        promo.starts_at is not None
        and now < promo.starts_at
    ):
        return (
            False,
            "Этот промокод ещё не активен.",
        )
    # -----------------------------------------------------
    # EXPIRATION
    # -----------------------------------------------------
    if (
        promo.expires_at is not None
        and now >= promo.expires_at
    ):
        return (
            False,
            "Срок действия промокода истёк.",
        )
    # -----------------------------------------------------
    # GLOBAL LIMIT
    # -----------------------------------------------------
    if (
        promo.max_activations is not None
        and promo.activations_count
        >= promo.max_activations
    ):
        return (
            False,
            "Лимит активаций этого промокода исчерпан.",
        )
    # -----------------------------------------------------
    # ONLY NEW USERS
    # -----------------------------------------------------
    if promo.only_new_users:
        # Пользователь считается новым,
        # если аккаунт создан менее суток назад.
        if user.created_at is not None:
            age = now - user.created_at
            if age.total_seconds() > 86400:
                return (
                    False,
                    "Промокод доступен только новым пользователям.",
                )
    # -----------------------------------------------------
    # ONLY PREMIUM
    # -----------------------------------------------------
    if promo.only_premium:
        premium_active = user.premium_active
        if (
            premium_active
            and user.premium_until is not None
            and user.premium_until <= now
        ):
            premium_active = False
        if not premium_active:
            return (
                False,
                "Этот промокод доступен только Premium пользователям.",
            )
    # -----------------------------------------------------
    # ALLOWED USERS
    # -----------------------------------------------------
    if promo.allowed_user_ids:
        allowed = set()
        for item in promo.allowed_user_ids.split(","):
            item = item.strip()
            if not item:
                continue
            try:
                allowed.add(
                    int(item)
                )
            except ValueError:
                continue
        if user.telegram_id not in allowed:
            return (
                False,
                "У тебя нет доступа к этому промокоду.",
            )
    # -----------------------------------------------------
    # PER USER LIMIT
    # -----------------------------------------------------
    if (
        promo.max_activations_per_user
        is not None
    ):
        result = await session.execute(
            select(
                func.count(
                    PromoActivation.id
                )
            ).where(
                PromoActivation.promo_id
                == promo.id,
                PromoActivation.user_id
                == user.id,
            )
        )
        user_activations = int(
            result.scalar_one() or 0
        )
        if (
            user_activations
            >= promo.max_activations_per_user
        ):
            return (
                False,
                "Ты уже использовал этот промокод максимальное количество раз.",
            )
    return (
        True,
        "OK",
    )
# =========================================================
# 🎁 PROMO — ACTIVATE
# =========================================================
async def activate_promo(
    session: AsyncSession,
    promo: PromoCode,
    user: User,
) -> PromoActivation:
    valid, error = await validate_promo(
        session=session,
        promo=promo,
        user=user,
    )
    if not valid:
        raise ValueError(error)
    # -----------------------------------------------------
    # RECORD ACTIVATION
    # -----------------------------------------------------
    activation = PromoActivation(
        promo_id=promo.id,
        user_id=user.id,
        telegram_id=user.telegram_id,
        reward_type=promo.reward_type,
        reward_amount=promo.reward_amount,
        premium_days=promo.premium_days,
    )
    session.add(
        activation
    )
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
    elif promo.reward_type == "traps":
        # Поле для ловушек появится
        # в User на следующем этапе.
        #
        # Пока награда фиксируется
        # в PromoActivation.
        pass
    elif promo.reward_type == "premium":
        now = datetime.now(
            timezone.utc
        )
        current_until = (
            user.premium_until
        )
        if (
            user.premium_active
            and current_until is not None
            and current_until > now
        ):
            base_date = current_until
        else:
            base_date = now
        from datetime import timedelta
        user.premium_active = True
        user.premium_until = (
            base_date
            + timedelta(
                days=promo.premium_days
            )
        )
    promo.activations_count += 1
    await session.commit()
    await session.refresh(
        activation
    )
    return activation
# =========================================================
# 📊 PROMO STATISTICS
# =========================================================
async def promo_statistics(
    session: AsyncSession,
    promo_id: int,
) -> dict[str, int]:
    total_result = await session.execute(
        select(
            func.count(
                PromoActivation.id
            )
        ).where(
            PromoActivation.promo_id
            == promo_id
        )
    )
    total = int(
        total_result.scalar_one() or 0
    )
    unique_result = await session.execute(
        select(
            func.count(
                func.distinct(
                    PromoActivation.user_id
                )
            )
        ).where(
            PromoActivation.promo_id
            == promo_id
        )
    )
    unique_users = int(
        unique_result.scalar_one() or 0
    )
    return {
        "total": total,
        "unique_users": unique_users,
    }
