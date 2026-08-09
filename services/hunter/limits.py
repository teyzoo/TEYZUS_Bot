from __future__ import annotations

from datetime import datetime, timezone

from database.models import User
from services.premium import is_premium


FREE_DAILY_SEARCH_LIMIT = 5


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def today_string() -> str:
    return utc_now().strftime("%Y-%m-%d")


def reset_daily_counter_if_needed(
    user: User,
) -> None:
    today = today_string()

    if user.search_counter_date != today:
        user.search_counter_date = today
        user.successful_searches_today = 0


def get_daily_search_limit(
    user: User,
) -> int | None:
    """
    None = безлимит.
    """

    if is_premium(user):
        return None

    return FREE_DAILY_SEARCH_LIMIT


def get_remaining_daily_searches(
    user: User,
) -> int | None:
    """
    Возвращает:
    None — безлимит
    число — сколько обычных поисков осталось.
    """

    reset_daily_counter_if_needed(user)

    limit = get_daily_search_limit(user)

    if limit is None:
        return None

    remaining = (
        limit
        - user.successful_searches_today
    )

    return max(remaining, 0)


def can_search(
    user: User,
) -> bool:

    if user.is_blocked:
        return False

    remaining = get_remaining_daily_searches(
        user
    )

    if remaining is None:
        return True

    return remaining > 0


def consume_search(
    user: User,
) -> bool:
    """
    Списывает один обычный поиск.

    Важно:
    дополнительный поиск из промокода
    здесь пока не списывается.

    Возвращает True, если поиск успешно списан.
    """

    if user.is_blocked:
        return False

    reset_daily_counter_if_needed(user)

    limit = get_daily_search_limit(user)

    if limit is None:
        return True

    if user.successful_searches_today >= limit:
        return False

    user.successful_searches_today += 1

    return True


def search_limit_text(
    user: User,
) -> str:

    remaining = get_remaining_daily_searches(
        user
    )

    if remaining is None:
        return "♾️ Безлимит"

    return (
        f"🔎 Осталось сегодня: "
        f"<b>{remaining}</b>"
    )
