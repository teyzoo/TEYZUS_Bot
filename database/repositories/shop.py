from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    SellerProfile,
    ShopCartItem,
    ShopFavorite,
    ShopListing,
    ShopPurchase,
    ShopReview,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# =========================================================
# SELLER PROFILE
# =========================================================

async def get_seller_profile(
    session: AsyncSession,
    user_id: int,
) -> Optional[SellerProfile]:

    result = await session.execute(
        select(SellerProfile).where(
            SellerProfile.user_id == user_id
        )
    )

    return result.scalar_one_or_none()


async def create_seller_profile(
    session: AsyncSession,
    user_id: int,
    telegram_id: int,
    display_name: Optional[str] = None,
) -> SellerProfile:

    profile = SellerProfile(
        user_id=user_id,
        telegram_id=telegram_id,
        display_name=display_name,
    )

    session.add(profile)

    await session.flush()

    return profile


# =========================================================
# LISTINGS
# =========================================================

async def create_listing(
    session: AsyncSession,
    seller_id: int,
    seller_telegram_id: int,
    username: str,
    price_rub: int,
    price_stars: Optional[int] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    category: Optional[str] = None,
) -> ShopListing:

    listing = ShopListing(
        seller_id=seller_id,
        seller_telegram_id=seller_telegram_id,
        username=username.lower().lstrip("@"),
        title=title,
        description=description,
        category=category,
        price_rub=price_rub,
        price_stars=price_stars,
        status="pending",
    )

    session.add(listing)

    await session.flush()

    return listing


async def get_listing(
    session: AsyncSession,
    listing_id: int,
) -> Optional[ShopListing]:

    result = await session.execute(
        select(ShopListing).where(
            ShopListing.id == listing_id
        )
    )

    return result.scalar_one_or_none()


async def get_listing_by_username(
    session: AsyncSession,
    username: str,
) -> Optional[ShopListing]:

    username = username.lower().lstrip("@")

    result = await session.execute(
        select(ShopListing).where(
            ShopListing.username == username,
            ShopListing.status.in_(
                [
                    "pending",
                    "approved",
                    "reserved",
                ]
            ),
        )
    )

    return result.scalar_one_or_none()


async def get_user_listings(
    session: AsyncSession,
    seller_id: int,
) -> list[ShopListing]:

    result = await session.execute(
        select(ShopListing)
        .where(
            ShopListing.seller_id == seller_id
        )
        .order_by(
            ShopListing.created_at.desc()
        )
    )

    return list(result.scalars().all())


