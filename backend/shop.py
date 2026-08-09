from __future__ import annotations

from typing import Optional

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    ShopFavorite,
    ShopListing,
    SellerProfile,
    User,
)


# =========================================================
# SHOP SETTINGS
# =========================================================

DEFAULT_COMMISSION_PERCENT = 5


# =========================================================
# GET LISTINGS
# =========================================================

async def get_shop_listings(
    session: AsyncSession,
    user: Optional[User],
    search: str = "",
    category: str = "all",
    sort: str = "new",
    page: int = 1,
    per_page: int = 20,
):
    page = max(page, 1)
    per_page = min(
        max(per_page, 1),
        50,
    )

    query = (
        select(
            ShopListing,
            User.username.label(
                "seller_username"
            ),
        )
        .join(
            User,
            User.id == ShopListing.seller_id,
        )
        .where(
            ShopListing.status == "approved"
        )
    )

    if search:
        search_value = (
            search.strip()
            .lstrip("@")
        )

        if search_value:
            query = query.where(
                ShopListing.username.ilike(
                    f"%{search_value}%"
                )
            )

    if category == "premium":
        query = query.where(
            ShopListing.is_premium.is_(True)
        )

    elif category == "new":
        query = query.order_by(
            ShopListing.created_at.desc()
        )

    elif category == "cheap":
        query = query.order_by(
            ShopListing.price_rub.asc()
        )

    elif category == "popular":
        query = query.order_by(
            ShopListing.views.desc(),
            ShopListing.favorites_count.desc(),
        )

    if sort == "price_asc":
        query = query.order_by(
            ShopListing.price_rub.asc()
        )

    elif sort == "price_desc":
        query = query.order_by(
            ShopListing.price_rub.desc()
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

    count_query = select(
        func.count(ShopListing.id)
    ).where(
        ShopListing.status == "approved"
    )

    if search:
        search_value = (
            search.strip()
            .lstrip("@")
        )

        if search_value:
            count_query = count_query.where(
                ShopListing.username.ilike(
                    f"%{search_value}%"
                )
            )

    if category == "premium":
        count_query = count_query.where(
            ShopListing.is_premium.is_(True)
        )

    total_result = await session.execute(
        count_query
    )

    total = (
        total_result.scalar_one_or_none()
        or 0
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

    rows = result.all()

    favorites = set()

    if user and rows:
        listing_ids = [
            row.ShopListing.id
            for row in rows
        ]

        favorite_result = await session.execute(
            select(
                ShopFavorite.listing_id
            ).where(
                ShopFavorite.user_id == user.id,
                ShopFavorite.listing_id.in_(
                    listing_ids
                ),
            )
        )

        favorites = set(
            favorite_result.scalars().all()
        )

    items = []

    for row in rows:
        listing = row.ShopListing

        items.append(
            {
                "id": listing.id,
                "username": listing.username,
                "price_rub": listing.price_rub,
                "price_stars": listing.price_stars,
                "seller_id": listing.seller_id,
                "seller_username": row.seller_username,
                "description": listing.description,
                "category": listing.category,
                "is_premium": listing.is_premium,
                "is_verified": listing.is_verified,
                "is_favorite": (
                    listing.id
                    in favorites
                ),
                "created_at": (
                    listing.created_at.isoformat()
                ),
            }
        )

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
    }


# =========================================================
# FAVORITE
# =========================================================

async def add_favorite(
    session: AsyncSession,
    user: User,
    listing_id: int,
) -> bool:

    listing_result = await session.execute(
        select(ShopListing).where(
            ShopListing.id == listing_id,
            ShopListing.status == "approved",
        )
    )

    listing = (
        listing_result.scalar_one_or_none()
    )

    if not listing:
        return False

    existing_result = await session.execute(
        select(ShopFavorite).where(
            ShopFavorite.user_id == user.id,
            ShopFavorite.listing_id == listing_id,
        )
    )

    existing = (
        existing_result.scalar_one_or_none()
    )

    if existing:
        return True

    favorite = ShopFavorite(
        user_id=user.id,
        listing_id=listing_id,
    )

    session.add(favorite)

    listing.favorites_count += 1

    await session.commit()

    return True


async def remove_favorite(
    session: AsyncSession,
    user: User,
    listing_id: int,
) -> bool:

    result = await session.execute(
        select(ShopFavorite).where(
            ShopFavorite.user_id == user.id,
            ShopFavorite.listing_id == listing_id,
        )
    )

    favorite = (
        result.scalar_one_or_none()
    )

    if not favorite:
        return True

    listing_result = await session.execute(
        select(ShopListing).where(
            ShopListing.id == listing_id
        )
    )

    listing = (
        listing_result.scalar_one_or_none()
    )

    await session.delete(
        favorite
    )

    if listing:
        listing.favorites_count = max(
            listing.favorites_count - 1,
            0,
        )

    await session.commit()

    return True


# =========================================================
# CREATE LISTING
# =========================================================

async def create_listing(
    session: AsyncSession,
    seller: User,
    username: str,
    price_rub: int,
    price_stars: Optional[int] = None,
    description: Optional[str] = None,
    category: Optional[str] = None,
    is_premium: bool = False,
):
    username = (
        username.strip()
        .lstrip("@")
    )

    if not username:
        raise ValueError(
            "Username is required."
        )

    if price_rub <= 0:
        raise ValueError(
            "Price must be greater than zero."
        )

    existing_result = await session.execute(
        select(ShopListing).where(
            ShopListing.username.ilike(
                username
            ),
            ShopListing.status.in_(
                [
                    "pending",
                    "approved",
                ]
            ),
        )
    )

    existing = (
        existing_result.scalar_one_or_none()
    )

    if existing:
        raise ValueError(
            "This username already has a listing."
        )

    listing = ShopListing(
        username=username,
        seller_id=seller.id,
        price_rub=price_rub,
        price_stars=price_stars,
        description=description,
        category=category,
        is_premium=is_premium,
        status="pending",
    )

    session.add(listing)

    await session.commit()
    await session.refresh(listing)

    return listing


# =========================================================
# ADMIN APPROVE
# =========================================================

async def approve_listing(
    session: AsyncSession,
    listing_id: int,
):
    result = await session.execute(
        select(ShopListing).where(
            ShopListing.id == listing_id
        )
    )

    listing = (
        result.scalar_one_or_none()
    )

    if not listing:
        return None

    listing.status = "approved"

    await session.commit()
    await session.refresh(listing)

    return listing


# =========================================================
# ADMIN REJECT
# =========================================================

async def reject_listing(
    session: AsyncSession,
    listing_id: int,
):
    result = await session.execute(
        select(ShopListing).where(
            ShopListing.id == listing_id
        )
    )

    listing = (
        result.scalar_one_or_none()
    )

    if not listing:
        return None

    listing.status = "rejected"

    await session.commit()
    await session.refresh(listing)

    return listing
