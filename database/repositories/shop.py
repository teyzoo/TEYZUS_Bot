from __future__ import annotations

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    CartItem,
    ShopCategory,
    ShopFavorite,
    ShopListing,
    SellerProfile,
)
from database.repositories.base import BaseRepository


class ShopRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    # =====================================================
    # LISTINGS
    # =====================================================

    async def get_listing(
        self,
        listing_id: int,
    ) -> ShopListing | None:

        result = await self.session.execute(
            select(ShopListing).where(
                ShopListing.id == listing_id
            )
        )

        return result.scalar_one_or_none()

    async def get_listing_by_username(
        self,
        username: str,
    ) -> ShopListing | None:

        username = username.strip().lstrip("@").lower()

        result = await self.session.execute(
            select(ShopListing).where(
                func.lower(
                    ShopListing.username
                ) == username
            )
        )

        return result.scalar_one_or_none()

    async def create_listing(
        self,
        **kwargs,
    ) -> ShopListing:

        listing = ShopListing(
            **kwargs
        )

        self.session.add(listing)

        await self.session.flush()

        return listing

    async def update_listing(
        self,
        listing: ShopListing,
        **kwargs,
    ) -> ShopListing:

        for key, value in kwargs.items():

            if hasattr(listing, key):
                setattr(
                    listing,
                    key,
                    value,
                )

        await self.session.flush()

        return listing

    async def delete_listing(
        self,
        listing: ShopListing,
    ) -> None:

        await self.session.delete(
            listing
        )

        await self.session.flush()

    async def list_listings(
        self,
        *,
        search: str | None = None,
        category_id: int | None = None,
        status: str = "approved",
        premium: bool | None = None,
        sort: str = "new",
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[ShopListing], int]:

        conditions = [
            ShopListing.status == status
        ]

        if search:
            search_value = (
                search
                .strip()
                .lstrip("@")
            )

            conditions.append(
                ShopListing.username.ilike(
                    f"%{search_value}%"
                )
            )

        if category_id is not None:
            conditions.append(
                ShopListing.category_id
                == category_id
            )

        if premium is not None:
            conditions.append(
                ShopListing.is_premium
                == premium
            )

        count_query = (
            select(
                func.count(
                    ShopListing.id
                )
            )
            .where(*conditions)
        )

        count_result = (
            await self.session.execute(
                count_query
            )
        )

        total = (
            count_result.scalar_one()
        )

        query = select(
            ShopListing
        ).where(*conditions)

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
                ShopListing.views_count.desc(),
                ShopListing.favorites_count.desc(),
            )

        else:

            query = query.order_by(
                ShopListing.created_at.desc()
            )

        offset = (
            max(page, 1) - 1
        ) * per_page

        query = query.offset(
            offset
        ).limit(
            per_page
        )

        result = await self.session.execute(
            query
        )

        return (
            list(
                result.scalars().all()
            ),
            total,
        )

    # =====================================================
    # FAVORITES
    # =====================================================

    async def is_favorite(
        self,
        user_id: int,
        listing_id: int,
    ) -> bool:

        result = await self.session.execute(
            select(ShopFavorite.id)
            .where(
                ShopFavorite.user_id
                == user_id,
                ShopFavorite.listing_id
                == listing_id,
            )
        )

        return result.scalar_one_or_none() is not None

    async def add_favorite(
        self,
        user_id: int,
        listing_id: int,
    ) -> ShopFavorite:

        existing = await self.session.execute(
            select(ShopFavorite)
            .where(
                ShopFavorite.user_id
                == user_id,
                ShopFavorite.listing_id
                == listing_id,
            )
        )

        favorite = (
            existing.scalar_one_or_none()
        )

        if favorite:
            return favorite

        favorite = ShopFavorite(
            user_id=user_id,
            listing_id=listing_id,
        )

        self.session.add(
            favorite
        )

        listing = await self.get_listing(
            listing_id
        )

        if listing:
            listing.favorites_count += 1

        await self.session.flush()

        return favorite

    async def remove_favorite(
        self,
        user_id: int,
        listing_id: int,
    ) -> None:

        result = await self.session.execute(
            select(ShopFavorite)
            .where(
                ShopFavorite.user_id
                == user_id,
                ShopFavorite.listing_id
                == listing_id,
            )
        )

        favorite = (
            result.scalar_one_or_none()
        )

        if favorite:

            await self.session.delete(
                favorite
            )

            listing = await self.get_listing(
                listing_id
            )

            if listing:
                listing.favorites_count = max(
                    0,
                    listing.favorites_count - 1,
                )

            await self.session.flush()

    # =====================================================
    # CART
    # =====================================================

    async def get_cart(
        self,
        user_id: int,
    ) -> list[CartItem]:

        result = await self.session.execute(
            select(CartItem)
            .where(
                CartItem.user_id
                == user_id
            )
            .order_by(
                CartItem.created_at.desc()
            )
        )

        return list(
            result.scalars().all()
        )

    async def add_to_cart(
        self,
        user_id: int,
        listing_id: int,
    ) -> CartItem:

        result = await self.session.execute(
            select(CartItem)
            .where(
                CartItem.user_id
                == user_id,
                CartItem.listing_id
                == listing_id,
            )
        )

        existing = (
            result.scalar_one_or_none()
        )

        if existing:
            return existing

        item = CartItem(
            user_id=user_id,
            listing_id=listing_id,
        )

        self.session.add(item)

        await self.session.flush()

        return item

    async def remove_from_cart(
        self,
        user_id: int,
        listing_id: int,
    ) -> None:

        await self.session.execute(
            delete(CartItem)
            .where(
                CartItem.user_id
                == user_id,
                CartItem.listing_id
                == listing_id,
            )
        )

        await self.session.flush()

    async def clear_cart(
        self,
        user_id: int,
    ) -> None:

        await self.session.execute(
            delete(CartItem)
            .where(
                CartItem.user_id
                == user_id
            )
        )

        await self.session.flush()

    # =====================================================
    # CATEGORIES
    # =====================================================

    async def get_categories(
        self,
    ) -> list[ShopCategory]:

        result = await self.session.execute(
            select(ShopCategory)
            .where(
                ShopCategory.enabled
                == True
            )
            .order_by(
                ShopCategory.sort_order.asc(),
                ShopCategory.id.asc(),
            )
        )

        return list(
            result.scalars().all()
        )

    async def create_category(
        self,
        **kwargs,
    ) -> ShopCategory:

        category = ShopCategory(
            **kwargs
        )

        self.session.add(
            category
        )

        await self.session.flush()

        return category

    # =====================================================
    # SELLER
    # =====================================================

    async def get_seller_profile(
        self,
        user_id: int,
    ) -> SellerProfile | None:

        result = await self.session.execute(
            select(SellerProfile)
            .where(
                SellerProfile.user_id
                == user_id
            )
        )

        return result.scalar_one_or_none()

    async def create_seller_profile(
        self,
        user_id: int,
        **kwargs,
    ) -> SellerProfile:

        profile = SellerProfile(
            user_id=user_id,
            **kwargs,
        )

        self.session.add(
            profile
        )

        await self.session.flush()

        return profile
