import asyncio
from typing import Iterable

import aiohttp


class HTTPUsernameChecker:

    def __init__(
        self,
        timeout_seconds: int = 5,
        concurrency: int = 50,
    ) -> None:

        self.timeout = aiohttp.ClientTimeout(
            total=timeout_seconds
        )

        self.concurrency = concurrency

        self.session: aiohttp.ClientSession | None = None

        self._semaphore = asyncio.Semaphore(
            concurrency
        )

    async def start(self) -> None:

        if self.session is None:
            self.session = aiohttp.ClientSession(
                timeout=self.timeout,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 "
                        "(compatible; TEYZUS/1.0)"
                    )
                },
            )

    async def close(self) -> None:

        if self.session is not None:

            await self.session.close()

            self.session = None

    async def check(
        self,
        username: str,
    ) -> bool:

        username = (
            username
            .strip()
            .lstrip("@")
            .lower()
        )

        if not username:
            return False

        await self.start()

        if self.session is None:
            return False

        url = f"https://t.me/{username}"

        async with self._semaphore:

            try:

                async with self.session.get(
                    url,
                    allow_redirects=True,
                ) as response:

                    if response.status == 404:
                        return True

                    if response.status == 200:
                        return False

                    return False

            except (
                asyncio.TimeoutError,
                aiohttp.ClientError,
            ):

                return False

            except Exception:

                return False

    async def check_many(
        self,
        usernames: Iterable[str],
    ) -> list[tuple[str, bool]]:

        usernames = list(usernames)

        if not usernames:
            return []

        await self.start()

        async def worker(
            username: str,
        ) -> tuple[str, bool]:

            result = await self.check(
                username
            )

            return username, result

        tasks = [
            asyncio.create_task(
                worker(username)
            )
            for username in usernames
        ]

        return await asyncio.gather(
            *tasks
        )
