from __future__ import annotations

import asyncio
import logging
import sys

import uvicorn

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from config import settings

from database.session import (
    init_database,
    close_database,
)

from bot.handlers.start import (
    router as start_router,
)

from bot.handlers.menu import (
    router as menu_router,
    hunter,
)

from bot.handlers.profile import (
    router as profile_router,
)

from bot.handlers.admin_promo import (
    router as admin_promo_router,
)

from bot.handlers.tasks import (
    router as tasks_router,
)


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=getattr(
        logging,
        settings.log_level.upper(),
        logging.INFO,
    ),
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    ),
    stream=sys.stdout,
)

logger = logging.getLogger("TEYZUS")


# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(
    title="TEYZUS API",
    version="1.0.0",
)


@app.get("/")
async def root():
    return JSONResponse(
        {
            "status": "ok",
            "service": "TEYZUS",
            "bot": settings.bot_username,
        }
    )


@app.get("/health")
async def health():
    return JSONResponse(
        {
            "status": "healthy",
        }
    )


# =========================================================
# BOT
# =========================================================

async def run_bot() -> None:
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
        ),
    )

    dispatcher = Dispatcher()

    # =====================================================
    # MAIN ROUTERS
    # =====================================================

    dispatcher.include_router(
        start_router
    )

    dispatcher.include_router(
        menu_router
    )

    dispatcher.include_router(
        profile_router
    )

    # =====================================================
    # TASKS
    # =====================================================

    dispatcher.include_router(
        tasks_router
    )

    # =====================================================
    # OWNER PROMO
    # =====================================================

    dispatcher.include_router(
        admin_promo_router
    )

    logger.info(
        "TEYZUS Bot starting..."
    )

    try:
        await dispatcher.start_polling(
            bot,
            allowed_updates=(
                dispatcher.resolve_used_update_types()
            ),
        )

    finally:
        try:
            await hunter.close()
        except Exception:
            logger.exception(
                "Failed to close hunter"
            )

        await bot.session.close()


# =========================================================
# WEB
# =========================================================

async def run_web() -> None:
    configuration = uvicorn.Config(
        app,
        host=settings.web_host,
        port=settings.web_port,
        log_level=settings.log_level.lower(),
    )

    server = uvicorn.Server(
        configuration
    )

    await server.serve()


# =========================================================
# MAIN
# =========================================================

async def main() -> None:
    logger.info(
        "Initializing database..."
    )

    await init_database()

    logger.info(
        "Database initialized."
    )

    try:
        await asyncio.gather(
            run_bot(),
            run_web(),
        )

    finally:
        logger.info(
            "Closing database..."
        )

        await close_database()

        logger.info(
            "TEYZUS shutdown complete."
        )


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    try:
        asyncio.run(
            main()
        )

    except KeyboardInterrupt:
        logger.info(
            "TEYZUS stopped."
        )

    except Exception:
        logger.exception(
            "TEYZUS crashed."
        )
        raise