async def get_public_listings(
    session: AsyncSession,
    search: str = "",
    category: str = "all",
    sort: str = "new",
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[ShopListing], int]:

    query = select(ShopListing).where(
        ShopListing.status == "approved"
    )

    count_query = select(
        func.count(ShopListing.id)
    ).where(
        ShopListing.status == "approved"
    )

    if search:
        search_value = (
            search.lower()
            .lstrip("@")
        )

        query = query.where(
            ShopListing.username.ilike(
                f"%{search_value}%"
            )
        )

        count_query = count_query.where(
            ShopListing.username.ilike(
                f"%{search_value}%"
            )
        )

    if category == "premium":

        query = query.where(
            ShopListing.is_premium.is_(True)
        )

        count_query = count_query.where(
            ShopListing.is_premium.is_(True)
        )

    elif category == "popular":

        query = query.order_by(
            ShopListing.views_count.desc(),
            ShopListing.favorites_count.desc(),
        )

    elif category == "cheap":

        query = query.order_by(
            ShopListing.price_rub.asc()
        )

    elif category == "new":

        query = query.order_by(
            ShopListing.created_at.desc()
        )

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
            ShopListing.views_count.desc()
        )

    elif sort == "new":

        query = query.order_by(
            ShopListing.created_at.desc()
        )

    offset = max(
        page - 1,
        0
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

    total = count_result.scalar_one()

    return (
        list(result.scalars().all()),
        total,
    )


# =========================================================
# MODERATION
# =========================================================

async def approve_listing(
    session: AsyncSession,
    listing_id: int,
) -> Optional[ShopListing]:

    listing = await get_listing(
        session,
        listing_id,
    )

    if listing is None:
        return None

    listing.status = "approved"
    listing.published_at = utc_now()
    listing.rejection_reason = None

    await session.flush()

    return listing


async def reject_listing(
    session: AsyncSession,
    listing_id: int,
    reason: Optional[str] = None,
) -> Optional[ShopListing]:

    listing = await get_listing(
        session,
        listing_id,
    )

    if listing is None:
        return None

    listing.status = "rejected"
    listing.rejection_reason = reason

    await session.flush()

    return listing


# =========================================================
# FAVORITES
# =========================================================

async def is_favorite(
    session: AsyncSession,
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


async def add_favorite(
    session: AsyncSession,
    user_id: int,
    listing_id: int,
) -> bool:

    exists = await is_favorite(
        session,
        user_id,
        listing_id,
    )

    if exists:
        return False

    favorite = ShopFavorite(
        user_id=user_id,
        listing_id=listing_id,
    )

    session.add(favorite)

    listing = await get_listing(
        session,
        listing_id,
    )

    if listing:
        listing.favorites_count += 1

    await session.flush()

    return True


async def remove_favorite(
    session: AsyncSession,
    user_id: int,
    listing_id: int,
) -> bool:

    result = await session.execute(
        select(ShopFavorite).where(
            ShopFavorite.user_id == user_id,
            ShopFavorite.listing_id == listing_id,
        )
    )

    favorite = result.scalar_one_or_none()

    if favorite is None:
        return False

    await session.delete(
        favorite
    )

    listing = await get_listing(
        session,
        listing_id,
    )

    if listing and listing.favorites_count > 0:
        listing.favorites_count -= 1

    await session.flush()

    return True


async def get_user_favorites(
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
            ShopFavorite.user_id == user_id
        )
        .order_by(
            ShopFavorite.created_at.desc()
        )
    )

    return list(
        result.scalars().all()
    )


# =========================================================
# CART
# =========================================================

async def add_to_cart(
    session: AsyncSession,
    user_id: int,
    listing_id: int,
) -> bool:

    result = await session.execute(
        select(ShopCartItem).where(
            ShopCartItem.user_id == user_id,
            ShopCartItem.listing_id == listing_id,
        )
    )

    exists = result.scalar_one_or_none()

    if exists:
        return False

    item = ShopCartItem(
        user_id=user_id,
        listing_id=listing_id,
    )

    session.add(item)

    await session.flush()

    return True


async def remove_from_cart(
    session: AsyncSession,
    user_id: int,
    listing_id: int,
) -> bool:

    result = await session.execute(
        select(ShopCartItem).where(
            ShopCartItem.user_id == user_id,
            ShopCartItem.listing_id == listing_id,
        )
    )

    item = result.scalar_one_or_none()

    if item is None:
        return False

    await session.delete(item)

    await session.flush()

    return True


async def get_cart(
    session: AsyncSession,
    user_id: int,
) -> list[ShopListing]:

    result = await session.execute(
        select(ShopListing)
        .join(
            ShopCartItem,
            ShopCartItem.listing_id
            == ShopListing.id,
        )
        .where(
            ShopCartItem.user_id == user_id
        )
        .order_by(
            ShopCartItem.added_at.desc()
        )
    )

    return list(
        result.scalars().all()
    )


async def clear_cart(
    session: AsyncSession,
    user_id: int,
) -> None:

    await session.execute(
        delete(ShopCartItem).where(
            ShopCartItem.user_id == user_id
        )
    )

    await session.flush()


# =========================================================
# PURCHASES
# =========================================================

async def create_purchase(
    session: AsyncSession,
    buyer_id: int,
    buyer_telegram_id: int,
    listing: ShopListing,
    payment_method: str,
) -> ShopPurchase:

    purchase = ShopPurchase(
        buyer_id=buyer_id,
        buyer_telegram_id=buyer_telegram_id,
        seller_id=listing.seller_id,
        seller_telegram_id=listing.seller_telegram_id,
        listing_id=listing.id,
        username=listing.username,
        price_rub=listing.price_rub,
        price_stars=listing.price_stars,
        currency=(
            "STARS"
            if payment_method == "stars"
            else "RUB"
        ),
        payment_method=payment_method,
        status="pending",
    )

    session.add(purchase)

    listing.status = "reserved"

    await session.flush()

    return purchase


async def get_user_purchases(
    session: AsyncSession,
    user_id: int,
) -> list[ShopPurchase]:

    result = await session.execute(
        select(ShopPurchase)
        .where(
            ShopPurchase.buyer_id == user_id
        )
        .order_by(
            ShopPurchase.created_at.desc()
        )
    )

    return list(
        result.scalars().all()
    )


async def get_user_sales(
    session: AsyncSession,
    user_id: int,
) -> list[ShopPurchase]:

    result = await session.execute(
        select(ShopPurchase)
        .where(
            ShopPurchase.seller_id == user_id
        )
        .order_by(
            ShopPurchase.created_at.desc()
        )
    )

    return list(
        result.scalars().all()
    )


# =========================================================
# REVIEWS
# =========================================================

async def create_review(
    session: AsyncSession,
    purchase_id: int,
    buyer_id: int,
    seller_id: int,
    rating: int,
    text: Optional[str] = None,
) -> ShopReview:

    rating = max(
        1,
        min(5, rating)
    )

    review = ShopReview(
        purchase_id=purchase_id,
        buyer_id=buyer_id,
        seller_id=seller_id,
        rating=rating,
        text=text,
    )

    session.add(review)

    profile = await get_seller_profile(
        session,
        seller_id,
    )

    if profile:

        profile.total_reviews += 1

        profile.rating = (
            (
                profile.rating
                * (profile.total_reviews - 1)
            )
            + rating
        ) // profile.total_reviews

    await session.flush()

    return review
