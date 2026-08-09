from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User

from services.hunter.engine import (
    HunterEngine,
    HunterResult,
)

from services.premium import is_premium

from services.search_limits import (
    can_search,
    get_remaining_searches,
    register_successful_search,
)

from services.hunter.modes import (
    generate_dictionary_candidates,
    generate_mask_candidates,
    sort_expensive_candidates,
    sort_popular_candidates,
)


# =========================================================
# RESULT
# =========================================================

@dataclass(frozen=True)
class HunterSearchResponse:
    success: bool
    message: str
    results: list[HunterResult]


# =========================================================
# SERVICE
# =========================================================

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

        # -------------------------------------------------
        # BLOCKED
        # -------------------------------------------------

        if user.is_blocked:

            return HunterSearchResponse(
                success=False,
                message=(
                    "⛔ <b>Доступ запрещён.</b>\n\n"
                    "Твой аккаунт заблокирован."
                ),
                results=[],
            )

        # -------------------------------------------------
        # NORMALIZE
        # -------------------------------------------------

        normalized: list[str] = []

        seen: set[str] = set()

        for username in candidates:

            username = username.strip().lower()

            if username.startswith("@"):
                username = username[1:]

            if not username:
                continue

            if username in seen:
                continue

            seen.add(username)

            normalized.append(username)

        candidates = normalized

        # -------------------------------------------------
        # EMPTY
        # -------------------------------------------------

        if not candidates:

            return HunterSearchResponse(
                success=False,
                message=(
                    "😔 <b>Подходящих кандидатов не найдено.</b>\n\n"
                    "Попробуй изменить параметры поиска."
                ),
                results=[],
            )

        # -------------------------------------------------
        # CHECK LIMIT
        # -------------------------------------------------

        allowed = await can_search(
            session=session,
            user=user,
        )

        if not allowed:

            remaining = await get_remaining_searches(
                session=session,
                user=user,
            )

            if remaining is None:

                limit_text = "♾️"

            else:

                limit_text = str(
                    remaining or 0
                )

            return HunterSearchResponse(
                success=False,
                message=(
                    "🚫 <b>Лимит поиска исчерпан.</b>\n\n"
                    f"Осталось: <b>{limit_text}</b>\n\n"
                    "💎 TEYZUS Premium открывает "
                    "безлимитный поиск."
                ),
                results=[],
            )

        # -------------------------------------------------
        # CHECK CANDIDATES
        # -------------------------------------------------

        results: list[HunterResult] = []

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

        # -------------------------------------------------
        # NOTHING FOUND
        # -------------------------------------------------

        if not results:

            return HunterSearchResponse(
                success=False,
                message=(
                    "😔 <b>Свободных username не найдено.</b>\n\n"
                    "Попробуй изменить параметры поиска."
                ),
                results=[],
            )

        # -------------------------------------------------
        # SORT
        # -------------------------------------------------

        results.sort(
            key=lambda item: (
                getattr(
                    item,
                    "beauty_score",
                    0,
                ),
                getattr(
                    item,
                    "liquidity",
                    0,
                ),
                getattr(
                    item,
                    "brand",
                    0,
                ),
                getattr(
                    item,
                    "rarity",
                    0,
                ),
                getattr(
                    item,
                    "price_max",
                    0,
                ),
            ),
            reverse=True,
        )

        results = results[:amount]

        # -------------------------------------------------
        # REGISTER SEARCH
        # -------------------------------------------------

        registered = await register_successful_search(
            session=session,
            user=user,
        )

        if not registered:

            return HunterSearchResponse(
                success=False,
                message=(
                    "🚫 <b>Лимит поиска закончился.</b>\n\n"
                    "Попробуй снова позже "
                    "или активируй Premium."
                ),
                results=[],
            )

        # -------------------------------------------------
        # REMAINING
        # -------------------------------------------------

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
                f"🔎 Осталось сегодня: "
                f"<b>{remaining}</b>"
            )

        # -------------------------------------------------
        # SUCCESS
        # -------------------------------------------------

        return HunterSearchResponse(
            success=True,
            message=footer,
            results=results,
        )

    # =====================================================
    # 6 CHARACTERS
    # =====================================================

    async def six_characters(
        self,
        session: AsyncSession,
        user: User,
        amount: int = 10,
    ) -> HunterSearchResponse:

        candidates = self.engine.prepare_candidates(
            length=6,
            amount=max(
                amount * 20,
                200,
            ),
        )

        return await self._run(
            session=session,
            user=user,
            candidates=candidates,
            amount=amount,
        )

    # =====================================================
    # 5 CHARACTERS
    # =====================================================

    async def five_characters(
        self,
        session: AsyncSession,
        user: User,
        amount: int = 10,
    ) -> HunterSearchResponse:

        if not is_premium(user):

            return HunterSearchResponse(
                success=False,
                message=(
                    "💎 <b>Нужен TEYZUS Premium.</b>\n\n"
                    "Поиск username из 5 символов "
                    "доступен только Premium пользователям."
                ),
                results=[],
            )

        candidates = self.engine.prepare_candidates(
            length=5,
            amount=max(
                amount * 30,
                300,
            ),
        )

        return await self._run(
            session=session,
            user=user,
            candidates=candidates,
            amount=amount,
        )

    # =====================================================
    # BEAUTIFUL
    # =====================================================

    async def beautiful(
        self,
        session: AsyncSession,
        user: User,
        length: int = 6,
        amount: int = 10,
    ) -> HunterSearchResponse:

        if length < 5:

            return HunterSearchResponse(
                success=False,
                message="❌ Минимальная длина username — 5.",
                results=[],
            )

        if length > 32:

            return HunterSearchResponse(
                success=False,
                message="❌ Максимальная длина username — 32.",
                results=[],
            )

        if length == 5 and not is_premium(user):

            return HunterSearchResponse(
                success=False,
                message=(
                    "💎 <b>Нужен Premium.</b>\n\n"
                    "5-символьный поиск доступен Premium."
                ),
                results=[],
            )

        candidates = self.engine.prepare_candidates(
            length=length,
            amount=max(
                amount * 30,
                300,
            ),
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
        length: int = 6,
        amount: int = 10,
    ) -> HunterSearchResponse:

        if length < 5:

            return HunterSearchResponse(
                success=False,
                message="❌ Минимальная длина — 5.",
                results=[],
            )

        if length == 5 and not is_premium(user):

            return HunterSearchResponse(
                success=False,
                message=(
                    "💎 <b>Нужен Premium.</b>\n\n"
                    "5-символьный поиск доступен Premium."
                ),
                results=[],
            )

        candidates = self.engine.prepare_candidates(
            length=length,
            amount=max(
                amount * 50,
                500,
            ),
        )

        candidates = sort_expensive_candidates(
            candidates
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
        words: list[str],
        length: int = 6,
        amount: int = 10,
    ) -> HunterSearchResponse:

        if length < 5:

            return HunterSearchResponse(
                success=False,
                message="❌ Минимальная длина — 5.",
                results=[],
            )

        if length == 5 and not is_premium(user):

            return HunterSearchResponse(
                success=False,
                message=(
                    "💎 <b>Нужен Premium.</b>\n\n"
                    "Dictionary на 5 символов доступен Premium."
                ),
                results=[],
            )

        candidates = generate_dictionary_candidates(
            words=words,
            length=length,
            limit=max(
                amount * 30,
                300,
            ),
        )

        return await self._run(
            session=session,
            user=user,
            candidates=candidates,
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
        amount: int = 10,
    ) -> HunterSearchResponse:

        mask = mask.strip().lower()

        if not mask:

            return HunterSearchResponse(
                success=False,
                message="❌ Маска не может быть пустой.",
                results=[],
            )

        if len(mask) < 5:

            return HunterSearchResponse(
                success=False,
                message=(
                    "❌ Username должен содержать "
                    "минимум 5 символов."
                ),
                results=[],
            )

        if len(mask) > 32:

            return HunterSearchResponse(
                success=False,
                message=(
                    "❌ Username может содержать "
                    "максимум 32 символа."
                ),
                results=[],
            )

        if len(mask) == 5 and not is_premium(user):

            return HunterSearchResponse(
                success=False,
                message=(
                    "💎 <b>Нужен Premium.</b>\n\n"
                    "5-символьные маски доступны Premium."
                ),
                results=[],
            )

        candidates = generate_mask_candidates(
            mask=mask,
            limit=max(
                amount * 30,
                300,
            ),
        )

        return await self._run(
            session=session,
            user=user,
            candidates=candidates,
            amount=amount,
        )

    # =====================================================
    # POPULAR
    # =====================================================

    async def popular(
        self,
        session: AsyncSession,
        user: User,
        length: int = 6,
        amount: int = 10,
    ) -> HunterSearchResponse:

        if length < 5:

            return HunterSearchResponse(
                success=False,
                message="❌ Минимальная длина — 5.",
                results=[],
            )

        if length == 5 and not is_premium(user):

            return HunterSearchResponse(
                success=False,
                message=(
                    "💎 <b>Нужен Premium.</b>\n\n"
                    "5-символьный поиск доступен Premium."
                ),
                results=[],
            )

        candidates = self.engine.prepare_candidates(
            length=length,
            amount=max(
                amount * 50,
                500,
            ),
        )

        candidates = sort_popular_candidates(
            candidates
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
