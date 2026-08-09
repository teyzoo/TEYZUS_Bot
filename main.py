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
            "service": "TEYZUS",
        }
    )


@app.get("/api/health")
async def api_health():
    return JSONResponse(
        {
            "status": "ok",
            "database": "connected",
            "service": "TEYZUS API",
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
    # ROUTERS
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
    # OWNER / ADMIN
    # =====================================================

    dispatcher.include_router(
        admin_promo_router
    )

    logger.info(
        "========================================"
    )

    logger.info(
        "TEYZUS BOT STARTING"
    )

    logger.info(
        "Bot username: %s",
        settings.bot_username,
    )

    logger.info(
        "========================================"
    )

    try:
        await dispatcher.start_polling(
            bot,
            allowed_updates=(
                dispatcher.resolve_used_update_types()
            ),
        )

    except Exception:
        logger.exception(
            "Bot polling crashed."
        )
        raise

    finally:
        logger.info(
            "Closing username hunter..."
        )

        try:
            await hunter.close()
        except Exception:
            logger.exception(
                "Failed to close hunter."
            )

        logger.info(
            "Closing Telegram bot session..."
        )

        try:
            await bot.session.close()
        except Exception:
            logger.exception(
                "Failed to close bot session."
            )

        logger.info(
            "TEYZUS BOT STOPPED"
        )


# =========================================================
# WEB SERVER
# =========================================================

async def run_web() -> None:
    logger.info(
        "Starting FastAPI server..."
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

    except Exception:
        logger.exception(
            "FastAPI server crashed."
        )
        raise

    finally:
        logger.info(
            "FastAPI server stopped."
        )


# =========================================================
# MAIN
# =========================================================

async def main() -> None:
    logger.info(
        "========================================"
    )

    logger.info(
        "TEYZUS INITIALIZATION"
    )

    logger.info(
        "========================================"
    )

    # =====================================================
    # DATABASE
    # =====================================================

    logger.info(
        "Initializing database..."
    )

    try:
        await init_database()

    except Exception:
        logger.exception(
            "Database initialization failed."
        )
        raise

    logger.info(
        "Database initialized successfully."
    )

    # =====================================================
    # RUN BOT + WEB
    # =====================================================

    logger.info(
        "Starting TEYZUS services..."
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

        try:
            await close_database()
        except Exception:
            logger.exception(
                "Failed to close database."
            )

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
            "TEYZUS stopped by user."
        )

    except Exception:
        logger.exception(
            "TEYZUS stopped because of an unexpected error."
        )
        raise
