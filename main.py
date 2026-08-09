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
    # START
    # =====================================================

    dispatcher.include_router(
        start_router
    )

    # =====================================================
    # MENU / HUNTER
    # =====================================================

    dispatcher.include_router(
        menu_router
    )

    # =====================================================
    # PROFILE
    # =====================================================

    dispatcher.include_router(
        profile_router
    )

    # =====================================================
    # ADMIN / PROMO
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
        "Bot: @%s",
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
            "TEYZUS Bot crashed"
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
                "Failed to close hunter"
            )

        logger.info(
            "Closing Telegram bot session..."
        )

        try:
            await bot.session.close()

        except Exception:

            logger.exception(
                "Failed to close bot session"
            )

        logger.info(
            "TEYZUS Bot stopped."
        )


# =========================================================
# WEB SERVER
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

    await server.serve()


# =========================================================
# APPLICATION STARTUP
# =========================================================

async def startup() -> None:

    logger.info(
        "========================================"
    )

    logger.info(
        "TEYZUS INITIALIZATION"
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

    logger.info(
        "========================================"
    )

    logger.info(
        "TEYZUS SHUTDOWN"
    )

    logger.info(
        "Closing database..."
    )

    try:

        await close_database()

        logger.info(
            "Database closed successfully."
        )

    except Exception:

        logger.exception(
            "Failed to close database"
        )

    logger.info(
        "========================================"
    )


# =========================================================
# MAIN
# =========================================================

async def main() -> None:

    await startup()

    try:

        await asyncio.gather(
            run_bot(),
            run_web(),
        )

    except asyncio.CancelledError:

        logger.info(
            "TEYZUS tasks cancelled."
        )

        raise

    except Exception:

        logger.exception(
            "TEYZUS application crashed."
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

    except Exception:

        logger.exception(
            "Fatal TEYZUS error."
        )

        sys.exit(1)
