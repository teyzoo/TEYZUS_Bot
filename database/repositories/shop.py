from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    and_,
    delete,
    func,
    or_,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

from database.shop_models import (
    ShopCategory,
    ShopFavorite,
    ShopListing,
)


# =========================================================
# SHOP LISTINGS
# =========================================================

async def get_shop_listings(
    session: AsyncSession,
    *,
    user_id: Optional[int] = None,
    search: Optional[str] = None,
    category: str = "all",
    sort: str = "new",
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[ShopListing], int]:
    """
    Получает опубликованные объявления TEYZUS SHOP.

    Возвращает:

        (
            список объявлений,
            общее количество
        )
    """

    page = max(page, 1)

    per_page = max(
        1,
        min(per_page, 100),
    )

    conditions = [
        ShopListing.status == "active"
    ]

    # =====================================================
    # SEARCH
    # =====================================================

    if search:
        search_value = search.strip().lstrip("@")

        if search_value:
            conditions.append(
                or_(
                    ShopListing.username.ilike(
                        f"%{search_value}%"
                    ),
                    ShopListing.title.ilike(
                        f"%{search_value}%"
                    ),
                )
            )

    # =====================================================
    # CATEGORY
    # =====================================================

    if category == "premium":
        conditions.append(
            ShopListing.is_premium.is_(True)
        )

    # "popular" и "cheap" реализуются сортировкой.
    # "new" также сортируется ниже.

    # =====================================================
    # COUNT
    # =====================================================

    count_query = (
        select(
            func.count(
                ShopListing.id
            )
        )
        .where(
            and_(*conditions)
        )
    )

    count_result = await session.execute(
        count_query
    )

    total = count_result.scalar_one() or 0

    # =====================================================
    # SORT
    # =====================================================

    query = (
        select(ShopListing)
        .where(
            and_(*conditions)
        )
    )

    if category == "popular":
        query = query.order_by(
            ShopListing.views.desc(),
            ShopListing.favorites_count.desc(),
            ShopListing.created_at.desc(),
        )

    elif category == "cheap":
        query = query.order_by(
            ShopListing.price_rub.asc(),
            ShopListing.created_at.desc(),
        )

    elif sort == "price_asc":
        query = query.order_by(
            ShopListing.price_rub.asc(),
        )

    elif sort == "price_desc":
        query = query.order_by(
            ShopListing.price_rub.desc(),
        )

    elif sort == "popular":
        query = query.order_by(
            ShopListing.views.desc(),
            ShopListing.favorites_count.desc(),
        )

    else:
        query = query.order_by(
            ShopListing.created_at.desc()
        )

    # =====================================================
    # PAGINATION
    # =====================================================

    offset = (
        (page - 1)
        * per_page
    )

    query = (
        query
        .offset(offset)
        .limit(per_page)
    )

    result = await session.execute(
        query
    )

    listings = list(
        result.scalars().all()
    )

    return listings, total


# =========================================================
# GET LISTING
# =========================================================

async def get_shop_listing(
    session: AsyncSession,
    listing_id: int,
) -> Optional[ShopListing]:
    result = await session.execute(
        select(ShopListing)
        .where(
            ShopListing.id
            == listing_id
        )
    )

    return result.scalar_one_or_none()


# =========================================================
# FAVORITE CHECK
# =========================================================

async def is_favorite(
    session: AsyncSession,
    *,
    user_id: int,
    listing_id: int,
) -> bool:
    result = await session.execute(
        select(ShopFavorite.id)
        .where(
            ShopFavorite.user_id
            == user_id,
            ShopFavorite.listing_id
            == listing_id,
        )
        .limit(1)
    )

    return result.scalar_one_or_none() is not None


# =========================================================
# ADD FAVORITE
# =========================================================

async def add_favorite(
    session: AsyncSession,
    *,
    user_id: int,
    listing_id: int,
) -> bool:
    existing = await session.execute(
        select(ShopFavorite.id)
        .where(
            ShopFavorite.user_id
            == user_id,
            ShopFavorite.listing_id
            == listing_id,
        )
        .limit(1)
    )

    if existing.scalar_one_or_none() is not None:
        return False

    favorite = ShopFavorite(
        user_id=user_id,
        listing_id=listing_id,
    )

    session.add(favorite)

    # Обновляем счётчик.
    listing = await get_shop_listing(
        session,
        listing_id,
    )

    if listing:
        listing.favorites_count += 1

    await session.commit()

    return True


# =========================================================
# REMOVE FAVORITE
# =========================================================

async def remove_favorite(
    session: AsyncSession,
    *,
    user_id: int,
    listing_id: int,
) -> bool:
    result = await session.execute(
        select(ShopFavorite)
        .where(
            ShopFavorite.user_id
            == user_id,
            ShopFavorite.listing_id
            == listing_id,
        )
    )

    favorite = (
        result.scalar_one_or_none()
    )

    if favorite is None:
        return False

    await session.delete(
        favorite
    )

    listing = await get_shop_listing(
        session,
        listing_id,
    )

    if listing:
        listing.favorites_count = max(
            0,
            listing.favorites_count - 1,
        )

    await session.commit()

    return True


# =========================================================
# CATEGORIES
# =========================================================

async def get_shop_categories(
    session: AsyncSession,
) -> list[ShopCategory]:
    result = await session.execute(
        select(ShopCategory)
        .where(
            ShopCategory.enabled.is_(True)
        )
        .order_by(
            ShopCategory.sort_order.asc(),
            ShopCategory.id.asc(),
        )
    )

    return list(
        result.scalars().all()
    )


# =========================================================
# CREATE LISTING
# =========================================================

async def create_shop_listing(
    session: AsyncSession,
    *,
    seller_id: int,
    username: str,
    title: str,
    description: Optional[str],
    price_rub: Decimal,
    price_stars: Optional[int] = None,
    category_id: Optional[int] = None,
    is_premium: bool = False,
) -> ShopListing:

    normalized_username = (
        username
        .strip()
        .lstrip("@")
        .lower()
    )

    listing = ShopListing(
        username=normalized_username,
        title=title.strip(),
        description=description,
        price_rub=price_rub,
        price_stars=price_stars,
        seller_id=seller_id,
        category_id=category_id,
        is_premium=is_premium,
        is_verified=False,
        status="moderation",
        cover_status="pending",
    )

    session.add(listing)

    await session.commit()

    await session.refresh(
        listing
    )

    return listing


# =========================================================
# INCREMENT VIEWS
# =========================================================

async def increment_listing_views(
    session: AsyncSession,
    listing_id: int,
) -> None:
    listing = await get_shop_listing(
        session,
        listing_id,
    )

    if listing is None:
        return

    listing.views += 1

    await session.commit()
