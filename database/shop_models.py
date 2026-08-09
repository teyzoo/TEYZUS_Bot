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
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


# =========================================================
# TIME
# =========================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


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
        String(100),
        unique=True,
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    emoji: Mapped[str] = mapped_column(
        String(16),
        default="🏷️",
        nullable=False,
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
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
    # USERNAME
    # =====================================================

    username: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    normalized_username: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
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

    seller_username: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
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

    ai_card_url: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
    )

    ai_card_file_id: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
    )

    # =====================================================
    # CATEGORY
    # =====================================================

    category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey(
            "shop_categories.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
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
    # cancelled
    # hidden

    # =====================================================
    # MODERATION
    # =====================================================

    moderation_comment: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    moderated_by: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
    )

    moderated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # =====================================================
    # FLAGS
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
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
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

    __table_args__ = (
        Index(
            "ix_shop_listing_status_created",
            "status",
            "created_at",
        ),
        Index(
            "ix_shop_listing_active_price",
            "is_active",
            "price_rub",
        ),
    )


# =========================================================
# FAVORITE
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
# CART ITEM
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

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "listing_id",
            name="uq_shop_cart_user_listing",
        ),
    )


# =========================================================
# PURCHASE
# =========================================================

class ShopPurchase(Base):
    __tablename__ = "shop_purchases"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    listing_id: Mapped[int] = mapped_column(
        ForeignKey(
            "shop_listings.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    buyer_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    seller_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    # =====================================================
    # SNAPSHOT
    # =====================================================

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

    # =====================================================
    # PAYMENT
    # =====================================================

    payment_method: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    payment_status: Mapped[str] = mapped_column(
        String(32),
        default="pending",
        nullable=False,
        index=True,
    )

    # pending
    # paid
    # refunded
    # failed

    # =====================================================
    # PURCHASE STATUS
    # =====================================================

    status: Mapped[str] = mapped_column(
        String(32),
        default="created",
        nullable=False,
        index=True,
    )

    # created
    # waiting_payment
    # paid
    # completed
    # cancelled
    # refunded

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
# DEAL
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
        unique=True,
        nullable=False,
        index=True,
    )

    buyer_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    seller_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
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
    # payment_pending
    # escrow
    # transferring
    # completed
    # cancelled
    # disputed
    # refunded

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

    is_online: Mapped[bool] = mapped_column(
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

    is_visible: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "purchase_id",
            "buyer_id",
            name="uq_shop_review_purchase_buyer",
        ),
    )
