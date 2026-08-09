from __future__ import annotations

from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    ShopFavorite,
    ShopListing,
)


class ShopRepository:
    """
    Репозиторий TEYZUS SHOP.

    Здесь находится работа с:
    - объявлениями;
    - поиском;
    - категориями;
    - сортировкой;
    - избранным.
    """

    # =====================================================
    # LISTINGS
    # =====================================================

    @staticmethod
    async def get_listings(
        session: AsyncSession,
        *,
        search: str = "",
        category: str = "all",
        sort: str = "new",
        page: int = 1,
        per_page: int = 20,
        user_id: Optional[int] = None,
    ) -> tuple[list[ShopListing], int]:

        page = max(page, 1)
        per_page = min(max(per_page, 1), 100)

        query = select(ShopListing).where(
            ShopListing.is_active.is_(True),
            ShopListing.is_moderated.is_(True),
        )

        # -------------------------------------------------
        # SEARCH
        # -------------------------------------------------

        search = search.strip().lstrip("@")

        if search:
            pattern = f"%{search}%"

            query = query.where(
                or_(
                    ShopListing.username.ilike(
                        pattern
                    ),
                    ShopListing.title.ilike(
                        pattern
                    ),
                    ShopListing.description.ilike(
                        pattern
                    ),
                )
            )

        # -------------------------------------------------
        # CATEGORY
        # -------------------------------------------------

        if category == "premium":
            query = query.where(
                ShopListing.is_premium.is_(True)
            )

        # -------------------------------------------------
        # SORT
        # -------------------------------------------------

        if category == "cheap":
            query = query.order_by(
                ShopListing.price_rub.asc()
            )

        elif category == "popular" or sort == "popular":
            query = query.order_by(
                ShopListing.views.desc(),
                ShopListing.created_at.desc(),
            )

        elif sort == "price_asc":
            query = query.order_by(
                ShopListing.price_rub.asc()
            )

        elif sort == "price_desc":
            query = query.order_by(
                ShopListing.price_rub.desc()
            )

        else:
            query = query.order_by(
                ShopListing.created_at.desc()
            )

        # -------------------------------------------------
        # COUNT
        # -------------------------------------------------

        count_query = select(
            func.count()
        ).select_from(
            query.subquery()
        )

        count_result = await session.execute(
            count_query
        )

        total = count_result.scalar_one()

        # -------------------------------------------------
        # PAGINATION
        # -------------------------------------------------

        offset = (
            (page - 1) * per_page
        )

        query = query.offset(
            offset
        ).limit(
            per_page
        )

        result = await session.execute(
            query
        )

        listings = list(
            result.scalars().all()
        )

        return listings, total

    # =====================================================
    # SINGLE LISTING
    # =====================================================

    @staticmethod
    async def get_listing(
        session: AsyncSession,
        listing_id: int,
    ) -> Optional[ShopListing]:

        result = await session.execute(
            select(ShopListing).where(
                ShopListing.id == listing_id,
                ShopListing.is_active.is_(True),
            )
        )

        return result.scalar_one_or_none()

    # =====================================================
    # CREATE
    # =====================================================

    @staticmethod
    async def create_listing(
        session: AsyncSession,
        *,
        seller_id: int,
        username: str,
        title: str,
        description: Optional[str],
        price_rub: int,
        price_stars: Optional[int],
        category: Optional[str],
        is_premium: bool = False,
    ) -> ShopListing:

        listing = ShopListing(
            seller_id=seller_id,
            username=username.lstrip("@"),
            title=title,
            description=description,
            price_rub=price_rub,
            price_stars=price_stars,
            category=category,
            is_premium=is_premium,
            is_active=False,
            is_moderated=False,
            views=0,
        )

        session.add(listing)

        await session.flush()

        return listing

    # =====================================================
    # INCREMENT VIEWS
    # =====================================================

    @staticmethod
    async def increment_views(
        session: AsyncSession,
        listing_id: int,
    ) -> None:

        listing = await ShopRepository.get_listing(
            session,
            listing_id,
        )

        if listing is None:
            return

        listing.views += 1

        await session.flush()

    # =====================================================
    # FAVORITES
    # =====================================================

    @staticmethod
    async def is_favorite(
        session: AsyncSession,
        *,
        user_id: int,
        listing_id: int,
    ) -> bool:

        result = await session.execute(
            select(ShopFavorite.id).where(
                ShopFavorite.user_id == user_id,
                ShopFavorite.listing_id == listing_id,
            )
        )

        return result.scalar_one_or_none() is not None

    @staticmethod
    async def add_favorite(
        session: AsyncSession,
        *,
        user_id: int,
        listing_id: int,
    ) -> bool:

        exists = await ShopRepository.is_favorite(
            session,
            user_id=user_id,
            listing_id=listing_id,
        )

        if exists:
            return False

        favorite = ShopFavorite(
            user_id=user_id,
            listing_id=listing_id,
        )

        session.add(favorite)

        await session.flush()

        return True

    @staticmethod
    async def remove_favorite(
        session: AsyncSession,
        *,
        user_id: int,
        listing_id: int,
    ) -> bool:

        result = await session.execute(
            select(ShopFavorite).where(
                ShopFavorite.user_id == user_id,
                ShopFavorite.listing_id == listing_id,
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

        await session.flush()

        return True
