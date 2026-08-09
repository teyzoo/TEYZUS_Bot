from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from services.premium import is_premium


# =========================================================
# CONSTANTS
# =========================================================

FREE_DAILY_SEARCH_LIMIT = 5


# =========================================================
# TIME
# =========================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def today_key() -> str:
    return utc_now().strftime("%Y-%m-%d")


# =========================================================
# RESET DAILY COUNTER
# =========================================================

async def reset_search_counter_if_needed(
    session: AsyncSession,
    user: User,
) -> None:

    today = today_key()

    if user.search_counter_date != today:

        user.search_counter_date = today
        user.successful_searches_today = 0

        await session.commit()


# =========================================================
# PREMIUM
# =========================================================

def has_unlimited_searches(
    user: User,
) -> bool:

    return is_premium(user)


# =========================================================
# REMAINING SEARCHES
# =========================================================

async def get_remaining_searches(
    session: AsyncSession,
    user: User,
) -> int | None:

    await reset_search_counter_if_needed(
        session=session,
        user=user,
    )

    if has_unlimited_searches(user):
        return None

    remaining = (
        FREE_DAILY_SEARCH_LIMIT
        - user.successful_searches_today
    )

    return max(
        remaining,
        0,
    )


# =========================================================
# CAN SEARCH
# =========================================================

async def can_search(
    session: AsyncSession,
    user: User,
) -> bool:

    remaining = await get_remaining_searches(
        session=session,
        user=user,
    )

    if remaining is None:
        return True

    return remaining > 0


# =========================================================
# REGISTER SUCCESSFUL SEARCH
# =========================================================

async def register_successful_search(
    session: AsyncSession,
    user: User,
) -> bool:

    await reset_search_counter_if_needed(
        session=session,
        user=user,
    )

    # Premium не расходует дневной лимит.
    if has_unlimited_searches(user):
        return True

    if (
        user.successful_searches_today
        >= FREE_DAILY_SEARCH_LIMIT
    ):
        return False

    user.successful_searches_today += 1

    await session.commit()

    return True


# =========================================================
# SEARCH STATUS TEXT
# =========================================================

async def search_limit_text(
    session: AsyncSession,
    user: User,
) -> str:

    remaining = await get_remaining_searches(
        session=session,
        user=user,
    )

    if remaining is None:
        return "💎 <b>Premium:</b> ♾️ безлимитный поиск"

    if remaining <= 0:
        return (
            "🔎 <b>Поиски:</b> 0/5\n\n"
            "❌ Дневной лимит исчерпан.\n"
            "💎 Оформи Premium для безлимитного поиска."
        )

    return (
        f"🔎 <b>Поиски сегодня:</b> "
        f"{remaining}/"
        f"{FREE_DAILY_SEARCH_LIMIT}"
    )
