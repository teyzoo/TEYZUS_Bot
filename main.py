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

from database.session import init_database

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

from bot.handlers.hunter import (
    router as hunter_router,
)


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


async def run_bot() -> None:

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
        ),
    )

    dispatcher = Dispatcher()

    dispatcher.include_router(
        start_router
    )

    dispatcher.include_router(
        menu_router
    )

    dispatcher.include_router(
        profile_router
    )

    dispatcher.include_router(
        hunter_router
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

        await hunter.close()

        await bot.session.close()


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


if __name__ == "__main__":

    try:

        asyncio.run(main())

    except KeyboardInterrupt:

        logger.info(
            "TEYZUS stopped."
        )
