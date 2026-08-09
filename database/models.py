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
    UniqueConstraint,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
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
    # BALANCE
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
    # REFERRALS
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
    # EXTRA BONUSES
    # =====================================================
    bonus_searches: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    bonus_traps: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    # =====================================================
    # SETTINGS
    # =====================================================
    notifications_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
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
    # =====================================================
    # RELATIONSHIPS
    # =====================================================
    promo_activations: Mapped[list["PromoActivation"]] = (
        relationship(
            "PromoActivation",
            back_populates="user",
            cascade="all, delete-orphan",
        )
    )
# =========================================================
# PROMO REWARD TYPE
# =========================================================
class PromoRewardType:
    PREMIUM = "premium"
    STARS = "stars"
    BALANCE_RUB = "balance_rub"
    SEARCHES = "searches"
    TRAPS = "traps"
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
    # =====================================================
    # CODE
    # =====================================================
    code: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        index=True,
        nullable=False,
    )
    # =====================================================
    # REWARD
    # =====================================================
    reward_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    reward_amount: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    # =====================================================
    # PREMIUM
    # =====================================================
    # Используется только если reward_type == premium.
    # Количество дней Premium.
    premium_days: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    # =====================================================
    # LIMITS
    # =====================================================
    # Общий лимит активаций.
    # NULL = без ограничения.
    max_activations: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    # Сколько раз один пользователь может активировать.
    # NULL = без ограничения.
    max_activations_per_user: Mapped[Optional[int]] = (
        mapped_column(
            Integer,
            nullable=True,
        )
    )
    activations_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    # =====================================================
    # DATE LIMITS
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
    # USER RESTRICTIONS
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
    # STATUS
    # =====================================================
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    # =====================================================
    # TARGET TELEGRAM IDS
    # =====================================================
    # Если NULL — доступен всем.
    # Если заполнен — только указанным Telegram ID.
    allowed_user_ids: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    # =====================================================
    # METADATA
    # =====================================================
    created_by: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
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
    # =====================================================
    # RELATIONSHIP
    # =====================================================
    activations: Mapped[list["PromoActivation"]] = relationship(
        "PromoActivation",
        back_populates="promo",
        cascade="all, delete-orphan",
    )
# =========================================================
# PROMO ACTIVATION
# =========================================================
class PromoActivation(Base):
    __tablename__ = "promo_activations"
    __table_args__ = (
        UniqueConstraint(
            "promo_id",
            "user_id",
            "activation_number",
            name="uq_promo_user_activation",
        ),
    )
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    # =====================================================
    # PROMO
    # =====================================================
    promo_id: Mapped[int] = mapped_column(
        ForeignKey(
            "promo_codes.id",
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
    # =====================================================
    # ACTIVATION NUMBER
    # =====================================================
    # 1 = первая активация этим пользователем
    # 2 = вторая
    # 3 = третья
    # и т.д.
    activation_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    # =====================================================
    # REWARD SNAPSHOT
    # =====================================================
    reward_type: Mapped[str] = mapped_column(
        String(32),
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    # =====================================================
    # RELATIONSHIPS
    # =====================================================
    promo: Mapped["PromoCode"] = relationship(
        "PromoCode",
        back_populates="activations",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="promo_activations",
    )
