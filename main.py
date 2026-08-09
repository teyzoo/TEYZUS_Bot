from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from fastapi import FastAPI
from fastapi.responses import JSONResponse

import uvicorn

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

from bot.handlers.shop import (
    router as shop_router,
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
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="TEYZUS API",
    version="1.0.0",
    description="TEYZUS Telegram Username Platform API",
)


# =========================================================
# ROOT
# =========================================================

@app.get("/")
async def root():
    return JSONResponse(
        {
            "status": "ok",
            "service": "TEYZUS",
            "bot": settings.bot_username,
            "version": "1.0.0",
        }
    )


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
async def health():
    return JSONResponse(
        {
            "status": "healthy",
            "service": "TEYZUS",
        }
    )


# =========================================================
# API STATUS
# =========================================================

@app.get("/api/status")
async def api_status():
    return JSONResponse(
        {
            "success": True,
            "service": "TEYZUS API",
            "bot": settings.bot_username,
            "database": "connected",
        }
    )


# =========================================================
# BOT
# =========================================================

async def create_bot() -> Bot:
    """
    Создаёт Telegram Bot.
    """

    return Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
        ),
    )


# =========================================================
# DISPATCHER
# =========================================================

def create_dispatcher() -> Dispatcher:
    """
    Создаёт Dispatcher и подключает все основные роутеры.
    """

    dispatcher = Dispatcher()

    # -----------------------------------------------------
    # START
    # -----------------------------------------------------

    dispatcher.include_router(
        start_router
    )

    # -----------------------------------------------------
    # MAIN MENU / HUNTER
    # -----------------------------------------------------

    dispatcher.include_router(
        menu_router
    )

    # -----------------------------------------------------
    # PROFILE
    # -----------------------------------------------------

    dispatcher.include_router(
        profile_router
    )

    # -----------------------------------------------------
    # OWNER / ADMIN PROMO
    # -----------------------------------------------------

    dispatcher.include_router(
        admin_promo_router
    )

    return dispatcher
dispatcher.include_router(
    shop_router
)

# =========================================================
# BOT RUNNER
# =========================================================

async def run_bot() -> None:
    """
    Запускает Telegram-бота через long polling.
    """

    bot = await create_bot()

    dispatcher = create_dispatcher()

    logger.info(
        "========================================"
    )

    logger.info(
        "TEYZUS BOT STARTING"
    )

    logger.info(
        "Bot: @%s",
        settings.bot_username,
    )

    logger.info(
        "========================================"
    )

    try:

        # -------------------------------------------------
        # Проверяем токен
        # -------------------------------------------------

        bot_info = await bot.get_me()

        logger.info(
            "Telegram connected: @%s",
            bot_info.username,
        )

        # -------------------------------------------------
        # POLLING
        # -------------------------------------------------

        await dispatcher.start_polling(
            bot,
            allowed_updates=(
                dispatcher.resolve_used_update_types()
            ),
        )

    except asyncio.CancelledError:

        logger.info(
            "Bot polling cancelled."
        )

        raise

    except Exception:

        logger.exception(
            "Fatal error inside Telegram bot."
        )

        raise

    finally:

        # -------------------------------------------------
        # HUNTER
        # -------------------------------------------------

        try:

            await hunter.close()

            logger.info(
                "Hunter closed."
            )

        except Exception:

            logger.exception(
                "Failed to close hunter."
            )

        # -------------------------------------------------
        # BOT SESSION
        # -------------------------------------------------

        try:

            await bot.session.close()

            logger.info(
                "Telegram bot session closed."
            )

        except Exception:

            logger.exception(
                "Failed to close bot session."
            )


# =========================================================
# WEB SERVER
# =========================================================

async def run_web() -> None:
    """
    Запускает FastAPI/Uvicorn.
    """

    logger.info(
        "Starting FastAPI server..."
    )

    logger.info(
        "Host: %s",
        settings.web_host,
    )

    logger.info(
        "Port: %s",
        settings.web_port,
    )

    configuration = uvicorn.Config(
        app,
        host=settings.web_host,
        port=settings.web_port,
        log_level=settings.log_level.lower(),
        access_log=True,
    )

    server = uvicorn.Server(
        configuration
    )

    try:

        await server.serve()

    except asyncio.CancelledError:

        logger.info(
            "Web server cancelled."
        )

        raise


# =========================================================
# APPLICATION STARTUP
# =========================================================

async def startup() -> None:
    """
    Инициализация приложения.
    """

    logger.info(
        "========================================"
    )

    logger.info(
        "TEYZUS STARTUP"
    )

    logger.info(
        "Initializing database..."
    )

    await init_database()

    logger.info(
        "Database initialized successfully."
    )

    logger.info(
        "========================================"
    )


# =========================================================
# APPLICATION SHUTDOWN
# =========================================================

async def shutdown() -> None:
    """
    Корректное завершение приложения.
    """

    logger.info(
        "Shutting down TEYZUS..."
    )

    try:

        await close_database()

        logger.info(
            "Database connection pool closed."
        )

    except Exception:

        logger.exception(
            "Failed to close database."
        )

    logger.info(
        "TEYZUS stopped."
    )


# =========================================================
# MAIN
# =========================================================

async def main() -> None:
    """
    Главная функция приложения.
    """

    await startup()

    try:

        # -------------------------------------------------
        # Одновременно запускаем:
        #
        # 1. Telegram Bot
        # 2. FastAPI
        # -------------------------------------------------

        await asyncio.gather(
            run_bot(),
            run_web(),
        )

    except asyncio.CancelledError:

        logger.info(
            "Main task cancelled."
        )

        raise

    except Exception:

        logger.exception(
            "Fatal TEYZUS error."
        )

        raise

    finally:

        await shutdown()


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
            "TEYZUS stopped by user."
        )
