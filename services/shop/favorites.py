from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.shop import ShopRepository


class FavoriteService:

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

        if not listing.is_active:
            raise ValueError(
                "Listing is inactive"
            )

        added = (
            await ShopRepository.add_favorite(
                session,
                user_id,
                listing_id,
            )
        )

        if added:
            listing.favorites_count += 1

        await session.flush()

        return added

    @staticmethod
    async def remove(
        session: AsyncSession,
        user_id: int,
        listing_id: int,
    ) -> bool:

        removed = (
            await ShopRepository.remove_favorite(
                session,
                user_id,
                listing_id,
            )
        )

        if removed:
            listing = (
                await ShopRepository.get_listing(
                    session,
                    listing_id,
                )
            )

            if listing is not None:
                listing.favorites_count = max(
                    0,
                    listing.favorites_count - 1,
                )

        await session.flush()

        return removed

    @staticmethod
    async def list_user_favorites(
        session: AsyncSession,
        user_id: int,
    ) -> list[dict]:

        listings = (
            await ShopRepository.get_favorite_listings(
                session,
                user_id,
            )
        )

        return [
            {
                "id": item.id,
                "username": item.username,
                "price_rub": item.price_rub,
                "price_stars": item.price_stars,
                "description": item.description,
                "is_premium": item.is_premium,
                "is_verified": item.is_verified,
                "created_at": (
                    item.created_at.isoformat()
                ),
            }
            for item in listings
        ]
