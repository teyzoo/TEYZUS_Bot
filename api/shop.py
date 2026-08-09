from __future__ import annotations

from typing import Optional

from fastapi import (
    APIRouter,
    Header,
    HTTPException,
    Query,
)
from pydantic import BaseModel, Field

from database.session import get_session
from database.models import User
from database.repositories.shop import (
    get_listing_by_id,
)
from services.shop import (
    get_shop,
    favorite_listing,
    unfavorite_listing,
    cart_add,
    cart_remove,
    get_user_cart,
    create_shop_listing,
)


router = APIRouter(
    prefix="/api/miniapp/shop",
    tags=["TEYZUS SHOP"],
)


# =========================================================
# AUTH
# =========================================================

async def get_current_user(
    telegram_id: Optional[int],
) -> User:

    if telegram_id is None:
        raise HTTPException(
            status_code=401,
            detail="Telegram user not found.",
        )

    async with get_session() as session:

        from sqlalchemy import select

        result = await session.execute(
            select(User).where(
                User.telegram_id
                == telegram_id
            )
        )

        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found.",
            )

        if user.is_blocked:
            raise HTTPException(
                status_code=403,
                detail="User is blocked.",
            )

        return user


# =========================================================
# SCHEMAS
# =========================================================

class CreateListingRequest(
    BaseModel
):
    username: str = Field(
        min_length=1,
        max_length=255,
    )

    title: Optional[str] = Field(
        default=None,
        max_length=255,
    )

    description: Optional[str] = Field(
        default=None,
        max_length=5000,
    )

    category_id: Optional[int] = None

    price_rub: int = Field(
        gt=0,
        le=2_000_000_000,
    )

    price_stars: Optional[int] = Field(
        default=None,
        gt=0,
    )


# =========================================================
# LISTINGS
# =========================================================

@router.get("")
async def shop_list(
    search: str = "",
    category: str = "all",
    sort: str = "new",
    page: int = Query(
        default=1,
        ge=1,
    ),
    per_page: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    x_telegram_user_id: Optional[int] = Header(
        default=None
    ),
):

    async with get_session() as session:

        user_id = None

        if x_telegram_user_id:

            from sqlalchemy import select

            result = await session.execute(
                select(User.id).where(
                    User.telegram_id
                    == x_telegram_user_id
                )
            )

            user_id = (
                result.scalar_one_or_none()
            )

        return await get_shop(
            session,
            user_id=user_id,
            search=search,
            category=category,
            sort=sort,
            page=page,
            per_page=per_page,
        )


# =========================================================
# LISTING DETAILS
# =========================================================

@router.get(
    "/{listing_id}"
)
async def listing_details(
    listing_id: int,
):

    async with get_session() as session:

        listing = await get_listing_by_id(
            session,
            listing_id,
        )

        if not listing:
            raise HTTPException(
                status_code=404,
                detail="Объявление не найдено.",
            )

        if (
            not listing.is_active
            or listing.status != "approved"
        ):
            raise HTTPException(
                status_code=404,
                detail="Объявление недоступно.",
            )

        listing.views_count += 1

        await session.commit()

        return {
            "id": listing.id,
            "username": listing.username,
            "title": listing.title,
            "description": listing.description,
            "price_rub": listing.price_rub,
            "price_stars": listing.price_stars,
            "seller_id": listing.seller_id,
            "seller_username": listing.seller_username,
            "category_id": listing.category_id,
            "is_premium": listing.is_premium,
            "is_verified": listing.is_verified,
            "is_featured": listing.is_featured,
            "views_count": listing.views_count,
            "favorites_count": listing.favorites_count,
            "created_at": (
                listing.created_at.isoformat()
            ),
        }


# =========================================================
# CREATE LISTING
# =========================================================

@router.post(
    "/create"
)
async def create_listing_api(
    payload: CreateListingRequest,
    x_telegram_user_id: Optional[int] = Header(
        default=None
    ),
):

    user = await get_current_user(
        x_telegram_user_id
    )

    async with get_session() as session:

        # Получаем актуального пользователя
        from sqlalchemy import select

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
                detail="User not found.",
            )

        try:

            listing = await create_shop_listing(
                session,
                user=db_user,
                username=payload.username,
                title=payload.title,
                description=payload.description,
                category_id=payload.category_id,
                price_rub=payload.price_rub,
                price_stars=payload.price_stars,
            )

            await session.commit()

            return {
                "success": True,
                "message": (
                    "Объявление отправлено "
                    "на модерацию."
                ),
                "listing": {
                    "id": listing.id,
                    "username": listing.username,
                    "status": listing.status,
                    "price_rub": listing.price_rub,
                    "price_stars": listing.price_stars,
                },
            }

        except ValueError as error:

            await session.rollback()

            raise HTTPException(
                status_code=400,
                detail=str(error),
            )


# =========================================================
# FAVORITE
# =========================================================

@router.post(
    "/{listing_id}/favorite"
)
async def add_listing_favorite(
    listing_id: int,
    x_telegram_user_id: Optional[int] = Header(
        default=None
    ),
):

    user = await get_current_user(
        x_telegram_user_id
    )

    async with get_session() as session:

        try:

            result = await favorite_listing(
                session,
                user.id,
                listing_id,
            )

            return {
                "success": True,
                "added": result,
            }

        except Exception:

            await session.rollback()

            raise HTTPException(
                status_code=500,
                detail="Не удалось добавить в избранное.",
            )


@router.delete(
    "/{listing_id}/favorite"
)
async def remove_listing_favorite(
    listing_id: int,
    x_telegram_user_id: Optional[int] = Header(
        default=None
    ),
):

    user = await get_current_user(
        x_telegram_user_id
    )

    async with get_session() as session:

        try:

            result = await unfavorite_listing(
                session,
                user.id,
                listing_id,
            )

            return {
                "success": True,
                "removed": result,
            }

        except Exception:

            await session.rollback()

            raise HTTPException(
                status_code=500,
                detail="Не удалось убрать из избранного.",
            )


# =========================================================
# CART
# =========================================================

@router.get(
    "/cart/list"
)
async def get_cart_api(
    x_telegram_user_id: Optional[int] = Header(
        default=None
    ),
):

    user = await get_current_user(
        x_telegram_user_id
    )

    async with get_session() as session:

        items = await get_user_cart(
            session,
            user.id,
        )

        return {
            "items": items,
            "count": len(items),
        }


@router.post(
    "/{listing_id}/cart"
)
async def add_cart_api(
    listing_id: int,
    x_telegram_user_id: Optional[int] = Header(
        default=None
    ),
):

    user = await get_current_user(
        x_telegram_user_id
    )

    async with get_session() as session:

        try:

            added = await cart_add(
                session,
                user.id,
                listing_id,
            )

            return {
                "success": True,
                "added": added,
            }

        except ValueError as error:

            await session.rollback()

            raise HTTPException(
                status_code=400,
                detail=str(error),
            )


@router.delete(
    "/{listing_id}/cart"
)
async def remove_cart_api(
    listing_id: int,
    x_telegram_user_id: Optional[int] = Header(
        default=None
    ),
):

    user = await get_current_user(
        x_telegram_user_id
    )

    async with get_session() as session:

        removed = await cart_remove(
            session,
            user.id,
            listing_id,
        )

        return {
            "success": True,
            "removed": removed,
        }
