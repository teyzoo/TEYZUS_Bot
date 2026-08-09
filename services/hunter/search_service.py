from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User

from services.hunter.engine import (
    HunterEngine,
    HunterResult,
)

from services.hunter.limits import (
    can_search,
    consume_search,
    get_remaining_daily_searches,
    reset_daily_counter_if_needed,
)


@dataclass(frozen=True)
class SearchResult:
    success: bool
    message: str

    results: list[HunterResult]

    consumed_search: bool = False
    remaining_searches: int | None = None


class SearchService:

    def __init__(
        self,
        hunter: HunterEngine,
    ) -> None:

        self.hunter = hunter

    async def search(
        self,
        session: AsyncSession,
        user: User,
        length: int,
        amount: int = 10,
    ) -> SearchResult:

        # =================================================
        # USER BLOCK
        # =================================================

        if user.is_blocked:

            return SearchResult(
                success=False,
                message=(
                    "⛔ <b>Твой аккаунт заблокирован.</b>\n\n"
                    "Использование поиска недоступно."
                ),
                results=[],
            )

        # =================================================
        # RESET DAILY COUNTER
        # =================================================

        reset_daily_counter_if_needed(user)

        # =================================================
        # LIMIT CHECK
        # =================================================

        if not can_search(user):

            return SearchResult(
                success=False,
                message=(
                    "🚫 <b>Лимит поиска на сегодня исчерпан.</b>\n\n"
                    "Бесплатный лимит: "
                    "<b>5 поисков в день</b>.\n\n"
                    "💎 TEYZUS Premium снимает "
                    "дневной лимит."
                ),
                results=[],
                remaining_searches=0,
            )

        # =================================================
        # VALIDATION
        # =================================================

        if length < 5 or length > 32:

            return SearchResult(
                success=False,
                message=(
                    "❌ Некорректная длина username.\n\n"
                    "Допустимо: <b>5–32</b> символа."
                ),
                results=[],
            )

        if amount < 1:

            return SearchResult(
                success=False,
                message=(
                    "❌ Количество результатов "
                    "должно быть больше 0."
                ),
                results=[],
            )

        amount = min(
            amount,
            100,
        )

        # =================================================
        # HUNTER
        # =================================================

        try:

            results = await self.hunter.search(
                length=length,
                amount=amount,
            )

        except Exception:

            return SearchResult(
                success=False,
                message=(
                    "⚠️ <b>Ошибка Hunter Engine.</b>\n\n"
                    "Попробуй повторить поиск позже."
                ),
                results=[],
            )

        # =================================================
        # NO RESULTS
        # =================================================

        if not results:

            return SearchResult(
                success=False,
                message=(
                    "😔 Подходящих доступных "
                    "username не найдено."
                ),
                results=[],
                remaining_searches=(
                    get_remaining_daily_searches(
                        user
                    )
                ),
            )

        # =================================================
        # CONSUME SEARCH
        # =================================================

        consumed = consume_search(
            user
        )

        if not consumed:

            return SearchResult(
                success=False,
                message=(
                    "🚫 <b>Лимит поиска исчерпан.</b>"
                ),
                results=[],
                remaining_searches=0,
            )

        # =================================================
        # SAVE USER
        # =================================================

        await session.commit()

        remaining = (
            get_remaining_daily_searches(
                user
            )
        )

        return SearchResult(
            success=True,
            message=(
                "✅ <b>Поиск завершён.</b>"
            ),
            results=results,
            consumed_search=True,
            remaining_searches=remaining,
        )


hunter_engine = HunterEngine()

search_service = SearchService(
    hunter=hunter_engine
)
