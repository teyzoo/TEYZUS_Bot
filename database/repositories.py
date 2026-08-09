import secrets
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import func, select
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
# USER
# =========================================================
def generate_referral_code() -> str:
    return secrets.token_urlsafe(8)
async def get_user(
    session: AsyncSession,
    telegram_id: int,
) -> Optional[User]:
    result = await session.execute(
        select(User).where(
            User.telegram_id == telegram_id
        )
    )
    return result.scalar_one_or_none()
async def create_user(
    session: AsyncSession,
    telegram_id: int,
    username: Optional[str],
    first_name: Optional[str],
    last_name: Optional[str],
    language: str,
    referred_by: Optional[int] = None,
) -> User:
    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        language=language or "ru",
        referred_by=referred_by,
        referral_code=generate_referral_code(),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: Optional[str],
    first_name: Optional[str],
    last_name: Optional[str],
    language: str,
    referred_by: Optional[int] = None,
) -> tuple[User, bool]:
    user = await get_user(
        session=session,
        telegram_id=telegram_id,
    )
    if user:
        changed = False
        if user.username != username:
            user.username = username
            changed = True
        if user.first_name != first_name:
            user.first_name = first_name
            changed = True
        if user.last_name != last_name:
            user.last_name = last_name
            changed = True
        if user.language != language:
            user.language = language or "ru"
            changed = True
        if changed:
            await session.commit()
            await session.refresh(user)
        return user, False
    user = await create_user(
        session=session,
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        language=language,
        referred_by=referred_by,
    )
    return user, True
# =========================================================
# PROMO CODE
# =========================================================
def normalize_promo_code(
    code: str,
) -> str:
    return code.strip().upper()
