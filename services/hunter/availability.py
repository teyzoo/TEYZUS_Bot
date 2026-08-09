import asyncio
import logging
from dataclasses import dataclass
from enum import StrEnum

from services.hunter.telegram_checker import (
    TelegramChecker,
    TelegramUsernameStatus,
)

from services.hunter.tme_checker import (
    TMeChecker,
)


logger = logging.getLogger(
    "TEYZUS.availability"
)


class AvailabilityStatus(StrEnum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    INVALID = "invalid"
    UNKNOWN = "unknown"


@dataclass
class AvailabilityResult:

    username: str

    telegram: TelegramUsernameStatus

    tme: bool

    status: AvailabilityStatus

    checked: bool


class AvailabilityEngine:

    def __init__(self) -> None:

        self.telegram = TelegramChecker()
        self.tme = TMeChecker()

        self._lock = asyncio.Lock()

    async def close(self) -> None:

        await self.telegram.close()

    async def check(
        self,
        username: str,
    ) -> AvailabilityResult:

        username = (
            username
            .strip()
            .lstrip("@")
            .lower()
        )

        if not username:

            return AvailabilityResult(
                username=username,
                telegram=(
                    TelegramUsernameStatus.INVALID
                ),
                tme=False,
                status=(
                    AvailabilityStatus.INVALID
                ),
                checked=False,
            )

        async with self._lock:

            telegram_result = (
                await self.telegram.check(
                    username
                )
            )

            # Если Telegram точно показывает,
            # что username занят — дальше можно
            # не тратить запросы.
            if telegram_result == (
                TelegramUsernameStatus.OCCUPIED
            ):

                return AvailabilityResult(
                    username=username,
                    telegram=telegram_result,
                    tme=False,
                    status=(
                        AvailabilityStatus.OCCUPIED
                    ),
                    checked=True,
                )

            if telegram_result == (
                TelegramUsernameStatus.INVALID
            ):

                return AvailabilityResult(
                    username=username,
                    telegram=telegram_result,
                    tme=False,
                    status=(
                        AvailabilityStatus.INVALID
                    ),
                    checked=True,
                )

            # t.me проверяем только если
            # Telegram не подтвердил занятость.
            tme_result = await self.tme.check(
                username
            )

            if telegram_result == (
                TelegramUsernameStatus.AVAILABLE
            ):

                if tme_result:

                    status = (
                        AvailabilityStatus.AVAILABLE
                    )

                else:

                    status = (
                        AvailabilityStatus.UNKNOWN
                    )

            elif telegram_result == (
                TelegramUsernameStatus.FLOOD_WAIT
            ):

                status = (
                    AvailabilityStatus.UNKNOWN
                )

            else:

                status = (
                    AvailabilityStatus.UNKNOWN
                )

            return AvailabilityResult(
                username=username,
                telegram=telegram_result,
                tme=tme_result,
                status=status,
                checked=True,
            )

    async def check_many(
        self,
        usernames: list[str],
        concurrency: int = 5,
    ) -> list[AvailabilityResult]:

        semaphore = asyncio.Semaphore(
            concurrency
        )

        async def worker(
            username: str,
        ) -> AvailabilityResult:

            async with semaphore:

                return await self.check(
                    username
                )

        tasks = [
            asyncio.create_task(
                worker(username)
            )
            for username in usernames
        ]

        if not tasks:
            return []

        return await asyncio.gather(
            *tasks
        )

    async def available_only(
        self,
        usernames: list[str],
        concurrency: int = 5,
    ) -> list[str]:

        results = await self.check_many(
            usernames,
            concurrency=concurrency,
        )

        return [
            result.username
            for result in results
            if result.status
            == AvailabilityStatus.AVAILABLE
        ]
