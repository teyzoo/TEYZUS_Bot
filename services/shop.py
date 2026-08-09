from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from database.repositories.shop import (
    create_listing,
    get_listing_by_id,
    get_public_listings,
    add_favorite,
    remove_favorite,
    add_to_cart,
    remove_from_cart,
    get_cart,
)


# =========================================================
# VALIDATION
# =========================================================

def normalize_username(
    username: str,
) -> str:

    return (
        username
        .strip()
        .lstrip("@")
        .lower()
    )


def validate_price(
    price_rub: int,
) -> None:

    if price_rub <= 0:
        raise ValueError(
            "Цена должна быть больше 0."
        )

    if price_rub > 2_000_000_000:
        raise ValueError(
            "Цена слишком большая."
        )


# =========================================================
# CREATE LISTING
# =========================================================

async def create_shop_listing(
    session: AsyncSession,
    *,
    user: User,
    username: str,
    title: Optional[str],
    description: Optional[str],
    category_id: Optional[int],
    price_rub: int,
    price_stars: Optional[int],
):

    username = normalize_username(
        username
    )

    if not username:
        raise ValueError(
            "Username не указан."
        )

    validate_price(
        price_rub
    )

    if price_stars is not None:
        if price_stars <= 0:
            raise ValueError(
                "Цена в Stars должна быть больше 0."
            )

    existing = await get_listing_by_id(
        session,
        0,
    )

    # Проверяем username через
    # отдельный запрос в repository.
    from database.repositories.shop import (
        get_listing_by_username,
    )

    existing = await get_listing_by_username(
        session,
        username,
    )

    if existing:
        raise ValueError(
            "Этот username уже существует в магазине."
        )

    listing = await create_listing(
        session,
        seller=user,
        username=username,
        title=title,
        description=description,
        category_id=category_id,
        price_rub=price_rub,
        price_stars=price_stars,
    )

    return listing


# =========================================================
# SHOP LIST
# =========================================================

async def get_shop(
    session: AsyncSession,
    *,
    user_id: Optional[int],
    search: str = "",
    category: str = "all",
    sort: str = "new",
    page: int = 1,
    per_page: int = 20,
):

    listings, total = await get_public_listings(
        session,
        user_id=user_id,
        search=search,
        category=category,
        sort=sort,
        page=page,
        per_page=per_page,
    )

    return {
        "items": [
            {
                "id": item.id,
                "username": item.username,
                "price_rub": item.price_rub,
                "price_stars": item.price_stars,
                "seller_id": item.seller_id,
                "seller_username": item.seller_username,
                "description": item.description,
                "category": (
                    str(item.category_id)
                    if item.category_id
                    else None
                ),
                "is_premium": item.is_premium,
                "is_verified": item.is_verified,
                "is_favorite": getattr(
                    item,
                    "_is_favorite",
                    False,
                ),
                "created_at": (
                    item.created_at.isoformat()
                    if item.created_at
                    else None
                ),
            }
            for item in listings
        ],
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

    result = await add_favorite(
        session,
        user_id,
        listing_id,
    )

    await session.commit()

    return result


async def unfavorite_listing(
    session: AsyncSession,
    user_id: int,
    listing_id: int,
) -> bool:

    result = await remove_favorite(
        session,
        user_id,
        listing_id,
    )

    await session.commit()

    return result


# =========================================================
# CART
# =========================================================

async def cart_add(
    session: AsyncSession,
    user_id: int,
    listing_id: int,
) -> bool:

    listing = await get_listing_by_id(
        session,
        listing_id,
    )

    if not listing:
        raise ValueError(
            "Объявление не найдено."
        )

    if not listing.is_active:
        raise ValueError(
            "Объявление недоступно."
        )

    if listing.status != "approved":
        raise ValueError(
            "Объявление ещё не опубликовано."
        )

    if listing.seller_id == user_id:
        raise ValueError(
            "Нельзя добавить своё объявление."
        )

    result = await add_to_cart(
        session,
        user_id,
        listing_id,
    )

    await session.commit()

    return result


async def cart_remove(
    session: AsyncSession,
    user_id: int,
    listing_id: int,
) -> bool:

    result = await remove_from_cart(
        session,
        user_id,
        listing_id,
    )

    await session.commit()

    return result


async def get_user_cart(
    session: AsyncSession,
    user_id: int,
):

    listings = await get_cart(
        session,
        user_id,
    )

    return [
        {
            "id": item.id,
            "username": item.username,
            "price_rub": item.price_rub,
            "price_stars": item.price_stars,
            "seller_username": item.seller_username,
            "description": item.description,
            "is_premium": item.is_premium,
            "is_verified": item.is_verified,
        }
        for item in listings
    ]
