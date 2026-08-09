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
    Index,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
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
    # BONUS
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
    # SEARCH
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

    __table_args__ = (
        Index(
            "ix_promo_activation_user_promo",
            "user_id",
            "promo_id",
        ),
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

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # =====================================================
    # TYPE
    # =====================================================

    task_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    target_value: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # =====================================================
    # PERIOD
    #
    # daily
    # weekly
    # monthly
    # permanent
    # custom
    # =====================================================

    period_type: Mapped[str] = mapped_column(
        String(32),
        default="permanent",
        nullable=False,
        index=True,
    )

    # =====================================================
    # REWARD
    # =====================================================

    reward_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
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
    # USER FILTER
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

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    image_file_id: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
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
# TASK COMPLETION
# =========================================================

class TaskCompletion(Base):
    __tablename__ = "task_completions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    task_id: Mapped[int] = mapped_column(
        ForeignKey(
            "tasks.id",
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

    period_key: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        index=True,
    )

    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "task_id",
            "user_id",
            "period_key",
            name="uq_task_user_period",
        ),
    )


# =========================================================
# CASE
# =========================================================

class Case(Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    image_file_id: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
    )

    # =====================================================
    # PRICE
    # =====================================================

    price_stars: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    price_rub: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # =====================================================
    # STATUS
    # =====================================================

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
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
# CASE REWARD
# =========================================================

class CaseReward(Base):
    __tablename__ = "case_rewards"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    case_id: Mapped[int] = mapped_column(
        ForeignKey(
            "cases.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    emoji: Mapped[str] = mapped_column(
        String(32),
        default="🎁",
        nullable=False,
    )

    reward_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
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

    chance: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )


# =========================================================
# CASE OPEN
# =========================================================

class CaseOpen(Base):
    __tablename__ = "case_opens"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    case_id: Mapped[int] = mapped_column(
        ForeignKey(
            "cases.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    reward_id: Mapped[int] = mapped_column(
        ForeignKey(
            "case_rewards.id",
            ondelete="SET NULL",
        ),
        nullable=True,
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

    price_stars: Mapped[int] = mapped_column(
        Integer,
        default=0,
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

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )


# =========================================================
# SHOP CATEGORY
# =========================================================

class ShopCategory(Base):
    __tablename__ = "shop_categories"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
        index=True,
    )

    emoji: Mapped[str] = mapped_column(
        String(32),
        default="🏪",
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )


# =========================================================
# SELLER PROFILE
# =========================================================

class SellerProfile(Base):
    __tablename__ = "seller_profiles"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        unique=True,
        nullable=False,
        index=True,
    )

    display_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    avatar_file_id: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
    )

    rating: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    reviews_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    sales_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    online: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
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
# SHOP LISTING
# =========================================================

class ShopListing(Base):
    __tablename__ = "shop_listings"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    seller_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey(
            "shop_categories.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    # =====================================================
    # USERNAME
    # =====================================================

    username: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    title: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # =====================================================
    # AI CARD
    # =====================================================

    ai_card_file_id: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
    )

    ai_card_url: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
    )

    # =====================================================
    # PRICE
    # =====================================================

    price_rub: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    price_stars: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    # =====================================================
    # STATUS
    # =====================================================

    status: Mapped[str] = mapped_column(
        String(32),
        default="pending",
        nullable=False,
        index=True,
    )

    # pending
    # approved
    # rejected
    # sold
    # reserved
    # deleted

    rejection_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    is_premium: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    views_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    favorites_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


# =========================================================
# SHOP FAVORITE
# =========================================================

class ShopFavorite(Base):
    __tablename__ = "shop_favorites"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    listing_id: Mapped[int] = mapped_column(
        ForeignKey(
            "shop_listings.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "listing_id",
            name="uq_shop_favorite_user_listing",
        ),
    )


# =========================================================
# CART
# =========================================================

class CartItem(Base):
    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    listing_id: Mapped[int] = mapped_column(
        ForeignKey(
            "shop_listings.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "listing_id",
            name="uq_cart_user_listing",
        ),
    )


# =========================================================
# PURCHASE
# =========================================================

class Purchase(Base):
    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    buyer_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    seller_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    listing_id: Mapped[int] = mapped_column(
        ForeignKey(
            "shop_listings.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    username: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    price_rub: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    price_stars: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    payment_method: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        default="pending",
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


# =========================================================
# DEAL / ESCROW
# =========================================================

class Deal(Base):
    __tablename__ = "deals"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    buyer_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    seller_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    listing_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey(
            "shop_listings.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    purchase_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey(
            "purchases.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    amount_rub: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    commission_rub: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    seller_amount_rub: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        default="created",
        nullable=False,
        index=True,
    )

    # created
    # paid
    # escrow
    # completed
    # cancelled
    # dispute

    buyer_confirmed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    seller_confirmed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
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
# REVIEW
# =========================================================

class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    deal_id: Mapped[int] = mapped_column(
        ForeignKey(
            "deals.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    reviewer_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    seller_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )


# =========================================================
# SHOP SETTINGS
# =========================================================

class ShopSetting(Base):
    __tablename__ = "shop_settings"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    key: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
        index=True,
    )

    value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
