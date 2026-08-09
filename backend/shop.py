from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select

from database.models import User
from database.repositories.shop import ShopRepository
from database.session import get_session


router = APIRouter(
    prefix="/api/miniapp/shop",
    tags=["TEYZUS SHOP"],
)


# =========================================================
# TELEGRAM USER
# =========================================================

async def get_current_user(
    telegram_init_data: Optional[str],
) -> User:

    if not telegram_init_data:
        raise HTTPException(
            status_code=401,
            detail="Telegram authorization required",
        )

    # -----------------------------------------------------
    # ВАЖНО
    # -----------------------------------------------------
    # На следующем этапе здесь будет полноценная проверка
    # Telegram WebApp initData через BOT TOKEN.
    #
    # Пока ожидаем Telegram ID из заголовка после
    # подключения middleware авторизации.
    #
    # Этот участок НЕ должен использоваться как финальная
    # защита production API.
    # -----------------------------------------------------

    try:
        telegram_id = int(
            telegram_init_data
        )
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid Telegram authorization",
        )

    async with get_session() as session:

        result = await session.execute(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(
                status_code=404,
                detail="User not found",
            )

        if user.is_blocked:
            raise HTTPException(
                status_code=403,
                detail="User blocked",
            )

        return user


# =========================================================
# RESPONSE SCHEMA
# =========================================================

class ShopListingResponse(
    BaseModel
):
    id: int

    username: str

    title: str

    description: Optional[str]

    price_rub: int

    price_stars: Optional[int]

    seller_id: int

    seller_username: Optional[str]

    category: Optional[str]

    is_premium: bool

    is_verified: bool

    is_favorite: bool

    created_at: str


class ShopResponse(
    BaseModel
):
    items: list[
        ShopListingResponse
    ]

    total: int

    page: int

    per_page: int


# =========================================================
# LISTINGS
# =========================================================

@router.get(
    "",
    response_model=ShopResponse,
)
async def get_shop(
    search: str = Query(
        default="",
        max_length=100,
    ),
    category: str = Query(
        default="all",
    ),
    sort: str = Query(
        default="new",
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
    per_page: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    x_telegram_init_data: Optional[
        str
    ] = Header(
        default=None,
    ),
):
    """
    Получение объявлений TEYZUS SHOP.
    """

    user = await get_current_user(
        x_telegram_init_data
    )

    allowed_categories = {
        "all",
        "popular",
        "new",
        "cheap",
        "premium",
    }

    if category not in allowed_categories:
        category = "all"

    allowed_sorts = {
        "new",
        "price_asc",
        "price_desc",
        "popular",
    }

    if sort not in allowed_sorts:
        sort = "new"

    async with get_session() as session:

        listings, total = (
            await ShopRepository.get_listings(
                session,
                search=search,
                category=category,
                sort=sort,
                page=page,
                per_page=per_page,
                user_id=user.id,
            )
        )

        response_items = []

        for listing in listings:

            seller_result = (
                await session.execute(
                    select(User).where(
                        User.id
                        == listing.seller_id
                    )
                )
            )

            seller = (
                seller_result.scalar_one_or_none()
            )

            favorite = (
                await ShopRepository.is_favorite(
                    session,
                    user_id=user.id,
                    listing_id=listing.id,
                )
            )

            response_items.append(
                ShopListingResponse(
                    id=listing.id,
                    username=listing.username,
                    title=listing.title,
                    description=listing.description,
                    price_rub=listing.price_rub,
                    price_stars=listing.price_stars,
                    seller_id=listing.seller_id,
                    seller_username=(
                        seller.username
                        if seller
                        else None
                    ),
                    category=listing.category,
                    is_premium=listing.is_premium,
                    is_verified=listing.is_verified,
                    is_favorite=favorite,
                    created_at=listing.created_at.isoformat(),
                )
            )

        return ShopResponse(
            items=response_items,
            total=total,
            page=page,
            per_page=per_page,
        )


# =========================================================
# FAVORITE
# =========================================================

@router.post(
    "/{listing_id}/favorite"
)
async def add_favorite(
    listing_id: int,
    x_telegram_init_data: Optional[
        str
    ] = Header(
        default=None,
    ),
):
    user = await get_current_user(
        x_telegram_init_data
    )

    async with get_session() as session:

        listing = (
            await ShopRepository.get_listing(
                session,
                listing_id,
            )
        )

        if listing is None:
            raise HTTPException(
                status_code=404,
                detail="Listing not found",
            )

        await ShopRepository.add_favorite(
            session,
            user_id=user.id,
            listing_id=listing_id,
        )

        await session.commit()

        return {
            "success": True
        }


# =========================================================
# REMOVE FAVORITE
# =========================================================

@router.delete(
    "/{listing_id}/favorite"
)
async def remove_favorite(
    listing_id: int,
    x_telegram_init_data: Optional[
        str
    ] = Header(
        default=None,
    ),
):
    user = await get_current_user(
        x_telegram_init_data
    )

    async with get_session() as session:

        await ShopRepository.remove_favorite(
            session,
            user_id=user.id,
            listing_id=listing_id,
        )

        await session.commit()

        return {
            "success": True
        }
