from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import ShopListing
from database.repositories.shop import ShopRepository


class ShopService:
    """
    Основная бизнес-логика TEYZUS SHOP.
    """

    # =====================================================
    # LISTINGS
    # =====================================================

    @staticmethod
    async def get_listings(
        session: AsyncSession,
        *,
        user_id: Optional[int] = None,
        search: str = "",
        category: str = "all",
        sort: str = "new",
        page: int = 1,
        per_page: int = 20,
    ) -> dict:

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

            is_favorite = False

            if user_id is not None:
                is_favorite = (
                    await ShopRepository.is_favorite(
                        session,
                        user_id,
                        listing.id,
                    )
                )

            items.append(
                {
                    "id": listing.id,
                    "username": listing.username,
                    "price_rub": listing.price_rub,
                    "price_stars": listing.price_stars,
                    "seller_id": listing.seller_id,
                    "description": listing.description,
                    "title": listing.title,
                    "category_id": listing.category_id,
                    "is_premium": listing.is_premium,
                    "is_verified": listing.is_verified,
                    "is_favorite": is_favorite,
                    "views_count": listing.views_count,
                    "favorites_count": listing.favorites_count,
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

    # =====================================================
    # SINGLE LISTING
    # =====================================================

    @staticmethod
    async def get_listing(
        session: AsyncSession,
        listing_id: int,
        user_id: Optional[int] = None,
    ) -> Optional[dict]:

        listing = (
            await ShopRepository.get_listing(
                session,
                listing_id,
            )
        )

        if listing is None:
            return None

        listing.views_count += 1

        is_favorite = False

        if user_id is not None:
            is_favorite = (
                await ShopRepository.is_favorite(
                    session,
                    user_id,
                    listing.id,
                )
            )

        await session.flush()

        return {
            "id": listing.id,
            "username": listing.username,
            "title": listing.title,
            "description": listing.description,
            "price_rub": listing.price_rub,
            "price_stars": listing.price_stars,
            "seller_id": listing.seller_id,
            "category_id": listing.category_id,
            "is_premium": listing.is_premium,
            "is_verified": listing.is_verified,
            "is_favorite": is_favorite,
            "views_count": listing.views_count,
            "favorites_count": listing.favorites_count,
            "created_at": listing.created_at.isoformat(),
        }

    # =====================================================
    # CREATE LISTING
    # =====================================================

    @staticmethod
    async def create_listing(
        session: AsyncSession,
        *,
        seller_id: int,
        username: str,
        price_rub: int,
        price_stars: Optional[int] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        category_id: Optional[int] = None,
        is_premium: bool = False,
    ) -> ShopListing:

        username = (
            username
            .strip()
            .lstrip("@")
        )

        normalized = username.lower()

        if not normalized:
            raise ValueError(
                "Username is required"
            )

        if price_rub < 0:
            raise ValueError(
                "Invalid RUB price"
            )

        existing = (
            await ShopRepository.get_listing_by_username(
                session,
                normalized,
            )
        )

        if existing is not None:
            raise ValueError(
                "This username is already listed"
            )

        listing = ShopListing(
            username=username,
            normalized_username=normalized,
            seller_id=seller_id,
            category_id=category_id,
            title=title,
            description=description,
            price_rub=price_rub,
            price_stars=price_stars,
            is_premium=is_premium,
            status="pending",
            is_active=True,
        )

        session.add(
            listing
        )

        await session.flush()

        return listing
