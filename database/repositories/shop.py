from __future__ import annotations

from typing import Optional

from sqlalchemy import (
    delete,
    func,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    CartItem,
    ShopCategory,
    ShopFavorite,
    ShopListing,
    ShopPurchase,
    ShopReview,
    SellerProfile,
)


class ShopRepository:
    """
    Репозиторий TEYZUS SHOP.

    Здесь находится только работа с БД.
    Бизнес-логика находится в services/shop.
    """

    # =====================================================
    # CATEGORIES
    # =====================================================

    @staticmethod
    async def get_categories(
        session: AsyncSession,
    ) -> list[ShopCategory]:
        result = await session.execute(
            select(ShopCategory)
            .where(
                ShopCategory.is_active.is_(True)
            )
            .order_by(
                ShopCategory.sort_order.asc(),
                ShopCategory.id.asc(),
            )
        )

        return list(result.scalars().all())

    @staticmethod
    async def get_category(
        session: AsyncSession,
        category_id: int,
    ) -> Optional[ShopCategory]:
        result = await session.execute(
            select(ShopCategory)
            .where(
                ShopCategory.id == category_id
            )
        )

        return result.scalar_one_or_none()

    # =====================================================
    # LISTINGS
    # =====================================================

    @staticmethod
    async def get_listing(
        session: AsyncSession,
        listing_id: int,
    ) -> Optional[ShopListing]:
        result = await session.execute(
            select(ShopListing)
            .where(
                ShopListing.id == listing_id
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def get_listing_by_username(
        session: AsyncSession,
        username: str,
    ) -> Optional[ShopListing]:
        normalized = username.lower().lstrip("@")

        result = await session.execute(
            select(ShopListing)
            .where(
                ShopListing.normalized_username
                == normalized
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def get_listings(
        session: AsyncSession,
        *,
        search: str = "",
        category: str = "all",
        sort: str = "new",
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[ShopListing], int]:

        page = max(page, 1)

        per_page = min(
            max(per_page, 1),
            100,
        )

        query = (
            select(ShopListing)
            .where(
                ShopListing.is_active.is_(True),
                ShopListing.status == "approved",
            )
        )

        count_query = (
            select(
                func.count(
                    ShopListing.id
                )
            )
            .where(
                ShopListing.is_active.is_(True),
                ShopListing.status == "approved",
            )
        )

        # -------------------------------------------------
        # SEARCH
        # -------------------------------------------------

        if search:
            clean_search = (
                search
                .strip()
                .lstrip("@")
                .lower()
            )

            pattern = f"%{clean_search}%"

            query = query.where(
                ShopListing.normalized_username.ilike(
                    pattern
                )
            )

            count_query = count_query.where(
                ShopListing.normalized_username.ilike(
                    pattern
                )
            )

        # -------------------------------------------------
        # CATEGORY
        # -------------------------------------------------

        if category == "premium":
            query = query.where(
                ShopListing.is_premium.is_(True)
            )

            count_query = count_query.where(
                ShopListing.is_premium.is_(True)
            )

        # -------------------------------------------------
        # SORT
        # -------------------------------------------------

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
                ShopListing.created_at.desc(),
            )

        else:
            query = query.order_by(
                ShopListing.created_at.desc()
            )

        # -------------------------------------------------
        # PAGINATION
        # -------------------------------------------------

        offset = (
            page - 1
        ) * per_page

        query = query.offset(
            offset
        ).limit(
            per_page
        )

        result = await session.execute(
            query
        )

        count_result = await session.execute(
            count_query
        )

        total = (
            count_result.scalar()
            or 0
        )

        return (
            list(result.scalars().all()),
            total,
        )

    # =====================================================
    # FAVORITES
    # =====================================================

    @staticmethod
    async def is_favorite(
        session: AsyncSession,
        user_id: int,
        listing_id: int,
    ) -> bool:
        result = await session.execute(
            select(ShopFavorite.id)
            .where(
                ShopFavorite.user_id
                == user_id,
                ShopFavorite.listing_id
                == listing_id,
            )
            .limit(1)
        )

        return result.scalar_one_or_none() is not None

    @staticmethod
    async def add_favorite(
        session: AsyncSession,
        user_id: int,
        listing_id: int,
    ) -> bool:

        existing = await ShopRepository.is_favorite(
            session,
            user_id,
            listing_id,
        )

        if existing:
            return False

        favorite = ShopFavorite(
            user_id=user_id,
            listing_id=listing_id,
        )

        session.add(
            favorite
        )

        await session.flush()

        return True

    @staticmethod
    async def remove_favorite(
        session: AsyncSession,
        user_id: int,
        listing_id: int,
    ) -> bool:

        result = await session.execute(
            delete(ShopFavorite)
            .where(
                ShopFavorite.user_id
                == user_id,
                ShopFavorite.listing_id
                == listing_id,
            )
        )

        return result.rowcount > 0

    @staticmethod
    async def get_favorite_listings(
        session: AsyncSession,
        user_id: int,
    ) -> list[ShopListing]:

        result = await session.execute(
            select(ShopListing)
            .join(
                ShopFavorite,
                ShopFavorite.listing_id
                == ShopListing.id,
            )
            .where(
                ShopFavorite.user_id
                == user_id
            )
            .order_by(
                ShopFavorite.created_at.desc()
            )
        )

        return list(
            result.scalars().all()
        )

    # =====================================================
    # CART
    # =====================================================

    @staticmethod
    async def get_cart(
        session: AsyncSession,
        user_id: int,
    ) -> list[ShopListing]:

        result = await session.execute(
            select(ShopListing)
            .join(
                CartItem,
                CartItem.listing_id
                == ShopListing.id,
            )
            .where(
                CartItem.user_id
                == user_id
            )
            .order_by(
                CartItem.added_at.desc()
            )
        )

        return list(
            result.scalars().all()
        )

    @staticmethod
    async def add_to_cart(
        session: AsyncSession,
        user_id: int,
        listing_id: int,
    ) -> bool:

        result = await session.execute(
            select(CartItem.id)
            .where(
                CartItem.user_id
                == user_id,
                CartItem.listing_id
                == listing_id,
            )
            .limit(1)
        )

        if result.scalar_one_or_none():
            return False

        item = CartItem(
            user_id=user_id,
            listing_id=listing_id,
        )

        session.add(
            item
        )

        return True

    @staticmethod
    async def remove_from_cart(
        session: AsyncSession,
        user_id: int,
        listing_id: int,
    ) -> bool:

        result = await session.execute(
            delete(CartItem)
            .where(
                CartItem.user_id
                == user_id,
                CartItem.listing_id
                == listing_id,
            )
        )

        return result.rowcount > 0

    @staticmethod
    async def clear_cart(
        session: AsyncSession,
        user_id: int,
    ) -> None:

        await session.execute(
            delete(CartItem)
            .where(
                CartItem.user_id
                == user_id
            )
        )

    # =====================================================
    # SELLER
    # =====================================================

    @staticmethod
    async def get_seller_profile(
        session: AsyncSession,
        user_id: int,
    ) -> Optional[SellerProfile]:

        result = await session.execute(
            select(SellerProfile)
            .where(
                SellerProfile.user_id
                == user_id
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def create_seller_profile(
        session: AsyncSession,
        user_id: int,
    ) -> SellerProfile:

        profile = SellerProfile(
            user_id=user_id
        )

        session.add(
            profile
        )

        await session.flush()

        return profile

    # =====================================================
    # PURCHASES
    # =====================================================

    @staticmethod
    async def get_user_purchases(
        session: AsyncSession,
        user_id: int,
    ) -> list[ShopPurchase]:

        result = await session.execute(
            select(ShopPurchase)
            .where(
                ShopPurchase.buyer_id
                == user_id
            )
            .order_by(
                ShopPurchase.created_at.desc()
            )
        )

        return list(
            result.scalars().all()
        )

    @staticmethod
    async def get_seller_purchases(
        session: AsyncSession,
        user_id: int,
    ) -> list[ShopPurchase]:

        result = await session.execute(
            select(ShopPurchase)
            .where(
                ShopPurchase.seller_id
                == user_id
            )
            .order_by(
                ShopPurchase.created_at.desc()
            )
        )

        return list(
            result.scalars().all()
        )

    # =====================================================
    # REVIEWS
    # =====================================================

    @staticmethod
    async def get_seller_reviews(
        session: AsyncSession,
        seller_id: int,
    ) -> list[ShopReview]:

        result = await session.execute(
            select(ShopReview)
            .where(
                ShopReview.seller_id
                == seller_id
            )
            .order_by(
                ShopReview.created_at.desc()
            )
        )

        return list(
            result.scalars().all()
        )
