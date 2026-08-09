from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from services.premium import is_premium


FREE_DAILY_LIMIT = 5


def current_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def reset_daily_counter_if_needed(
    user: User,
) -> None:

    today = current_date()

    if user.search_counter_date != today:
        user.successful_searches_today = 0
        user.search_counter_date = today


def get_daily_limit(
    user: User,
) -> int | None:

    if is_premium(user):
        return None

    return FREE_DAILY_LIMIT


def searches_left(
    user: User,
) -> int | None:

    reset_daily_counter_if_needed(user)

    limit = get_daily_limit(user)

    if limit is None:
        return None

    return max(
        0,
        limit - user.successful_searches_today,
    )


def can_search(
    user: User,
) -> bool:

    reset_daily_counter_if_needed(user)

    limit = get_daily_limit(user)

    if limit is None:
        return True

    return (
        user.successful_searches_today
        < limit
    )


async def register_successful_search(
    session: AsyncSession,
    user: User,
    found_count: int,
) -> None:

    if found_count <= 0:
        return

    reset_daily_counter_if_needed(user)

    user.successful_searches_today += found_count

    await session.commit()


def limit_text(
    user: User,
) -> str:

    reset_daily_counter_if_needed(user)

    if is_premium(user):
        return "💎 Premium: ♾️ безлимитный поиск"

    left = searches_left(user)

    return (
        f"🔎 Бесплатных найденных сегодня: "
        f"<b>{left}/5</b>"
    )
