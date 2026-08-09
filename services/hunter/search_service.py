from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from services.hunter.engine import HunterEngine, HunterResult
from services.premium import is_premium
from services.search_limits import (
    can_search,
    get_remaining_searches,
    register_successful_search,
)


@dataclass(frozen=True)
class HunterSearchResponse:
    success: bool
    message: str
    results: list[HunterResult]


class HunterSearchService:

    def __init__(
        self,
        engine: HunterEngine,
    ) -> None:
        self.engine = engine

    # =====================================================
    # COMMON SEARCH
    # =====================================================

    async def _run(
        self,
        session: AsyncSession,
        user: User,
        candidates: list[str],
        amount: int,
    ) -> HunterSearchResponse:

        if user.is_blocked:
            return HunterSearchResponse(
                success=False,
                message=(
                    "⛔ <b>Доступ запрещён.</b>\n\n"
                    "Твой аккаунт заблокирован."
                ),
                results=[],
            )

        if not candidates:
            return HunterSearchResponse(
                success=False,
                message="😔 Подходящих кандидатов не найдено.",
                results=[],
            )

        allowed = await can_search(
            session=session,
            user=user,
        )

        if not allowed:
            remaining = await get_remaining_searches(
                session=session,
                user=user,
            )

            return HunterSearchResponse(
                success=False,
                message=(
                    "🚫 <b>Дневной лимит поиска исчерпан.</b>\n\n"
                    f"Осталось: <b>{remaining or 0}</b>\n\n"
                    "💎 Premium открывает безлимитный поиск."
                ),
                results=[],
            )

        results: list[HunterResult] = []

        # Проверяем кандидатов последовательно.
        # Позже здесь можно сделать конкурентную проверку
        # с ограничением количества одновременных запросов.

        for username in candidates:

            if len(results) >= amount:
                break

            try:
                result = await self.engine.check_candidate(
                    username
                )

            except Exception:
                continue

            if result is None:
                continue

            results.append(result)

        if not results:
            return HunterSearchResponse(
                success=False,
                message=(
                    "😔 <b>Свободных подходящих username не найдено.</b>\n\n"
                    "Попробуй изменить параметры поиска."
                ),
                results=[],
            )

        results.sort(
            key=lambda item: (
                item.beauty_score,
                item.liquidity,
                item.brand,
                item.rarity,
                item.price_max,
            ),
            reverse=True,
        )

        registered = await register_successful_search(
            session=session,
            user=user,
        )

        if not registered:
            return HunterSearchResponse(
                success=False,
                message=(
                    "🚫 <b>Лимит поиска закончился.</b>\n\n"
                    "Попробуй снова завтра "
                    "или активируй Premium."
                ),
                results=[],
            )

        remaining = await get_remaining_searches(
            session=session,
            user=user,
        )

        if remaining is None:
            footer = (
                "💎 <b>Premium</b> • ♾️ безлимитный поиск"
            )
        else:
            footer = (
                f"🔎 Осталось сегодня: <b>{remaining}</b>"
            )

        return HunterSearchResponse(
            success=True,
            message=footer,
            results=results[:amount],
        )

    # =====================================================
    # BEAUTIFUL
    # =====================================================

    async def beautiful(
        self,
        session: AsyncSession,
        user: User,
        length: int,
        amount: int,
    ) -> HunterSearchResponse:

        candidates = self.engine.prepare_candidates(
            length=length,
            amount=max(amount * 10, 100),
        )

        return await self._run(
            session=session,
            user=user,
            candidates=candidates,
            amount=amount,
        )

    # =====================================================
    # EXPENSIVE
    # =====================================================

    async def expensive(
        self,
        session: AsyncSession,
        user: User,
        length: int,
        amount: int,
    ) -> HunterSearchResponse:

        candidates = self.engine.prepare_candidates(
            length=length,
            amount=max(amount * 20, 200),
        )

        # Сначала сортируем кандидатов по потенциальной
        # красоте. После проверки engine.check_candidate()
        # выдаст реальные price/brand/liquidity.

        return await self._run(
            session=session,
            user=user,
            candidates=candidates,
            amount=amount,
        )

    # =====================================================
    # PREMIUM
    # =====================================================

    async def premium(
        self,
        session: AsyncSession,
        user: User,
        length: int,
        amount: int,
    ) -> HunterSearchResponse:

        if not is_premium(user):
            return HunterSearchResponse(
                success=False,
                message=(
                    "💎 <b>Нужен Premium.</b>\n\n"
                    "Пятисимвольный Hunter доступен "
                    "только Premium пользователям."
                ),
                results=[],
            )

        candidates = self.engine.prepare_candidates(
            length=length,
            amount=max(amount * 20, 200),
        )

        return await self._run(
            session=session,
            user=user,
            candidates=candidates,
            amount=amount,
        )

    # =====================================================
    # DICTIONARY
    # =====================================================

    async def dictionary(
        self,
        session: AsyncSession,
        user: User,
        length: int,
        amount: int,
    ) -> HunterSearchResponse:

        candidates = self.engine.dictionary(
            length=length,
            limit=max(amount * 20, 200),
        )

        usernames = [
            item.username
            if hasattr(item, "username")
            else item
            for item in candidates
        ]

        return await self._run(
            session=session,
            user=user,
            candidates=usernames,
            amount=amount,
        )

    # =====================================================
    # MASK
    # =====================================================

    async def mask(
        self,
        session: AsyncSession,
        user: User,
        mask: str,
        amount: int,
    ) -> HunterSearchResponse:

        candidates = self.engine.mask(
            mask=mask,
            limit=max(amount * 20, 200),
        )

        usernames = [
            item.username
            if hasattr(item, "username")
            else item
            for item in candidates
        ]

        return await self._run(
            session=session,
            user=user,
            candidates=usernames,
            amount=amount,
        )

    # =====================================================
    # POPULAR
    # =====================================================

    async def popular(
        self,
        session: AsyncSession,
        user: User,
        amount: int = 20,
    ) -> HunterSearchResponse:

        candidates = self.engine.prepare_candidates(
            length=6,
            amount=max(amount * 20, 200),
        )

        return await self._run(
            session=session,
            user=user,
            candidates=candidates,
            amount=amount,
        )


# =========================================================
# SINGLETON
# =========================================================

hunter_search_service = HunterSearchService(
    engine=HunterEngine()
)
