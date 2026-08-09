from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qsl

from fastapi import Header, HTTPException
from sqlalchemy import select

from config import settings
from database.models import User
from database.session import get_session


# =========================================================
# TELEGRAM WEB APP AUTH
# =========================================================

@dataclass
class TelegramWebAppUser:
    id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    language_code: str | None
    allows_write_to_pm: bool = False


# =========================================================
# HASH
# =========================================================

def _secret_key() -> bytes:
    """
    Telegram Web App secret key.

    secret_key = HMAC_SHA256(
        key=b"WebAppData",
        message=BOT_TOKEN
    )
    """

    return hmac.new(
        b"WebAppData",
        settings.bot_token.encode(),
        hashlib.sha256,
    ).digest()


# =========================================================
# VALIDATE INIT DATA
# =========================================================

def validate_init_data(
    init_data: str,
    max_age: int = 86400,
) -> TelegramWebAppUser:

    if not init_data:
        raise ValueError(
            "Empty Telegram initData"
        )

    pairs = dict(
        parse_qsl(
            init_data,
            keep_blank_values=True,
        )
    )

    received_hash = pairs.pop(
        "hash",
        None,
    )

    if not received_hash:
        raise ValueError(
            "Telegram hash missing"
        )

    auth_date_raw = pairs.get(
        "auth_date"
    )

    if not auth_date_raw:
        raise ValueError(
            "Telegram auth_date missing"
        )

    try:
        auth_date = int(
            auth_date_raw
        )
    except ValueError as exc:
        raise ValueError(
            "Invalid auth_date"
        ) from exc

    # -----------------------------------------------------
    # EXPIRATION
    # -----------------------------------------------------

    now = int(
        time.time()
    )

    if now - auth_date > max_age:
        raise ValueError(
            "Telegram initData expired"
        )

    if auth_date > now + 60:
        raise ValueError(
            "Telegram auth_date is invalid"
        )

    # -----------------------------------------------------
    # DATA CHECK STRING
    # -----------------------------------------------------

    data_check_string = "\n".join(
        f"{key}={value}"
        for key, value in sorted(
            pairs.items()
        )
    )

    calculated_hash = hmac.new(
        _secret_key(),
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(
        calculated_hash,
        received_hash,
    ):
        raise ValueError(
            "Telegram initData hash invalid"
        )

    # -----------------------------------------------------
    # USER
    # -----------------------------------------------------

    user_raw = pairs.get(
        "user"
    )

    if not user_raw:
        raise ValueError(
            "Telegram user missing"
        )

    try:
        user_data: dict[str, Any] = json.loads(
            user_raw
        )
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Invalid Telegram user JSON"
        ) from exc

    telegram_id = user_data.get(
        "id"
    )

    if not telegram_id:
        raise ValueError(
            "Telegram user ID missing"
        )

    return TelegramWebAppUser(
        id=int(telegram_id),
        username=user_data.get(
            "username"
        ),
        first_name=user_data.get(
            "first_name"
        ),
        last_name=user_data.get(
            "last_name"
        ),
        language_code=user_data.get(
            "language_code"
        ),
        allows_write_to_pm=bool(
            user_data.get(
                "allows_write_to_pm",
                False,
            )
        ),
    )


# =========================================================
# DATABASE USER
# =========================================================

async def get_database_user(
    telegram_user: TelegramWebAppUser,
) -> User:

    async with get_session() as session:

        result = await session.execute(
            select(User).where(
                User.telegram_id
                == telegram_user.id
            )
        )

        user = (
            result.scalar_one_or_none()
        )

        if user is None:
            raise HTTPException(
                status_code=404,
                detail="User is not registered",
            )

        # -------------------------------------------------
        # UPDATE TELEGRAM DATA
        # -------------------------------------------------

        user.username = (
            telegram_user.username
        )

        user.first_name = (
            telegram_user.first_name
        )

        user.last_name = (
            telegram_user.last_name
        )

        if telegram_user.language_code:
            user.language = (
                telegram_user.language_code
            )

        await session.commit()

        return user


# =========================================================
# FASTAPI DEPENDENCY
# =========================================================

async def get_current_user(
    x_telegram_init_data: str | None = Header(
        default=None,
        alias="X-Telegram-Init-Data",
    ),
) -> User:

    if not x_telegram_init_data:
        raise HTTPException(
            status_code=401,
            detail="Telegram authorization required",
        )

    try:
        telegram_user = validate_init_data(
            x_telegram_init_data
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=401,
            detail=str(exc),
        ) from exc

    user = await get_database_user(
        telegram_user
    )

    if user.is_blocked:
        raise HTTPException(
            status_code=403,
            detail="User blocked",
        )

    return user
