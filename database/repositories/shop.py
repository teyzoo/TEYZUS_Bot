from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    delete,
    func,
    or_,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from database.shop_models import (
    ShopCategory,
    ShopFavorite,
    ShopListing,
    ShopCartItem,
    ShopPurchase,
    ShopReview,
)


# =========================================================
# TIME
# =========================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# =========================================================
# CATEGORIES
# =========================================================

async def get_categories(
    session: AsyncSession,
) -> list[ShopCategory]:

    result = await session.execute(
        select(ShopCategory)
        .where(
            ShopCategory.is_active.is_(True)
        )
        .order_by(
            ShopCategory.sort_order.asc(),
            ShopCategory.id.asc(),
        )
    )

    return list(result.scalars().all())


async def get_category_by_slug(
    session: AsyncSession,
    slug: str,
) -> Optional[ShopCategory]:

    result = await session.execute(
        select(ShopCategory)
        .where(
            ShopCategory.slug == slug,
            ShopCategory.is_active.is_(True),
        )
    )

    return result.scalar_one_or_none()


# =========================================================
# LISTINGS
# =========================================================

async def get_shop_listings(
    session: AsyncSession,
    user_id: int,
    search: str = "",
    category: str = "all",
    sort: str = "new",
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[ShopListing], int]:

    page = max(page, 1)
    per_page = max(
        1,
        min(per_page, 100),
    )

    query = (
        select(ShopListing)
        .where(
            ShopListing.status == "approved",
            ShopListing.is_active.is_(True),
        )
    )

    count_query = (
        select(
            func.count(
                ShopListing.id
            )
        )
        .where(
            ShopListing.status == "approved",
            ShopListing.is_active.is_(True),
        )
    )

    # -----------------------------------------------------
    # SEARCH
    # -----------------------------------------------------

    if search:
        search_value = (
            search.strip()
            .lstrip("@")
        )

        pattern = (
            f"%{search_value}%"
        )

        condition = or_(
            ShopListing.username.ilike(
                pattern
            ),
            ShopListing.title.ilike(
                pattern
            ),
            ShopListing.description.ilike(
                pattern
            ),
        )

        query = query.where(
            condition
        )

        count_query = count_query.where(
            condition
        )

    # -----------------------------------------------------
    # CATEGORY
    # -----------------------------------------------------

    if category == "premium":

        query = query.where(
            ShopListing.is_premium.is_(True)
        )

        count_query = count_query.where(
            ShopListing.is_premium.is_(True)
        )

    # -----------------------------------------------------
    # SORT
    # -----------------------------------------------------

    if category == "popular" or sort == "popular":

        query = query.order_by(
            ShopListing.views_count.desc(),
            ShopListing.favorites_count.desc(),
            ShopListing.created_at.desc(),
        )

    elif category == "cheap" or sort == "price_asc":

        query = query.order_by(
            ShopListing.price_rub.asc(),
            ShopListing.created_at.desc(),
        )

    elif sort == "price_desc":

        query = query.order_by(
            ShopListing.price_rub.desc(),
            ShopListing.created_at.desc(),
        )

    else:

        query = query.order_by(
            ShopListing.created_at.desc()
        )

    # -----------------------------------------------------
    # PAGINATION
    # -----------------------------------------------------

    offset = (
        (page - 1)
        * per_page
    )

    query = query.offset(
        offset
    ).limit(
        per_page
    )

    result = await session.execute(
        query
    )

    listings = list(
        result.scalars().all()
    )

    total_result = await session.execute(
        count_query
    )

    total = int(
        total_result.scalar() or 0
    )

    return listings, total


# =========================================================
# LISTING BY ID
# =========================================================

async def get_listing(
    session: AsyncSession,
    listing_id: int,
) -> Optional[ShopListing]:

    result = await session.execute(
        select(ShopListing)
        .where(
            ShopListing.id == listing_id
        )
    )

    return result.scalar_one_or_none()


# =========================================================
# LISTING BY USERNAME
# =========================================================

