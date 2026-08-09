from __future__ import annotations

import hashlib
import hmac
import json
from typing import Optional
from urllib.parse import parse_qsl

from fastapi import APIRouter, Header, HTTPException, Query
from sqlalchemy import select

from config import settings
from database.models import User
from database.session import get_session
from database.repositories.shop import (
    add_favorite,
    get_shop_listing,
    get_shop_listings,
    is_favorite,
    remove_favorite,
)


router = APIRouter(
    prefix="/api/miniapp/shop",
    tags=["TEYZUS SHOP"],
)


# =========================================================
# TELEGRAM INIT DATA
# =========================================================

def validate_telegram_init_data(
    init_data: str,
) -> Optional[dict]:
    """
    Проверяет Telegram Mini App initData.

    Telegram передаёт строку примерно такого вида:

        query_id=...
        user=...
        auth_date=...
        hash=...

    Для проверки используется bot token.
    """

    if not init_data:
        return None

    try:
        parsed = dict(
            parse_qsl(
                init_data,
                keep_blank_values=True,
            )
        )

        received_hash = parsed.pop(
            "hash",
            None,
        )

        if not received_hash:
            return None

        data_check_string = "\n".join(
            f"{key}={value}"
            for key, value in sorted(
                parsed.items()
            )
        )

        secret_key = hmac.new(
            b"WebAppData",
            settings.bot_token.encode(),
            hashlib.sha256,
        ).digest()

        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(
            calculated_hash,
            received_hash,
        ):
            return None

        user_raw = parsed.get(
            "user"
        )

        if not user_raw:
            return None

        user_data = json.loads(
            user_raw
        )

        return user_data

    except Exception:
        return None


# =========================================================
# CURRENT USER
# =========================================================

async def get_current_user(
    init_data: Optional[str],
) -> Optional[User]:

    if not init_data:
        return None

    telegram_user = (
        validate_telegram_init_data(
            init_data
        )
    )

    if not telegram_user:
        return None

    telegram_id = telegram_user.get(
        "id"
    )

    if not telegram_id:
        return None

    async with get_session() as session:

        result = await session.execute(
            select(User).where(
                User.telegram_id
                == int(telegram_id)
            )
        )

        return result.scalar_one_or_none()


# =========================================================
# SHOP LISTINGS
# =========================================================

@router.get("")
async def shop_listings(
    search: str = Query(
        default="",
        max_length=64,
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
    x_telegram_init_data: Optional[str] = Header(
        default=None,
    ),
):
    """
    GET /api/miniapp/shop

    Возвращает объявления TEYZUS SHOP.
    """

    user = await get_current_user(
        x_telegram_init_data
    )

    async with get_session() as session:

        listings, total = (
            await get_shop_listings(
                session,
                user_id=(
                    user.id
                    if user
                    else None
                ),
                search=search,
                category=category,
                sort=sort,
                page=page,
                per_page=per_page,
            )
        )

        items = []

        for listing in listings:

            favorite = False

            if user:
                favorite = (
                    await is_favorite(
                        session,
                        user_id=user.id,
                        listing_id=listing.id,
                    )
                )

            seller_username = None

            seller_result = (
                await session.execute(
                    select(
                        User.username
                    ).where(
                        User.id
                        == listing.seller_id
                    )
                )
            )

            seller_username = (
                seller_result.scalar_one_or_none()
            )

            items.append(
                {
                    "id": listing.id,
                    "username": listing.username,
                    "price_rub": float(
                        listing.price_rub
                    ),
                    "price_stars": (
                        listing.price_stars
                    ),
                    "seller_id": listing.seller_id,
                    "seller_username": (
                        seller_username
                    ),
                    "description": (
                        listing.description
                    ),
                    "category": (
                        str(
                            listing.category_id
                        )
                        if listing.category_id
                        else None
                    ),
                    "is_premium": (
                        listing.is_premium
                    ),
                    "is_verified": (
                        listing.is_verified
                    ),
                    "is_favorite": favorite,
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
# ADD FAVORITE
# =========================================================

@router.post(
    "/{listing_id}/favorite"
)
async def favorite_listing(
    listing_id: int,
    x_telegram_init_data: Optional[str] = Header(
        default=None,
    ),
):
    """
    Добавляет объявление в избранное.
    """

    user = await get_current_user(
        x_telegram_init_data
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail=(
                "Telegram authorization required"
            ),
        )

    async with get_session() as session:

        listing = await get_shop_listing(
            session,
            listing_id,
        )

        if not listing:
            raise HTTPException(
                status_code=404,
                detail="Listing not found",
            )

        if listing.status != "active":
            raise HTTPException(
                status_code=400,
                detail=(
                    "Listing is not available"
                ),
            )

        await add_favorite(
            session,
            user_id=user.id,
            listing_id=listing_id,
        )

    return {
        "success": True,
    }


# =========================================================
# REMOVE FAVORITE
# =========================================================

@router.delete(
    "/{listing_id}/favorite"
)
async def unfavorite_listing(
    listing_id: int,
    x_telegram_init_data: Optional[str] = Header(
        default=None,
    ),
):
    """
    Удаляет объявление из избранного.
    """

    user = await get_current_user(
        x_telegram_init_data
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail=(
                "Telegram authorization required"
            ),
        )

    async with get_session() as session:

        listing = await get_shop_listing(
            session,
            listing_id,
        )

        if not listing:
            raise HTTPException(
                status_code=404,
                detail="Listing not found",
            )

        await remove_favorite(
            session,
            user_id=user.id,
            listing_id=listing_id,
        )

    return {
        "success": True,
    }
