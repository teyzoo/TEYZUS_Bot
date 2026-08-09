from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
FREE_DAILY_LIMIT = 5
def reset_daily_counter_if_needed(
    user: User,
) -> bool:
    today = datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%d")
    if user.search_counter_date != today:
        user.search_counter_date = today
        user.successful_searches_today = 0
        return True
    return False
def searches_left(
    user: User,
) -> int | None:
    reset_daily_counter_if_needed(user)
    if user.premium_active:
        return None
    return max(
        0,
        FREE_DAILY_LIMIT
        - user.successful_searches_today,
    )
def can_search(
    user: User,
) -> bool:
    remaining = searches_left(user)
    if remaining is None:
        return True
    return remaining > 0
def limit_text(
    user: User,
) -> str:
    remaining = searches_left(user)
    if remaining is None:
        return "💎 Premium: ♾️"
    return (
        f"🔎 Осталось сегодня: "
        f"<b>{remaining}/{FREE_DAILY_LIMIT}</b>"
    )
async def register_successful_search(
    session: AsyncSession,
    user: User,
    found_count: int,
) -> None:
    if found_count <= 0:
        return
    if user.premium_active:
        return
    reset_daily_counter_if_needed(user)
    remaining = max(
        0,
        FREE_DAILY_LIMIT
        - user.successful_searches_today,
    )
    counted = min(
        found_count,
        remaining,
    )
    user.successful_searches_today += counted
    await session.commit()
    await session.refresh(user)
