from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from services.hunter.engine import (
    HunterEngine,
    HunterResult,
)
from services.search_limits import (
    can_search,
    register_successful_search,
    get_remaining_searches,
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
    # SEARCH
    # =====================================================

    async def search(
        self,
        session: AsyncSession,
        user: User,
        length: int,
        amount: int = 1,
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
        # AMOUNT VALIDATION
        # -------------------------------------------------

        if amount < 1:

            amount = 1

        if amount > 100:

            amount = 100

        # -------------------------------------------------
        # LENGTH VALIDATION
        # -------------------------------------------------

        if length < 5 or length > 32:

            return HunterSearchResponse(
                success=False,
                message=(
                    "❌ Недопустимая длина username.\n\n"
                    "Разрешено: от 5 до 32 символов."
                ),
                results=[],
            )

        # -------------------------------------------------
        # PREMIUM / FREE
        # -------------------------------------------------

        from services.premium import is_premium

        premium = is_premium(user)

        # -------------------------------------------------
        # 5 SYMBOLS — PREMIUM
        # -------------------------------------------------

        if length == 5 and not premium:

            return HunterSearchResponse(
                success=False,
                message=(
                    "💎 <b>Пятисимвольный поиск</b>\n\n"
                    "Username длиной 5 символов "
                    "доступны только Premium пользователям."
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

            remaining_text = (
                str(remaining)
                if remaining is not None
                else "∞"
            )

            return HunterSearchResponse(
                success=False,
                message=(
                    "🚫 <b>Дневной лимит поиска исчерпан.</b>\n\n"
                    f"Осталось поисков: <b>{remaining_text}</b>\n\n"
                    "💎 Premium открывает безлимитный поиск."
                ),
                results=[],
            )

        # -------------------------------------------------
        # SEARCH
        # -------------------------------------------------

        try:

            results = await self.engine.search(
                length=length,
                amount=amount,
            )

        except Exception:

            return HunterSearchResponse(
                success=False,
                message=(
                    "⚠️ <b>Ошибка поиска.</b>\n\n"
                    "Попробуй повторить поиск немного позже."
                ),
                results=[],
            )

        # -------------------------------------------------
        # NOTHING FOUND
        # -------------------------------------------------

        if not results:

            return HunterSearchResponse(
                success=False,
                message=(
                    "😔 <b>Ничего не найдено.</b>\n\n"
                    "Попробуй другую длину или другой режим поиска."
                ),
                results=[],
            )

        # -------------------------------------------------
        # SUCCESS
        # -------------------------------------------------

        registered = await register_successful_search(
            session=session,
            user=user,
        )

        if not registered:

            return HunterSearchResponse(
                success=False,
                message=(
                    "🚫 <b>Лимит поиска исчерпан.</b>\n\n"
                    "Попробуй снова завтра "
                    "или активируй Premium."
                ),
                results=[],
            )

        # -------------------------------------------------
        # RESULT MESSAGE
        # -------------------------------------------------

        remaining = await get_remaining_searches(
            session=session,
            user=user,
        )

        if remaining is None:

            limit_text = (
                "💎 Premium • ♾️ безлимит"
            )

        else:

            limit_text = (
                f"🔎 Осталось сегодня: "
                f"<b>{remaining}</b>"
            )

        return HunterSearchResponse(
            success=True,
            message=(
                "✅ <b>Поиск завершён!</b>\n\n"
                f"{limit_text}"
            ),
            results=results,
        )


# =========================================================
# SINGLETON
# =========================================================

hunter_search_service = HunterSearchService(
    engine=HunterEngine()
)
