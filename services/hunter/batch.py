import asyncio
from dataclasses import dataclass

from services.hunter.http_checker import (
    HTTPUsernameChecker,
)
from services.hunter.telegram_checker import (
    TelegramChecker,
    TelegramUsernameStatus,
)


@dataclass
class BatchCheckResult:
    username: str
    telegram: TelegramUsernameStatus
    tme_available: bool
    available: bool


class BatchHunterChecker:

    def __init__(
        self,
        concurrency: int = 20,
    ) -> None:

        self.telegram = TelegramChecker()

        self.http = HTTPUsernameChecker(
            concurrency=concurrency
        )

        self.concurrency = concurrency

    async def start(self) -> None:

        await self.http.start()

        await self.telegram.connect()

    async def close(self) -> None:

        await self.telegram.close()

        await self.http.close()

    async def check_one(
        self,
        username: str,
    ) -> BatchCheckResult:

        username = (
            username
            .strip()
            .lstrip("@")
            .lower()
        )

        telegram_status = (
            await self.telegram.check(
                username
            )
        )

        if telegram_status == (
            TelegramUsernameStatus.OCCUPIED
        ):

            return BatchCheckResult(
                username=username,
                telegram=telegram_status,
                tme_available=False,
                available=False,
            )

        if telegram_status == (
            TelegramUsernameStatus.INVALID
        ):

            return BatchCheckResult(
                username=username,
                telegram=telegram_status,
                tme_available=False,
                available=False,
            )

        tme_available = await self.http.check(
            username
        )

        available = (
            telegram_status
            == TelegramUsernameStatus.AVAILABLE
            and tme_available
        )

        return BatchCheckResult(
            username=username,
            telegram=telegram_status,
            tme_available=tme_available,
            available=available,
        )

    async def check_many(
        self,
        usernames: list[str],
    ) -> list[BatchCheckResult]:

        if not usernames:
            return []

        await self.start()

        semaphore = asyncio.Semaphore(
            self.concurrency
        )

        async def worker(
            username: str,
        ) -> BatchCheckResult:

            async with semaphore:

                return await self.check_one(
                    username
                )

        tasks = [
            asyncio.create_task(
                worker(username)
            )
            for username in usernames
        ]

        return await asyncio.gather(
            *tasks
        )

    async def available(
        self,
        usernames: list[str],
    ) -> list[str]:

        results = await self.check_many(
            usernames
        )

        return [
            result.username
            for result in results
            if result.available
        ]
