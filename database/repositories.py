from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import (
    PromoCode,
    PromoActivation,
    User,
)
# =========================================================
# HELPERS
# =========================================================
def utc_now() -> datetime:
    return datetime.now(timezone.utc)
def normalize_code(code: str) -> str:
    return code.strip().upper()
def parse_allowed_user_ids(
    value: Optional[str],
) -> Optional[set[int]]:
    """
    Преобразует строку:
    "123,456,789"
    в:
    {123, 456, 789}
    Если ограничений нет — возвращает None.
    """
    if not value:
        return None
    result: set[int] = set()
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            telegram_id = int(item)
        except ValueError:
            continue
        if telegram_id > 0:
            result.add(telegram_id)
    return result or None
# =========================================================
# GET PROMO
# =========================================================
async def get_promo_by_code(
    session: AsyncSession,
    code: str,
) -> Optional[PromoCode]:
    normalized = normalize_code(code)
    result = await session.execute(
        select(PromoCode).where(
            PromoCode.code == normalized
        )
    )
    return result.scalar_one_or_none()
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
    active_only: bool = False,
) -> list[PromoCode]:
    query = select(PromoCode).order_by(
        PromoCode.id.desc()
    )
    if active_only:
        query = query.where(
            PromoCode.is_active.is_(True)
        )
    result = await session.execute(query)
    return list(result.scalars().all())
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
    created_by: Optional[int] = None,
) -> PromoCode:
    code = normalize_code(code)
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
    else:
        if reward_amount <= 0:
            raise ValueError(
                "Количество награды должно быть больше 0."
            )
    if max_activations is not None:
        if max_activations <= 0:
            raise ValueError(
                "Общий лимит активаций должен быть больше 0."
            )
    if max_activations_per_user is not None:
        if max_activations_per_user <= 0:
            raise ValueError(
                "Лимит активаций на пользователя должен быть больше 0."
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
        starts_at=starts_at,
        expires_at=expires_at,
        only_new_users=only_new_users,
        only_premium=only_premium,
        allowed_user_ids=allowed_user_ids,
        created_by=created_by,
        is_active=True,
        activations_count=0,
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
# ACTIVATE CHECK
# =========================================================
async def check_promo(
    session: AsyncSession,
    promo: PromoCode,
    user: User,
) -> tuple[bool, str]:
    now = utc_now()
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
            "Промокод ещё не начал действовать.",
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
    # ONLY PREMIUM
    # -----------------------------------------------------
    if promo.only_premium:
        if not user.premium_active:
            return (
                False,
                "Этот промокод доступен только Premium пользователям.",
            )
        if (
            user.premium_until is not None
            and user.premium_until <= now
        ):
            return (
                False,
                "Ваш Premium уже истёк.",
            )
    # -----------------------------------------------------
    # ONLY NEW USERS
    # -----------------------------------------------------
    if promo.only_new_users:
        # Пользователь считается новым,
        # если он зарегистрирован недавно.
        #
        # Здесь проверяем наличие созданной записи.
        # Если позже понадобится точное правило
        # "новый = зарегистрирован не более N часов назад",
        # его можно добавить здесь.
        if user.created_at is None:
            return (
                False,
                "Промокод доступен только новым пользователям.",
            )
        # По умолчанию считаем новым пользователя,
        # который зарегистрирован не более 24 часов назад.
        created_at = user.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(
                tzinfo=timezone.utc
            )
        age_seconds = (
            now - created_at
        ).total_seconds()
        if age_seconds > 24 * 60 * 60:
            return (
                False,
                "Этот промокод доступен только новым пользователям.",
            )
    # -----------------------------------------------------
    # ALLOWED USERS
    # -----------------------------------------------------
    allowed_ids = parse_allowed_user_ids(
        promo.allowed_user_ids
    )
    if allowed_ids is not None:
        if user.telegram_id not in allowed_ids:
            return (
                False,
                "У вас нет доступа к этому промокоду.",
            )
    # -----------------------------------------------------
    # USER ACTIVATION LIMIT
    # -----------------------------------------------------
    if (
        promo.max_activations_per_user
        is not None
    ):
        count_result = await session.execute(
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
            count_result.scalar_one() or 0
        )
        if (
            user_activations
            >= promo.max_activations_per_user
        ):
            return (
                False,
                "Вы уже использовали этот промокод максимальное количество раз.",
            )
    return (
        True,
        "OK",
    )
# =========================================================
# GET USER ACTIVATIONS
# =========================================================
async def get_user_promo_activations(
    session: AsyncSession,
    promo_id: int,
    user_id: int,
) -> int:
    result = await session.execute(
        select(
            func.count(
                PromoActivation.id
            )
        ).where(
            PromoActivation.promo_id == promo_id,
            PromoActivation.user_id == user_id,
        )
    )
    return int(
        result.scalar_one() or 0
    )
# =========================================================
# ACTIVATE PROMO
# =========================================================
async def activate_promo(
    session: AsyncSession,
    promo: PromoCode,
    user: User,
) -> PromoActivation:
    # Сначала повторно проверяем условия
    # непосредственно перед записью.
    allowed, reason = await check_promo(
        session=session,
        promo=promo,
        user=user,
    )
    if not allowed:
        raise ValueError(reason)
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
    await session.commit()
    await session.refresh(activation)
    return activation
# =========================================================
# GET PROMO STATISTICS
# =========================================================
async def get_promo_statistics(
    session: AsyncSession,
    promo_id: int,
) -> dict:
    promo = await get_promo_by_id(
        session=session,
        promo_id=promo_id,
    )
    if promo is None:
        raise ValueError(
            "Промокод не найден."
        )
    total_result = await session.execute(
        select(
            func.count(
                PromoActivation.id
            )
        ).where(
            PromoActivation.promo_id == promo.id
        )
    )
    total_activations = int(
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
            PromoActivation.promo_id == promo.id
        )
    )
    unique_users = int(
        unique_result.scalar_one() or 0
    )
    if promo.max_activations:
        percentage = (
            total_activations
            / promo.max_activations
        ) * 100
        percentage = min(
            percentage,
            100.0,
        )
    else:
        percentage = 0.0
    return {
        "promo_id": promo.id,
        "code": promo.code,
        "reward_type": promo.reward_type,
        "reward_amount": promo.reward_amount,
        "premium_days": promo.premium_days,
        "total_activations": total_activations,
        "unique_users": unique_users,
        "max_activations": promo.max_activations,
        "max_activations_per_user": (
            promo.max_activations_per_user
        ),
        "percentage": percentage,
        "is_active": promo.is_active,
        "starts_at": promo.starts_at,
        "expires_at": promo.expires_at,
    }