async def get_listing_by_username(
    session: AsyncSession,
    username: str,
) -> Optional[ShopListing]:

    username = (
        username
        .strip()
        .lstrip("@")
        .lower()
    )

    result = await session.execute(
        select(ShopListing)
        .where(
            func.lower(
                ShopListing.username
            ) == username,
            ShopListing.status.in_(
                [
                    "pending",
                    "approved",
                    "reserved",
                ]
            ),
        )
        .limit(1)
    )

    return result.scalar_one_or_none()


# =========================================================
# FAVORITE
# =========================================================

async def is_favorite(
    session: AsyncSession,
    user_id: int,
    listing_id: int,
) -> bool:

    result = await session.execute(
        select(ShopFavorite.id)
        .where(
            ShopFavorite.user_id == user_id,
            ShopFavorite.listing_id == listing_id,
        )
        .limit(1)
    )

    return result.scalar_one_or_none() is not None


async def add_favorite(
    session: AsyncSession,
    user_id: int,
    listing_id: int,
) -> bool:

    exists = await is_favorite(
        session,
        user_id,
        listing_id,
    )

    if exists:
        return False

    favorite = ShopFavorite(
        user_id=user_id,
        listing_id=listing_id,
    )

    session.add(favorite)

    await session.execute(
        __import__(
            "sqlalchemy"
        ).update(ShopListing)
        .where(
            ShopListing.id == listing_id
        )
        .values(
            favorites_count=(
                ShopListing.favorites_count + 1
            )
        )
    )

    await session.commit()

    return True


async def remove_favorite(
    session: AsyncSession,
    user_id: int,
    listing_id: int,
) -> bool:

    exists = await is_favorite(
        session,
        user_id,
        listing_id,
    )

    if not exists:
        return False

    await session.execute(
        delete(ShopFavorite)
        .where(
            ShopFavorite.user_id == user_id,
            ShopFavorite.listing_id == listing_id,
        )
    )

    await session.execute(
        __import__(
            "sqlalchemy"
        ).update(ShopListing)
        .where(
            ShopListing.id == listing_id,
            ShopListing.favorites_count > 0,
        )
        .values(
            favorites_count=(
                ShopListing.favorites_count - 1
            )
        )
    )

    await session.commit()

    return True


# =========================================================
# CART
# =========================================================

async def get_cart(
    session: AsyncSession,
    user_id: int,
) -> list[ShopListing]:

    result = await session.execute(
        select(ShopListing)
        .join(
            ShopCartItem,
            ShopCartItem.listing_id
            == ShopListing.id,
        )
        .where(
            ShopCartItem.user_id == user_id,
            ShopListing.status == "approved",
            ShopListing.is_active.is_(True),
        )
        .order_by(
            ShopCartItem.created_at.desc()
        )
    )

    return list(
        result.scalars().all()
    )


async def add_to_cart(
    session: AsyncSession,
    user_id: int,
    listing_id: int,
) -> bool:

    listing = await get_listing(
        session,
        listing_id,
    )

    if (
        listing is None
        or listing.status != "approved"
        or not listing.is_active
    ):
        return False

    if listing.seller_id == user_id:
        return False

    existing = await session.execute(
        select(ShopCartItem.id)
        .where(
            ShopCartItem.user_id == user_id,
            ShopCartItem.listing_id == listing_id,
        )
        .limit(1)
    )

    if existing.scalar_one_or_none():
        return False

    session.add(
        ShopCartItem(
            user_id=user_id,
            listing_id=listing_id,
        )
    )

    await session.commit()

    return True


async def remove_from_cart(
    session: AsyncSession,
    user_id: int,
    listing_id: int,
) -> bool:

    result = await session.execute(
        delete(ShopCartItem)
        .where(
            ShopCartItem.user_id == user_id,
            ShopCartItem.listing_id == listing_id,
        )
    )

    await session.commit()

    return result.rowcount > 0


# =========================================================
# USER
# =========================================================

async def get_user_by_id(
    session: AsyncSession,
    user_id: int,
) -> Optional[User]:

    result = await session.execute(
        select(User)
        .where(
            User.id == user_id
        )
    )

    return result.scalar_one_or_none()
