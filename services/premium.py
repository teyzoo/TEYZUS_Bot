from datetime import datetime, timezone

from database.models import User


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

    return premium_until > datetime.now(
        timezone.utc
    )


def premium_status_text(
    user: User,
) -> str:

    if is_premium(user):

        if user.premium_until:
            return (
                "💎 Premium до "
                f"{user.premium_until:%d.%m.%Y}"
            )

        return "💎 Premium активен"

    return "▫️ Premium не активен"