# =========================================================
# GET ACTIVATIONS
# =========================================================
async def list_promo_activations(
    session: AsyncSession,
    promo_id: int,
    limit: int = 100,
) -> list[PromoActivation]:
    limit = max(
        1,
        min(limit, 1000),
    )
    result = await session.execute(
        select(PromoActivation)
        .where(
            PromoActivation.promo_id == promo_id
        )
        .order_by(
            PromoActivation.id.desc()
        )
        .limit(limit)
    )
    return list(
        result.scalars().all()
    )
# =========================================================
# CHECK IF USER EVER ACTIVATED PROMO
# =========================================================
async def user_has_activated_promo(
    session: AsyncSession,
    promo_id: int,
    user_id: int,
) -> bool:
    result = await session.execute(
        select(PromoActivation.id)
        .where(
            PromoActivation.promo_id == promo_id,
            PromoActivation.user_id == user_id,
        )
        .limit(1)
    )
    return (
        result.scalar_one_or_none()
        is not None
    )
# =========================================================
# COUNT ALL PROMO ACTIVATIONS
# =========================================================
async def count_promo_activations(
    session: AsyncSession,
    promo_id: int,
) -> int:
    result = await session.execute(
        select(
            func.count(
                PromoActivation.id
            )
        ).where(
            PromoActivation.promo_id == promo_id
        )
    )
    return int(
        result.scalar_one() or 0
    )
# =========================================================
# COUNT UNIQUE USERS
# =========================================================
async def count_unique_promo_users(
    session: AsyncSession,
    promo_id: int,
) -> int:
    result = await session.execute(
        select(
            func.count(
                func.distinct(
                    PromoActivation.user_id
                )
            )
        ).where(
            PromoActivation.promo_id == promo_id
        )
    )
    return int(
        result.scalar_one() or 0
    )
