import asyncio
import logging
import sys

from aiogram import (
    Bot,
    Dispatcher,
)

from aiogram.client.default import (
    DefaultBotProperties,
)

from aiogram.enums import (
    ParseMode,
)

from fastapi import (
    FastAPI,
)

from fastapi.responses import (
    JSONResponse,
)

import uvicorn

from config import settings

from database.session import (
    init_database,
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

from bot.handlers.cases import (
    router as cases_router,
)

from bot.handlers.admin_cases import (
    router as admin_cases_router,
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

logger = logging.getLogger(
    "TEYZUS"
)


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
    # MAIN
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
    # CASES
    # =====================================================

    dispatcher.include_router(
        cases_router
    )

    # =====================================================
    # OWNER
    # =====================================================

    dispatcher.include_router(
        admin_promo_router
    )

    dispatcher.include_router(
        admin_cases_router
    )

    logger.info(
        "TEYZUS Bot starting..."
    )

    try:

        await dispatcher.start_polling(
            bot,
            allowed_updates=(
                dispatcher
                .resolve_used_update_types()
            ),
        )

    finally:

        await hunter.close()

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

    await asyncio.gather(
        run_bot(),
        run_web(),
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