async def get_promo_by_code(
    session: AsyncSession,
    code: str,
) -> Optional[PromoCode]:
    normalized_code = normalize_promo_code(code)
    result = await session.execute(
        select(PromoCode).where(
            PromoCode.code == normalized_code
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
async def create_promo(
    session: AsyncSession,
    *,
    code: str,
    reward_type: str,
    reward_amount: int = 0,
    premium_days: int = 0,
    max_activations: Optional[int] = None,
    max_activations_per_user: Optional[int] = 1,
    starts_at: Optional[datetime] = None,
    expires_at: Optional[datetime] = None,
    only_new_users: bool = False,
    only_premium: bool = False,
    allowed_user_ids: Optional[str] = None,
    created_by: Optional[int] = None,
) -> PromoCode:
    normalized_code = normalize_promo_code(code)
    existing = await get_promo_by_code(
        session=session,
        code=normalized_code,
    )
    if existing is not None:
        raise ValueError(
            "Промокод с таким кодом уже существует."
        )
    if reward_amount < 0:
        raise ValueError(
            "Размер награды не может быть отрицательным."
        )
    if premium_days < 0:
        raise ValueError(
            "Количество Premium дней не может быть отрицательным."
        )
    if max_activations is not None:
        if max_activations < 1:
            raise ValueError(
                "Общий лимит активаций должен быть больше 0."
            )
    if max_activations_per_user is not None:
        if max_activations_per_user < 1:
            raise ValueError(
                "Лимит активаций пользователя должен быть больше 0."
            )
    if starts_at and expires_at:
        if expires_at <= starts_at:
            raise ValueError(
                "Дата окончания должна быть позже даты начала."
            )
    promo = PromoCode(
        code=normalized_code,
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
    )
    session.add(promo)
    await session.commit()
    await session.refresh(promo)
    return promo
async def list_promos(
    session: AsyncSession,
    *,
    active_only: bool = False,
) -> list[PromoCode]:
    query = select(PromoCode).order_by(
        PromoCode.created_at.desc()
    )
    if active_only:
        query = query.where(
            PromoCode.is_active.is_(True)
        )
    result = await session.execute(query)
    return list(
        result.scalars().all()
    )
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
            "Этот промокод отключён."
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
    # EXPIRATION
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
                "Лимит активаций промокода исчерпан."
            )
    # =====================================================
    # NEW USERS
    # =====================================================
    if promo.only_new_users:
        # Пользователь считается новым,
        # если его регистрация была недавно
        # и он ещё не активировал этот промокод.
        existing_activation = await get_user_promo_activation_count(
            session=session,
            promo_id=promo.id,
            user_id=user.id,
        )
        if existing_activation > 0:
            raise ValueError(
                "Этот промокод доступен только новым пользователям."
            )
    # =====================================================
    # PREMIUM ONLY
    # =====================================================
    if promo.only_premium:
        if not user.premium_active:
            raise ValueError(
                "Этот промокод доступен только Premium пользователям."
            )
        if user.premium_until is not None:
            premium_until = user.premium_until
            if premium_until.tzinfo is None:
                premium_until = premium_until.replace(
                    tzinfo=timezone.utc
                )
            if premium_until <= now:
                raise ValueError(
                    "Этот промокод доступен только активным Premium пользователям."
                )
    # =====================================================
    # ALLOWED USER IDS
    # =====================================================
    if promo.allowed_user_ids:
        allowed_ids = parse_allowed_user_ids(
            promo.allowed_user_ids
        )
        if user.telegram_id not in allowed_ids:
            raise ValueError(
                "У тебя нет доступа к этому промокоду."
            )
    # =====================================================
    # USER LIMIT
    # =====================================================
    user_activations = (
        await get_user_promo_activation_count(
            session=session,
            promo_id=promo.id,
            user_id=user.id,
        )
    )
    if promo.max_activations_per_user is not None:
        if (
            user_activations
            >= promo.max_activations_per_user
        ):
            raise ValueError(
                "Ты уже использовал этот промокод максимальное количество раз."
            )
    # =====================================================
    # ACTIVATION NUMBER
    # =====================================================
    activation_number = user_activations + 1
    # =====================================================
    # CREATE ACTIVATION
    # =====================================================
    activation = PromoActivation(
        promo_id=promo.id,
        user_id=user.id,
        activation_number=activation_number,
        reward_type=promo.reward_type,
        reward_amount=promo.reward_amount,
        premium_days=promo.premium_days,
    )
    session.add(activation)
    # =====================================================
    # UPDATE PROMO COUNTER
    # =====================================================
    promo.activations_count += 1
    # =====================================================
    # APPLY REWARD
    # =====================================================
    apply_promo_reward(
        user=user,
        promo=promo,
        now=now,
    )
    await session.commit()
    await session.refresh(activation)
    return activation
async def get_user_promo_activation_count(
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
    return int(
        result.scalar_one() or 0
    )
async def get_user_promo_activations(
    session: AsyncSession,
    user_id: int,
) -> list[PromoActivation]:
    result = await session.execute(
        select(PromoActivation)
        .where(
            PromoActivation.user_id == user_id
        )
        .order_by(
            PromoActivation.created_at.desc()
        )
    )
    return list(
        result.scalars().all()
    )
# =========================================================
# ALLOWED USER IDS
# =========================================================
def parse_allowed_user_ids(
    value: str,
) -> set[int]:
    result: set[int] = set()
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            result.add(
                int(item)
            )
        except ValueError:
            continue
    return result
# =========================================================
# APPLY PROMO REWARD
# =========================================================
def apply_promo_reward(
    user: User,
    promo: PromoCode,
    now: Optional[datetime] = None,
) -> None:
    if now is None:
        now = utc_now()
    # =====================================================
    # PREMIUM
    # =====================================================
    if promo.reward_type == "premium":
        days = promo.premium_days
        if days <= 0:
            return
        if (
            user.premium_until is not None
            and user.premium_until > now
        ):
            user.premium_until = (
                user.premium_until
                + __import__(
                    "datetime"
                ).timedelta(
                    days=days
                )
            )
        else:
            user.premium_until = (
                now
                + __import__(
                    "datetime"
                ).timedelta(
                    days=days
                )
            )
        user.premium_active = True
        return
    # =====================================================
    # STARS
    # =====================================================
    if promo.reward_type == "stars":
        user.stars_balance += max(
            0,
            promo.reward_amount,
        )
        return
    # =====================================================
    # RUB BALANCE
    # =====================================================
    if promo.reward_type == "balance_rub":
        user.balance_rub += max(
            0,
            promo.reward_amount,
        )
        return
    # =====================================================
    # SEARCHES
    # =====================================================
    if promo.reward_type == "searches":
        user.bonus_searches += max(
            0,
            promo.reward_amount,
        )
        return
    # =====================================================
    # TRAPS
    # =====================================================
    if promo.reward_type == "traps":
        user.bonus_traps += max(
            0,
            promo.reward_amount,
        )
        return
