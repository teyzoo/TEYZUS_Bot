from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    ShopDeal,
    ShopListing,
    ShopPurchase,
)


class DealService:

    # =====================================================
    # CREATE DEAL
    # =====================================================

    @staticmethod
    async def create_purchase(
        session: AsyncSession,
        *,
        listing: ShopListing,
        buyer_id: int,
        payment_method: str,
    ) -> ShopPurchase:

        if not listing.is_active:
            raise ValueError(
                "Listing is inactive"
            )

        if listing.status != "approved":
            raise ValueError(
                "Listing is not available"
            )

        if listing.seller_id == buyer_id:
            raise ValueError(
                "You cannot buy your own username"
            )

        purchase = ShopPurchase(
            listing_id=listing.id,
            buyer_id=buyer_id,
            seller_id=listing.seller_id,
            username=listing.username,
            price_rub=listing.price_rub,
            price_stars=listing.price_stars,
            payment_method=payment_method,
            status="pending",
        )

        session.add(
            purchase
        )

        # Временно резервируем объявление.
        listing.status = "reserved"

        await session.flush()

        return purchase

    # =====================================================
    # CREATE ESCROW DEAL
    # =====================================================

    @staticmethod
    async def create_deal(
        session: AsyncSession,
        *,
        purchase: ShopPurchase,
        commission_percent: int = 0,
    ) -> ShopDeal:

        amount = purchase.price_rub

        commission = (
            amount
            * commission_percent
            // 100
        )

        seller_amount = (
            amount - commission
        )

        deal = ShopDeal(
            purchase_id=purchase.id,
            buyer_id=purchase.buyer_id,
            seller_id=purchase.seller_id,
            amount_rub=amount,
            commission_rub=commission,
            seller_amount_rub=seller_amount,
            status="waiting_payment",
        )

        session.add(
            deal
        )

        await session.flush()

        return deal

    # =====================================================
    # PAYMENT CONFIRMED
    # =====================================================

    @staticmethod
    async def mark_paid(
        session: AsyncSession,
        deal: ShopDeal,
    ) -> None:

        if deal.status != "waiting_payment":
            raise ValueError(
                "Deal is not waiting for payment"
            )

        deal.status = "paid"

        purchase = await session.get(
            ShopPurchase,
            deal.purchase_id,
        )

        if purchase is not None:
            purchase.status = "paid"

            listing = None

            if purchase.listing_id:
                listing = await session.get(
                    ShopListing,
                    purchase.listing_id,
                )

            if listing is not None:
                listing.status = "reserved"

        await session.flush()

    # =====================================================
    # BUYER CONFIRMATION
    # =====================================================

    @staticmethod
    async def buyer_confirm(
        session: AsyncSession,
        deal: ShopDeal,
        buyer_id: int,
    ) -> None:

        if deal.buyer_id != buyer_id:
            raise PermissionError(
                "Not deal buyer"
            )

        deal.buyer_confirmed = True

        await DealService._try_complete(
            session,
            deal,
        )

    # =====================================================
    # SELLER CONFIRMATION
    # =====================================================

    @staticmethod
    async def seller_confirm(
        session: AsyncSession,
        deal: ShopDeal,
        seller_id: int,
    ) -> None:

        if deal.seller_id != seller_id:
            raise PermissionError(
                "Not deal seller"
            )

        deal.seller_confirmed = True

        await DealService._try_complete(
            session,
            deal,
        )

    # =====================================================
    # COMPLETE
    # =====================================================

    @staticmethod
    async def _try_complete(
        session: AsyncSession,
        deal: ShopDeal,
    ) -> None:

        if not deal.buyer_confirmed:
            return

        if not deal.seller_confirmed:
            return

        if deal.status in {
            "completed",
            "cancelled",
            "refunded",
        }:
            return

        deal.status = "completed"

        deal.completed_at = (
            datetime.now(timezone.utc)
        )

        purchase = await session.get(
            ShopPurchase,
            deal.purchase_id,
        )

        if purchase is not None:

            purchase.status = "completed"

            purchase.completed_at = (
                datetime.now(timezone.utc)
            )

            if purchase.listing_id:

                listing = await session.get(
                    ShopListing,
                    purchase.listing_id,
                )

                if listing is not None:

                    listing.status = "sold"

                    listing.is_active = False

                    listing.sold_at = (
                        datetime.now(timezone.utc)
                    )

                    listing.purchase_count += 1

        await session.flush()
