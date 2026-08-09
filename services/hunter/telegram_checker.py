from __future__ import annotations

import asyncio
from typing import Optional

from telethon import TelegramClient
from telethon.errors import (
    FloodWaitError,
    UsernameInvalidError,
    UsernameNotOccupiedError,
)
from telethon.tl.functions.contacts import ResolveUsernameRequest

from config import API_ID, API_HASH


# =========================================================
# TELEGRAM CLIENT
# =========================================================

client = TelegramClient(
    "checker",
    API_ID,
    API_HASH,
)


# =========================================================
# LOCK
# =========================================================

_connect_lock = asyncio.Lock()


# =========================================================
# CONNECT
# =========================================================

async def ensure_connected() -> None:

    if client.is_connected():
        return

    async with _connect_lock:

        if client.is_connected():
            return

        await client.connect()


# =========================================================
# CHECK USERNAME
# =========================================================

async def check_telegram(
    username: str,
) -> bool:

    username = username.strip()

    if username.startswith("@"):
        username = username[1:]

    username = username.lower()

    if not username:
        return False

    try:

        await ensure_connected()

        result = await client(
            ResolveUsernameRequest(
                username=username
            )
        )

        # -------------------------------------------------
        # Если Telegram вернул entity,
        # username уже занят.
        # -------------------------------------------------

        if result.users:

            return False

        if result.chats:

            return False

        # -------------------------------------------------
        # Нет entity -> username может быть свободен.
        # -------------------------------------------------

        return True

    except UsernameNotOccupiedError:

        return True

    except UsernameInvalidError:

        return False

    except FloodWaitError as error:

        # Не пытаемся спамить Telegram во время FloodWait.
        await asyncio.sleep(
            error.seconds
        )

        return await check_telegram(
            username
        )

    except asyncio.CancelledError:

        raise

    except Exception:

        return False


# =========================================================
# DISCONNECT
# =========================================================

async def close_telegram() -> None:

    if client.is_connected():

        await client.disconnect()
