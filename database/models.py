from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


# =========================================================
# TIME
# =========================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# =========================================================
# USER
# =========================================================

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        index=True,
        nullable=False,
    )

    username: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    first_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    last_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    language: Mapped[str] = mapped_column(
        String(16),
        default="ru",
        nullable=False,
    )

    avatar_file_id: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
    )

    role: Mapped[str] = mapped_column(
        String(32),
        default="user",
        nullable=False,
        index=True,
    )

    # =====================================================
    # PREMIUM
    # =====================================================

    premium_active: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    premium_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # =====================================================
    # BALANCES
    # =====================================================

    balance_rub: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    stars_balance: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # =====================================================
    # BONUS SEARCHES
    # =====================================================

    bonus_searches: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # =====================================================
    # BONUS TRAPS
    # =====================================================

    bonus_traps: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # =====================================================
    # DISCOUNT
    # =====================================================

    discount_percent: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # =====================================================
    # REFERRAL
    # =====================================================

    referral_code: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
    )

    referred_by: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        index=True,
    )

    # =====================================================
    # SEARCH LIMIT
    # =====================================================

    successful_searches_today: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    search_counter_date: Mapped[Optional[str]] = mapped_column(
        String(16),
        nullable=True,
    )

    # =====================================================
    # NOTIFICATIONS
    # =====================================================

    notifications_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # =====================================================
    # BLOCK
    # =====================================================

    is_blocked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # =====================================================
    # DATES
    # =====================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


# =========================================================
# PROMO CODE
# =========================================================

class PromoCode(Base):
    __tablename__ = "promo_codes"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    code: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        index=True,
        nullable=False,
    )

    reward_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    reward_amount: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    premium_days: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    max_activations: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    max_activations_per_user: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    activations_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    starts_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    only_new_users: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    only_premium: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    allowed_user_ids: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    created_by: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


# =========================================================
# PROMO ACTIVATION
# =========================================================

class PromoActivation(Base):
    __tablename__ = "promo_activations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    promo_id: Mapped[int] = mapped_column(
        ForeignKey(
            "promo_codes.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
    )

    reward_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    reward_amount: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    premium_days: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    activated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )


# =========================================================
# TASK
# =========================================================

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # =====================================================
    # BASIC
    # =====================================================

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # =====================================================
    # TASK TYPE
    # =====================================================

    task_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    # Например:
    #
    # subscribe_channel
    # referral
    # search
    # promo
    # premium
    # open_miniapp
    # custom

    # Значение, которое нужно выполнить.
    #
    # Например:
    #
    # @teyzus
    # 5
    # https://t.me/...
    #
    target_value: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # =====================================================
    # REWARD
    # =====================================================

    reward_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    # Количество:
    #
    # Stars
    # рублей
    # поисков
    # ловушек
    # процентов скидки

    reward_amount: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Для Premium.

    premium_days: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # =====================================================
    # LIMITS
    # =====================================================

    max_completions: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    completions_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    max_completions_per_user: Mapped[Optional[int]] = mapped_column(
        Integer,
        default=1,
        nullable=True,
    )

    repeatable: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # =====================================================
    # USER FILTERS
    # =====================================================

    only_new_users: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    only_premium: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # =====================================================
    # DATES
    # =====================================================

    starts_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # =====================================================
    # STATUS
    # =====================================================

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    # =====================================================
    # SORT
    # =====================================================

    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # =====================================================
    # IMAGE
    # =====================================================

    image_file_id: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
    )

    # =====================================================
    # OWNER
    # =====================================================

    created_by: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    # =====================================================
    # DATES
    # =====================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


# =========================================================
# TASK COMPLETION
# =========================================================

class TaskCompletion(Base):
    __tablename__ = "task_completions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # =====================================================
    # TASK
    # =====================================================

    task_id: Mapped[int] = mapped_column(
        ForeignKey(
            "tasks.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # =====================================================
    # USER
    # =====================================================

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
    )

    # =====================================================
    # REWARD SNAPSHOT
    # =====================================================

    reward_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    reward_amount: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    premium_days: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # =====================================================
    # DATE
    # =====================================================

    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
    )
