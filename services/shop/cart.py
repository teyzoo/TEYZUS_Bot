from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.shop import ShopRepository


class CartService:

    @staticmethod
    async def get_cart(
        session: AsyncSession,
        user_id: int,
    ) -> dict:

        listings = (
            await ShopRepository.get_cart(
                session,
                user_id,
            )
        )

        items = []

        total_rub = 0
        total_stars = 0

        has_stars_prices = True

        for listing in listings:

            total_rub += listing.price_rub

            if listing.price_stars is not None:
                total_stars += listing.price_stars
            else:
                has_stars_prices = False

            items.append(
                {
                    "id": listing.id,
                    "username": listing.username,
                    "price_rub": listing.price_rub,
                    "price_stars": listing.price_stars,
                    "description": listing.description,
                    "is_premium": listing.is_premium,
                    "is_verified": listing.is_verified,
                }
            )

        return {
            "items": items,
            "count": len(items),
            "total_rub": total_rub,
            "total_stars": (
                total_stars
                if has_stars_prices
                else None
            ),
        }

    @staticmethod
    async def add(
        session: AsyncSession,
        user_id: int,
        listing_id: int,
    ) -> bool:

        listing = (
            await ShopRepository.get_listing(
                session,
                listing_id,
            )
        )

        if listing is None:
            raise ValueError(
                "Listing not found"
            )

        if listing.status != "approved":
            raise ValueError(
                "Listing is not available"
            )

        if not listing.is_active:
            raise ValueError(
                "Listing is inactive"
            )

        if listing.seller_id == user_id:
            raise ValueError(
                "You cannot add your own listing"
            )

        return await ShopRepository.add_to_cart(
            session,
            user_id,
            listing_id,
        )

    @staticmethod
    async def remove(
        session: AsyncSession,
        user_id: int,
        listing_id: int,
    ) -> bool:

        return await ShopRepository.remove_from_cart(
            session,
            user_id,
            listing_id,
        )

    @staticmethod
    async def clear(
        session: AsyncSession,
        user_id: int,
    ) -> None:

        await ShopRepository.clear_cart(
            session,
            user_id,
        )
