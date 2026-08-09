from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select

from backend.shop import (
    add_favorite,
    create_listing,
    get_shop_listings,
    remove_favorite,
)
from database.models import User
from database.session import get_session


router = APIRouter(
    prefix="/api/miniapp/shop",
    tags=["TEYZUS SHOP"],
)


# =========================================================
# TEMP TELEGRAM AUTH
# =========================================================

async def get_current_user(
    telegram_init_data: Optional[str],
) -> User:

    """
    Сейчас используется упрощённая
    авторизация.

    В следующем этапе сюда подключим
    полноценную Telegram WebApp
    initData validation через HMAC.
    """

    if not telegram_init_data:
        raise HTTPException(
            status_code=401,
            detail="Telegram authorization required",
        )

    # TODO:
    # Здесь будет:
    #
    # validate_telegram_init_data()
    #
    # После проверки получаем telegram_id.

    raise HTTPException(
        status_code=401,
        detail="Telegram initData validation is not connected yet",
    )


# =========================================================
# SHOP LISTINGS
# =========================================================

@router.get("")
async def shop_listings(
    search: str = "",
    category: str = "all",
    sort: str = "new",
    page: int = Query(
        1,
        ge=1,
    ),
    per_page: int = Query(
        20,
        ge=1,
        le=50,
    ),
    x_telegram_init_data: Optional[str] = Header(
        default=None,
        alias="X-Telegram-Init-Data",
    ),
):

    async with get_session() as session:

        user = None

        if x_telegram_init_data:
            try:
                user = await get_current_user(
                    x_telegram_init_data
                )
            except HTTPException:
                user = None

        return await get_shop_listings(
            session=session,
            user=user,
            search=search,
            category=category,
            sort=sort,
            page=page,
            per_page=per_page,
        )


# =========================================================
# FAVORITE
# =========================================================

@router.post(
    "/{listing_id}/favorite"
)
async def favorite_listing(
    listing_id: int,
    x_telegram_init_data: Optional[str] = Header(
        default=None,
        alias="X-Telegram-Init-Data",
    ),
):

    user = await get_current_user(
        x_telegram_init_data
    )

    async with get_session() as session:

        result = await session.execute(
            select(User).where(
                User.id == user.id
            )
        )

        db_user = (
            result.scalar_one_or_none()
        )

        if not db_user:
            raise HTTPException(
                status_code=404,
                detail="User not found",
            )

        success = await add_favorite(
            session,
            db_user,
            listing_id,
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail="Listing not found",
            )

        return {
            "success": True
        }


@router.delete(
    "/{listing_id}/favorite"
)
async def unfavorite_listing(
    listing_id: int,
    x_telegram_init_data: Optional[str] = Header(
        default=None,
        alias="X-Telegram-Init-Data",
    ),
):

    user = await get_current_user(
        x_telegram_init_data
    )

    async with get_session() as session:

        result = await session.execute(
            select(User).where(
                User.id == user.id
            )
        )

        db_user = (
            result.scalar_one_or_none()
        )

        if not db_user:
            raise HTTPException(
                status_code=404,
                detail="User not found",
            )

        success = await remove_favorite(
            session,
            db_user,
            listing_id,
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail="Listing not found",
            )

        return {
            "success": True
        }


# =========================================================
# CREATE LISTING
# =========================================================

class CreateListingRequest(BaseModel):
    username: str = Field(
        min_length=5,
        max_length=255,
    )

    price_rub: int = Field(
        gt=0
    )

    price_stars: Optional[int] = Field(
        default=None,
        ge=1,
    )

    description: Optional[str] = Field(
        default=None,
        max_length=5000,
    )

    category: Optional[str] = Field(
        default=None,
        max_length=64,
    )

    is_premium: bool = False


@router.post(
    "/create"
)
async def create_shop_listing(
    payload: CreateListingRequest,
    x_telegram_init_data: Optional[str] = Header(
        default=None,
        alias="X-Telegram-Init-Data",
    ),
):

    user = await get_current_user(
        x_telegram_init_data
    )

    async with get_session() as session:

        result = await session.execute(
            select(User).where(
                User.id == user.id
            )
        )

        db_user = (
            result.scalar_one_or_none()
        )

        if not db_user:
            raise HTTPException(
                status_code=404,
                detail="User not found",
            )

        try:

            listing = await create_listing(
                session=session,
                seller=db_user,
                username=payload.username,
                price_rub=payload.price_rub,
                price_stars=payload.price_stars,
                description=payload.description,
                category=payload.category,
                is_premium=payload.is_premium,
            )

        except ValueError as error:

            raise HTTPException(
                status_code=400,
                detail=str(error),
            )

        return {
            "success": True,
            "listing": {
                "id": listing.id,
                "username": listing.username,
                "price_rub": listing.price_rub,
                "price_stars": listing.price_stars,
                "status": listing.status,
            },
        }
