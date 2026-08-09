from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    PromoActivation,
    PromoCode,
)


class PromoRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    # =====================================================
    # GET
    # =====================================================

    async def get_by_id(
        self,
        promo_id: int,
    ) -> PromoCode | None:

        result = await self.session.execute(
            select(PromoCode).where(
                PromoCode.id
                == promo_id
            )
        )

        return result.scalar_one_or_none()

    async def get_by_code(
        self,
        code: str,
    ) -> PromoCode | None:

        normalized = (
            code
            .strip()
            .upper()
        )

        result = await self.session.execute(
            select(PromoCode)
            .where(
                func.upper(
                    PromoCode.code
                )
                == normalized
            )
        )

        return result.scalar_one_or_none()

    # =====================================================
    # CREATE
    # =====================================================

    async def create(
        self,
        **kwargs,
    ) -> PromoCode:

        promo = PromoCode(
            **kwargs
        )

        self.session.add(
            promo
        )

        await self.session.flush()

        return promo

    # =====================================================
    # UPDATE
    # =====================================================

    async def update(
        self,
        promo: PromoCode,
        **kwargs,
    ) -> PromoCode:

        for key, value in kwargs.items():

            if hasattr(promo, key):
                setattr(
                    promo,
                    key,
                    value,
                )

        await self.session.flush()

        return promo

    # =====================================================
    # DELETE
    # =====================================================

    async def delete(
        self,
        promo: PromoCode,
    ) -> None:

        await self.session.delete(
            promo
        )

        await self.session.flush()

    # =====================================================
    # ACTIVATION COUNT
    # =====================================================

    async def get_user_activation_count(
        self,
        promo_id: int,
        user_id: int,
    ) -> int:

        result = await self.session.execute(
            select(
                func.count(
                    PromoActivation.id
                )
            )
            .where(
                PromoActivation.promo_id
                == promo_id,
                PromoActivation.user_id
                == user_id,
            )
        )

        return int(
            result.scalar_one()
        )

    async def create_activation(
        self,
        **kwargs,
    ) -> PromoActivation:

        activation = PromoActivation(
            **kwargs
        )

        self.session.add(
            activation
        )

        await self.session.flush()

        return activation

    # =====================================================
    # VALIDATION
    # =====================================================

    async def can_activate(
        self,
        promo: PromoCode,
        user_id: int,
        is_premium: bool,
        is_new_user: bool,
    ) -> tuple[bool, str]:

        now = datetime.now(
            timezone.utc
        )

        if not promo.is_active:
            return (
                False,
                "Промокод отключён.",
            )

        if (
            promo.starts_at
            and now < promo.starts_at
        ):
            return (
                False,
                "Промокод ещё не активен.",
            )

        if (
            promo.expires_at
            and now > promo.expires_at
        ):
            return (
                False,
                "Срок действия промокода истёк.",
            )

        if (
            promo.max_activations
            is not None
            and promo.activations_count
            >= promo.max_activations
        ):
            return (
                False,
                "Лимит активаций промокода исчерпан.",
            )

        if (
            promo.only_premium
            and not is_premium
        ):
            return (
                False,
                "Этот промокод доступен только Premium.",
            )

        if (
            promo.only_new_users
            and not is_new_user
        ):
            return (
                False,
                "Этот промокод доступен только новым пользователям.",
            )

        if promo.allowed_user_ids:

            allowed = {
                int(x.strip())
                for x in promo.allowed_user_ids.split(",")
                if x.strip().isdigit()
            }

            if user_id not in allowed:

                return (
                    False,
                    "У вас нет доступа к этому промокоду.",
                )

        user_count = (
            await self.get_user_activation_count(
                promo.id,
                user_id,
            )
        )

        if (
            promo.max_activations_per_user
            is not None
            and user_count
            >= promo.max_activations_per_user
        ):
            return (
                False,
                "Вы достигли лимита активаций этого промокода.",
            )

        return (
            True,
            "OK",
        )
