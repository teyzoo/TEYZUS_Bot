from __future__ import annotations

from datetime import datetime, timezone

from database.models import User


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def is_premium(
    user: User,
) -> bool:

    if not user.premium_active:
        return False

    if user.premium_until is None:
        return True

    premium_until = user.premium_until

    if premium_until.tzinfo is None:
        premium_until = premium_until.replace(
            tzinfo=timezone.utc
        )

    if premium_until <= utc_now():

        user.premium_active = False

        return False

    return True


def premium_status_text(
    user: User,
) -> str:

    if is_premium(user):

        if user.premium_until:

            premium_until = user.premium_until

            return (
                "💎 Premium до "
                f"{premium_until:%d.%m.%Y}"
            )

        return "💎 Premium активен"

    return "▫️ Premium не активен"
