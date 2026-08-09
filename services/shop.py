from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.shop import (
    get_shop_listings,
    is_favorite,
    add_favorite,
    remove_favorite,
    add_to_cart,
    remove_from_cart,
    get_cart,
)
from database.shop_models import ShopListing


# =========================================================
# LISTING SERIALIZER
# =========================================================

def serialize_listing(
    listing: ShopListing,
    is_favorite_value: bool = False,
) -> dict:

    return {
        "id": listing.id,
        "username": listing.username,
        "price_rub": listing.price_rub,
        "price_stars": listing.price_stars,
        "seller_id": listing.seller_id,
        "seller_username": None,
        "description": listing.description,
        "title": listing.title,
        "category": None,
        "is_premium": listing.is_premium,
        "is_verified": listing.is_verified,
        "is_favorite": is_favorite_value,
        "is_featured": listing.is_featured,
        "views_count": listing.views_count,
        "favorites_count": listing.favorites_count,
        "beauty_score": listing.beauty_score,
        "estimated_price_rub": (
            listing.estimated_price_rub
        ),
        "ai_card_file_id": (
            listing.ai_card_file_id
        ),
        "ai_card_url": (
            listing.ai_card_url
        ),
        "created_at": (
            listing.created_at.isoformat()
            if listing.created_at
            else None
        ),
    }


# =========================================================
# SHOP LIST
# =========================================================

async def get_shop_page(
    session: AsyncSession,
    user_id: int,
    search: str,
    category: str,
    sort: str,
    page: int,
    per_page: int,
) -> dict:

    listings, total = await get_shop_listings(
        session=session,
        user_id=user_id,
        search=search,
        category=category,
        sort=sort,
        page=page,
        per_page=per_page,
    )

    result = []

    for listing in listings:

        favorite = await is_favorite(
            session,
            user_id,
            listing.id,
        )

        result.append(
            serialize_listing(
                listing,
                favorite,
            )
        )

    return {
        "items": result,
        "total": total,
        "page": page,
        "per_page": per_page,
    }


# =========================================================
# FAVORITE
# =========================================================

async def favorite_listing(
    session: AsyncSession,
    user_id: int,
    listing_id: int,
) -> bool:

    return await add_favorite(
        session,
        user_id,
        listing_id,
    )


async def unfavorite_listing(
    session: AsyncSession,
    user_id: int,
    listing_id: int,
) -> bool:

    return await remove_favorite(
        session,
        user_id,
        listing_id,
    )


# =========================================================
# CART
# =========================================================

async def add_listing_to_cart(
    session: AsyncSession,
    user_id: int,
    listing_id: int,
) -> bool:

    return await add_to_cart(
        session,
        user_id,
        listing_id,
    )


async def remove_listing_from_cart(
    session: AsyncSession,
    user_id: int,
    listing_id: int,
) -> bool:

    return await remove_from_cart(
        session,
        user_id,
        listing_id,
    )


async def get_user_cart(
    session: AsyncSession,
    user_id: int,
) -> dict:

    listings = await get_cart(
        session,
        user_id,
    )

    items = []

    total_rub = 0
    total_stars = 0

    for listing in listings:

        favorite = await is_favorite(
            session,
            user_id,
            listing.id,
        )

        item = serialize_listing(
            listing,
            favorite,
        )

        items.append(item)

        total_rub += listing.price_rub

        if listing.price_stars:
            total_stars += (
                listing.price_stars
            )

    return {
        "items": items,
        "count": len(items),
        "total_rub": total_rub,
        "total_stars": total_stars,
    }
