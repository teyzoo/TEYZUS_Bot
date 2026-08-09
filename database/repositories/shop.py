from __future__ import annotations

from typing import Optional

from sqlalchemy import (
    and_,
    delete,
    func,
    or_,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from database.shop_models import (
    ShopFavorite,
    ShopListing,
    ShopCartItem,
    ShopCategory,
)


# =========================================================
# LISTINGS
# =========================================================

async def get_listing_by_id(
    session: AsyncSession,
    listing_id: int,
) -> Optional[ShopListing]:

    result = await session.execute(
        select(ShopListing).where(
            ShopListing.id == listing_id
        )
    )

    return result.scalar_one_or_none()


async def get_listing_by_username(
    session: AsyncSession,
    username: str,
) -> Optional[ShopListing]:

    normalized = username.lower().lstrip("@").strip()

    result = await session.execute(
        select(ShopListing).where(
            ShopListing.normalized_username
            == normalized
        )
    )

    return result.scalar_one_or_none()


async def create_listing(
    session: AsyncSession,
    *,
    seller: User,
    username: str,
    title: Optional[str],
    description: Optional[str],
    category_id: Optional[int],
    price_rub: int,
    price_stars: Optional[int],
) -> ShopListing:

    clean_username = (
        username
        .strip()
        .lstrip("@")
    )

    listing = ShopListing(
        username=clean_username,
        normalized_username=clean_username.lower(),
        seller_id=seller.id,
        seller_telegram_id=seller.telegram_id,
        seller_username=seller.username,
        title=title,
        description=description,
        category_id=category_id,
        price_rub=price_rub,
        price_stars=price_stars,
        status="pending",
        is_active=True,
    )

    session.add(listing)

    await session.flush()

    return listing


async def get_public_listings(
    session: AsyncSession,
    *,
    user_id: Optional[int],
    search: str = "",
    category: str = "all",
    sort: str = "new",
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[ShopListing], int]:

    conditions = [
        ShopListing.is_active.is_(True),
        ShopListing.status == "approved",
    ]

    search = search.strip()

    if search:
        search_value = (
            search
            .lstrip("@")
            .lower()
        )

        conditions.append(
            ShopListing.normalized_username.ilike(
                f"%{search_value}%"
            )
        )

    if category == "premium":
        conditions.append(
            ShopListing.is_premium.is_(True)
        )

    # =====================================================
    # TOTAL
    # =====================================================

    count_query = select(
        func.count(ShopListing.id)
    ).where(
        and_(*conditions)
    )

    total_result = await session.execute(
        count_query
    )

    total = total_result.scalar_one()

    # =====================================================
    # SORT
    # =====================================================

    query = select(
        ShopListing
    ).where(
        and_(*conditions)
    )

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

    # =====================================================
    # PAGINATION
    # =====================================================

    page = max(page, 1)
    per_page = max(
        1,
        min(per_page, 100),
    )

    offset = (
        page - 1
    ) * per_page

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

    # =====================================================
    # FAVORITES
    # =====================================================

    if user_id and listings:

        listing_ids = [
            item.id
            for item in listings
        ]

        favorite_result = await session.execute(
            select(
                ShopFavorite.listing_id
            ).where(
                ShopFavorite.user_id
                == user_id,
                ShopFavorite.listing_id.in_(
                    listing_ids
                ),
            )
        )

        favorite_ids = set(
            favorite_result.scalars().all()
        )

        for listing in listings:
            listing._is_favorite = (
                listing.id in favorite_ids
            )

    else:

        for listing in listings:
            listing._is_favorite = False

    return listings, total


# =========================================================
# FAVORITES
# =========================================================

async def is_favorite(
    session: AsyncSession,
    user_id: int,
    listing_id: int,
) -> bool:

    result = await session.execute(
        select(ShopFavorite.id).where(
            ShopFavorite.user_id
            == user_id,
            ShopFavorite.listing_id
            == listing_id,
        )
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

    listing = await get_listing_by_id(
        session,
        listing_id,
    )

    if listing:
        listing.favorites_count += 1

    return True


async def remove_favorite(
    session: AsyncSession,
    user_id: int,
    listing_id: int,
) -> bool:

    result = await session.execute(
        select(ShopFavorite).where(
            ShopFavorite.user_id
            == user_id,
            ShopFavorite.listing_id
            == listing_id,
        )
    )

    favorite = result.scalar_one_or_none()

    if not favorite:
        return False

    await session.delete(
        favorite
    )

    listing = await get_listing_by_id(
        session,
        listing_id,
    )

    if listing:
        listing.favorites_count = max(
            0,
            listing.favorites_count - 1,
        )

    return True


# =========================================================
# CART
# =========================================================

async def add_to_cart(
    session: AsyncSession,
    user_id: int,
    listing_id: int,
) -> bool:

    result = await session.execute(
        select(ShopCartItem).where(
            ShopCartItem.user_id
            == user_id,
            ShopCartItem.listing_id
            == listing_id,
        )
    )

    if result.scalar_one_or_none():
        return False

    session.add(
        ShopCartItem(
            user_id=user_id,
            listing_id=listing_id,
        )
    )

    return True


async def remove_from_cart(
    session: AsyncSession,
    user_id: int,
    listing_id: int,
) -> bool:

    result = await session.execute(
        select(ShopCartItem).where(
            ShopCartItem.user_id
            == user_id,
            ShopCartItem.listing_id
            == listing_id,
        )
    )

    item = result.scalar_one_or_none()

    if not item:
        return False

    await session.delete(item)

    return True


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
            ShopCartItem.user_id
            == user_id,
            ShopListing.is_active.is_(True),
        )
        .order_by(
            ShopCartItem.created_at.desc()
        )
    )

    return list(
        result.scalars().all()
    )


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

    return list(
        result.scalars().all()
    )
