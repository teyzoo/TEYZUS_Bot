from __future__ import annotations

import asyncio
import logging
import sys
from contextlib import asynccontextmanager

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
# FASTAPI LIFESPAN
# =========================================================

@asynccontextmanager
async def lifespan(
    fastapi_app: FastAPI,
):
    """
    Жизненный цикл FastAPI.

    При запуске:
        - база уже инициализируется
          в main()

    При остановке:
        - закрываем соединения БД.
    """

    logger.info(
        "FastAPI application started."
    )

    try:
        yield

    finally:
        logger.info(
            "FastAPI application stopping..."
        )


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="TEYZUS API",
    version="1.0.0",
    lifespan=lifespan,
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
            "version": "1.0.0",
            "bot": settings.bot_username,
        }
    )


# =========================================================
# HEALTH
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
            "status": "ok",
            "service": "TEYZUS API",
            "bot": settings.bot_username,
        }
    )


# =========================================================
# BOT
# =========================================================

async def run_bot() -> None:
    """
    Запускает Telegram-бота.
    """

    logger.info(
        "Creating Telegram Bot..."
    )

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
        ),
    )

    dispatcher = Dispatcher()

    # =====================================================
    # ROUTERS
    # =====================================================

    logger.info(
        "Registering Telegram routers..."
    )

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

    logger.info(
        "Telegram routers registered."
    )

    # =====================================================
    # START POLLING
    # =====================================================

    logger.info(
        "TEYZUS Bot starting..."
    )

    logger.info(
        "Bot username: %s",
        settings.bot_username,
    )

    try:
        await dispatcher.start_polling(
            bot,
            allowed_updates=(
                dispatcher.resolve_used_update_types()
            ),
        )

    except asyncio.CancelledError:

        logger.info(
            "Telegram polling cancelled."
        )

        raise

    except Exception:

        logger.exception(
            "Telegram bot crashed."
        )

        raise

    finally:

        # =================================================
        # CLOSE HUNTER
        # =================================================

        try:
            await hunter.close()

            logger.info(
                "Hunter closed."
            )

        except Exception:

            logger.exception(
                "Failed to close hunter."
            )

        # =================================================
        # CLOSE BOT SESSION
        # =================================================

        try:
            await bot.session.close()

            logger.info(
                "Telegram bot session closed."
            )

        except Exception:

            logger.exception(
                "Failed to close Telegram session."
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

    except Exception:

        logger.exception(
            "FastAPI server crashed."
        )

        raise


# =========================================================
# MAIN
# =========================================================

async def main() -> None:
    """
    Главная точка запуска TEYZUS.

    Запускает одновременно:

        1. PostgreSQL
           └── SQLAlchemy

        2. Telegram Bot
           └── Aiogram

        3. FastAPI
           └── Mini App / API
    """

    logger.info(
        "=================================================="
    )

    logger.info(
        "TEYZUS STARTING"
    )

    logger.info(
        "=================================================="
    )

    # =====================================================
    # DATABASE
    # =====================================================

    logger.info(
        "Initializing database..."
    )

    try:

        await init_database()

        logger.info(
            "Database initialized successfully."
        )

    except Exception:

        logger.exception(
            "Database initialization failed."
        )

        raise

    # =====================================================
    # START BOT + WEB
    # =====================================================

    logger.info(
        "Starting TEYZUS services..."
    )

    try:

        await asyncio.gather(
            run_bot(),
            run_web(),
        )

    except asyncio.CancelledError:

        logger.info(
            "TEYZUS services cancelled."
        )

        raise

    except Exception:

        logger.exception(
            "One of TEYZUS services crashed."
        )

        raise

    finally:

        # =================================================
        # DATABASE CLOSE
        # =================================================

        logger.info(
            "Closing database..."
        )

        try:

            await close_database()

            logger.info(
                "Database closed."
            )

        except Exception:

            logger.exception(
                "Failed to close database."
            )

        logger.info(
            "=================================================="
        )

        logger.info(
            "TEYZUS STOPPED"
        )

        logger.info(
            "==================================================")


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
            "TEYZUS stopped by keyboard interrupt."
        )

    except Exception:

        logger.exception(
            "TEYZUS terminated with an unexpected error."
        )

        sys.exit(1)
