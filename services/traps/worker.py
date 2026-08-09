from __future__ import annotations

import asyncio
import logging

from aiogram import Bot

from database.repositories import (
    get_active_traps,
    mark_trap_triggered,
    update_last_checked,
)
from database.session import async_session_factory

from services.hunter.telegram_checker import (
    TelegramChecker,
    TelegramUsernameStatus,
)
from services.hunter.tme_checker import (
    TMeChecker,
)


logger = logging.getLogger(__name__)


class TrapWorker:

    def __init__(
        self,
        bot: Bot,
        interval: int = 30,
    ) -> None:

        self.bot = bot
        self.interval = interval

        self.telegram = TelegramChecker()
        self.tme = TMeChecker()

        self._task: asyncio.Task | None = None
        self._running = False

    # =====================================================
    # START
    # =====================================================

    async def start(self) -> None:

        if self._running:
            return

        self._running = True

        self._task = asyncio.create_task(
            self._run()
        )

        logger.info(
            "TrapWorker started"
        )

    # =====================================================
    # STOP
    # =====================================================

    async def stop(self) -> None:

        self._running = False

        if self._task is not None:

            self._task.cancel()

            try:
                await self._task

            except asyncio.CancelledError:
                pass

            self._task = None

        await self.telegram.close()

        logger.info(
            "TrapWorker stopped"
        )

    # =====================================================
    # MAIN LOOP
    # =====================================================

    async def _run(self) -> None:

        while self._running:

            try:

                await self.check_all()

            except asyncio.CancelledError:

                raise

            except Exception:

                logger.exception(
                    "TrapWorker error"
                )

            await asyncio.sleep(
                self.interval
            )

    # =====================================================
    # CHECK ALL
    # =====================================================

    async def check_all(self) -> None:

        async with async_session_factory() as session:

            traps = await get_active_traps(
                session=session
            )

            if not traps:
                return

            logger.info(
                "Checking %s active traps",
                len(traps),
            )

            for trap in traps:

                if not trap.is_active:
                    continue

                try:

                    await self.check_trap(
                        trap
                    )

                except Exception:

                    logger.exception(
                        "Trap check failed: %s",
                        trap.username,
                    )

    # =====================================================
    # CHECK ONE TRAP
    # =====================================================

    async def check_trap(
        self,
        trap,
    ) -> None:

        username = trap.username

        logger.info(
            "Checking trap @%s",
            username,
        )

        # -------------------------------------------------
        # TELEGRAM
        # -------------------------------------------------

        telegram_status = (
            await self.telegram.check(
                username
            )
        )

        # Username всё ещё занят
        if (
            telegram_status
            != TelegramUsernameStatus.AVAILABLE
        ):

            async with async_session_factory() as session:

                fresh_trap = await session.get(
                    type(trap),
                    trap.id,
                )

                if fresh_trap is not None:

                    await update_last_checked(
                        session=session,
                        trap=fresh_trap,
                    )

            return

        # -------------------------------------------------
        # T.ME
        # -------------------------------------------------

        tme_available = await self.tme.check(
            username
        )

        if not tme_available:

            async with async_session_factory() as session:

                fresh_trap = await session.get(
                    type(trap),
                    trap.id,
                )

                if fresh_trap is not None:

                    await update_last_checked(
                        session=session,
                        trap=fresh_trap,
                    )

            return

        # -------------------------------------------------
        # USERNAME IS AVAILABLE
        # -------------------------------------------------

        async with async_session_factory() as session:

            fresh_trap = await session.get(
                type(trap),
                trap.id,
            )

            if fresh_trap is None:
                return

            if not fresh_trap.is_active:
                return

            await mark_trap_triggered(
                session=session,
                trap=fresh_trap,
            )

        # -------------------------------------------------
        # NOTIFY USER
        # -------------------------------------------------

        await self.notify_user(
            telegram_id=trap.telegram_id,
            username=username,
        )

        logger.info(
            "Trap triggered: @%s -> %s",
            username,
            trap.telegram_id,
        )

    # =====================================================
    # NOTIFICATION
    # =====================================================

    async def notify_user(
        self,
        telegram_id: int,
        username: str,
    ) -> None:

        text = (
            "🚨 <b>USERNAME ОСВОБОДИЛСЯ!</b>\n\n"
            f"👤 Username: "
            f"<code>@{username}</code>\n\n"
            "🟢 Telegram: доступен\n"
            "🟢 t.me: доступен\n\n"
            "⚡ Успей зарегистрировать его "
            "как можно быстрее."
        )

        try:

            await self.bot.send_message(
                chat_id=telegram_id,
                text=text,
                parse_mode="HTML",
            )

        except Exception:

            logger.exception(
                "Failed to notify user %s",
                telegram_id,
            )


trap_worker: TrapWorker | None = None


def create_trap_worker(
    bot: Bot,
) -> TrapWorker:

    global trap_worker

    trap_worker = TrapWorker(
        bot=bot,
        interval=30,
    )

    return trap_worker
