from __future__ import annotations

from typing import Optional

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
)
from pydantic import BaseModel, Field
from sqlalchemy import select

from backend.telegram_auth import (
    get_current_user,
)
from database.models import (
    ShopCartItem,
    ShopListing,
    User,
)
from database.repositories.shop import (
    ShopRepository,
)
from database.session import (
    get_session,
)


router = APIRouter(
    prefix="/api/miniapp/shop",
    tags=[
        "TEYZUS SHOP"
    ],
)


# =========================================================
# RESPONSE MODELS
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


class ShopListingDetailResponse(
    ShopListingResponse
):
    views: int

    favorites_count: int

    status: str


class CartItemResponse(
    BaseModel
):
    listing_id: int

    username: str

    title: str

    price_rub: int

    price_stars: Optional[int]


class CartResponse(
    BaseModel
):
    items: list[
        CartItemResponse
    ]

    total_rub: int

    total_stars: int


class CreateListingRequest(
    BaseModel
):
    username: str = Field(
        min_length=1,
        max_length=255,
    )

    title: str = Field(
        min_length=1,
        max_length=255,
    )

    description: Optional[str] = Field(
        default=None,
        max_length=5000,
    )

    price_rub: int = Field(
        ge=1,
    )

    price_stars: Optional[int] = Field(
        default=None,
        ge=1,
    )

    category: Optional[str] = Field(
        default=None,
        max_length=64,
    )

    is_premium: bool = False


# =========================================================
# LISTINGS
# =========================================================

@router.get(
    "",
    response_model=ShopResponse,
)
async def get_shop(
    user: User = __import__(
        "fastapi"
    ).Depends(
        get_current_user
    ),
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
):

    allowed_categories = {
        "all",
        "popular",
        "new",
        "cheap",
        "premium",
    }

    allowed_sorts = {
        "new",
        "price_asc",
        "price_desc",
        "popular",
    }

    if category not in allowed_categories:
        category = "all"

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
            )
        )

        items = []

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

            items.append(
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
            items=items,
            total=total,
            page=page,
            per_page=per_page,
        )


# =========================================================
# LISTING DETAILS
# =========================================================

@router.get(
    "/{listing_id}",
    response_model=ShopListingDetailResponse,
)
async def get_listing(
    listing_id: int,
    user: User = __import__(
        "fastapi"
    ).Depends(
        get_current_user
    ),
):

    async with get_session() as session:

        listing = (
            await ShopRepository.get_active_listing(
                session,
                listing_id,
            )
        )

        if listing is None:
            raise HTTPException(
                status_code=404,
                detail="Listing not found",
            )

        await ShopRepository.increment_views(
            session,
            listing_id,
        )

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

        await session.commit()

        return ShopListingDetailResponse(
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
            views=listing.views,
            favorites_count=listing.favorites_count,
            status=listing.status,
        )


# =========================================================
# CREATE LISTING
# =========================================================

@router.post(
    "/listings",
)
async def create_listing(
    data: CreateListingRequest,
    user: User = __import__(
        "fastapi"
    ).Depends(
        get_current_user
    ),
):

    async with get_session() as session:

        listing = (
            await ShopRepository.create_listing(
                session,
                seller_id=user.id,
                username=data.username,
                title=data.title,
                description=data.description,
                price_rub=data.price_rub,
                price_stars=data.price_stars,
                category=data.category,
                is_premium=data.is_premium,
            )
        )

        await session.commit()

        return {
            "success": True,
            "listing_id": listing.id,
            "status": "pending",
            "message": (
                "Объявление отправлено "
                "на модерацию."
            ),
        }


# =========================================================
# FAVORITE
# =========================================================

@router.post(
    "/{listing_id}/favorite",
)
async def add_favorite(
    listing_id: int,
    user: User = __import__(
        "fastapi"
    ).Depends(
        get_current_user
    ),
):

    async with get_session() as session:

        listing = (
            await ShopRepository.get_active_listing(
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
    "/{listing_id}/favorite",
)
async def remove_favorite(
    listing_id: int,
    user: User = __import__(
        "fastapi"
    ).Depends(
        get_current_user
    ),
):

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


# =========================================================
# ADD TO CART
# =========================================================

@router.post(
    "/{listing_id}/cart",
)
async def add_to_cart(
    listing_id: int,
    user: User = __import__(
        "fastapi"
    ).Depends(
        get_current_user
    ),
):

    async with get_session() as session:

        listing = (
            await ShopRepository.get_active_listing(
                session,
                listing_id,
            )
        )

        if listing is None:
            raise HTTPException(
                status_code=404,
                detail="Listing not found",
            )

        if listing.seller_id == user.id:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Нельзя добавить "
                    "своё объявление."
                ),
            )

        added = (
            await ShopRepository.add_to_cart(
                session,
                user_id=user.id,
                listing_id=listing_id,
            )
        )

        await session.commit()

        return {
            "success": True,
            "added": added,
        }


# =========================================================
# REMOVE FROM CART
# =========================================================

@router.delete(
    "/{listing_id}/cart",
)
async def remove_from_cart(
    listing_id: int,
    user: User = __import__(
        "fastapi"
    ).Depends(
        get_current_user
    ),
):

    async with get_session() as session:

        removed = (
            await ShopRepository.remove_from_cart(
                session,
                user_id=user.id,
                listing_id=listing_id,
            )
        )

        await session.commit()

        return {
            "success": True,
            "removed": removed,
        }


# =========================================================
# GET CART
# =========================================================

@router.get(
    "/cart/current",
    response_model=CartResponse,
)
async def get_cart(
    user: User = __import__(
        "fastapi"
    ).Depends(
        get_current_user
    ),
):

    async with get_session() as session:

        result = await session.execute(
            select(
                ShopCartItem
            ).where(
                ShopCartItem.user_id
                == user.id
            )
        )

        cart_items = list(
            result.scalars().all()
        )

        items = []

        total_rub = 0
        total_stars = 0

        for cart_item in cart_items:

            listing = (
                await ShopRepository.get_active_listing(
                    session,
                    cart_item.listing_id,
                )
            )

            # Если объявление удалили,
            # автоматически убираем его
            # из корзины.

            if listing is None:

                await session.delete(
                    cart_item
                )

                continue

            items.append(
                CartItemResponse(
                    listing_id=listing.id,
                    username=listing.username,
                    title=listing.title,
                    price_rub=listing.price_rub,
                    price_stars=listing.price_stars,
                )
            )

            total_rub += (
                listing.price_rub
            )

            if listing.price_stars:
                total_stars += (
                    listing.price_stars
                )

        await session.commit()

        return CartResponse(
            items=items,
            total_rub=total_rub,
            total_stars=total_stars,
        )


# =========================================================
# CLEAR CART
# =========================================================

@router.delete(
    "/cart/current",
)
async def clear_cart(
    user: User = __import__(
        "fastapi"
    ).Depends(
        get_current_user
    ),
):

    async with get_session() as session:

        await ShopRepository.clear_cart(
            session,
            user.id,
        )

        await session.commit()

        return {
            "success": True
        }
