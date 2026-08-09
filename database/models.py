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

    period: Mapped[str] = mapped_column(
    String(32),
    default="daily",
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

    price_stars: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    image_file_id: Mapped[Optional[str]] = mapped_column(
        String(512),
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
        String(16),
        default="🎁",
        nullable=False,
    )

    # stars
    # balance
    # premium
    # searches
    # traps
    # discount

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

    chance: Mapped[float] = mapped_column(
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
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

    # =====================================================
    # REWARD SNAPSHOT
    # =====================================================

    reward_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    reward_title: Mapped[str] = mapped_column(
        String(255),
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

    reward_chance: Mapped[float] = mapped_column(
        nullable=False,
    )

    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
    )

# =========================================================
# TEYZUS SHOP
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

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
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

    total_sales: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    total_reviews: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    rating: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    is_online: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
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

    # =====================================================
    # SELLER
    # =====================================================

    seller_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    seller_telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
    )

    # =====================================================
    # USERNAME
    # =====================================================

    username: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    # =====================================================
    # DESCRIPTION
    # =====================================================

    title: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
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
    # CATEGORY
    # =====================================================

    category: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )

    # =====================================================
    # PRICE
    # =====================================================

    price_rub: Mapped[int] = mapped_column(
        Integer,
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

    # =====================================================
    # SHOP FLAGS
    # =====================================================

    is_premium: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # =====================================================
    # STATISTICS
    # =====================================================

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

    purchases_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # =====================================================
    # DATES
    # =====================================================

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

    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    sold_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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


# =========================================================
# SHOP CART
# =========================================================

class ShopCartItem(Base):
    __tablename__ = "shop_cart_items"

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

    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )


# =========================================================
# SHOP PURCHASE
# =========================================================

class ShopPurchase(Base):
    __tablename__ = "shop_purchases"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # =====================================================
    # BUYER
    # =====================================================

    buyer_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    buyer_telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
    )

    # =====================================================
    # SELLER
    # =====================================================

    seller_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    seller_telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
    )

    # =====================================================
    # LISTING
    # =====================================================

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

    # =====================================================
    # PRICE SNAPSHOT
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

    currency: Mapped[str] = mapped_column(
        String(16),
        default="RUB",
        nullable=False,
    )

    # =====================================================
    # PAYMENT
    # =====================================================

    payment_method: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
    )

    payment_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
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
    # paid
    # escrow
    # completed
    # cancelled
    # refunded

    # =====================================================
    # DATES
    # =====================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


# =========================================================
# SHOP DEAL / ESCROW
# =========================================================

class ShopDeal(Base):
    __tablename__ = "shop_deals"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    purchase_id: Mapped[int] = mapped_column(
        ForeignKey(
            "shop_purchases.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
        index=True,
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
    # funded
    # username_transferred
    # buyer_confirmed
    # completed
    # cancelled
    # disputed
    # refunded

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

    funded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    cancelled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


# =========================================================
# SHOP REVIEW
# =========================================================

class ShopReview(Base):
    __tablename__ = "shop_reviews"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    purchase_id: Mapped[int] = mapped_column(
        ForeignKey(
            "shop_purchases.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
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
