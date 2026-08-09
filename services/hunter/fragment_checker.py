from __future__ import annotations

import asyncio
from enum import StrEnum
from typing import Optional

import aiohttp


class FragmentUsernameStatus(StrEnum):
    AVAILABLE = "available"
    TAKEN = "taken"
    FOR_SALE = "for_sale"
    AUCTION = "auction"
    UNKNOWN = "unknown"
    ERROR = "error"


class FragmentChecker:
    """
    Проверка username через Fragment.

    ВАЖНО:
    Fragment не предоставляет простой публичный API,
    поэтому этот класс изолирован от остального Hunter Engine.

    Если способ проверки Fragment изменится,
    достаточно заменить код внутри этого класса.
    """

    BASE_URL = "https://fragment.com/username/{}"

    REQUEST_TIMEOUT = 10

    MAX_RETRIES = 2

    RETRY_DELAY = 0.5

    def __init__(
        self,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> None:

        self._external_session = (
            session is not None
        )

        self.session = session

    async def _get_session(
        self,
    ) -> aiohttp.ClientSession:

        if self.session is None:

            timeout = aiohttp.ClientTimeout(
                total=self.REQUEST_TIMEOUT
            )

            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 "
                        "(iPhone; CPU iPhone OS 17_0 "
                        "like Mac OS X) "
                        "AppleWebKit/605.1.15 "
                        "(KHTML, like Gecko) "
                        "Version/17.0 Mobile/15E148 "
                        "Safari/604.1"
                    ),
                    "Accept": (
                        "text/html,"
                        "application/xhtml+xml,"
                        "application/xml;q=0.9,"
                        "image/avif,"
                        "image/webp,"
                        "*/*;q=0.8"
                    ),
                    "Accept-Language": (
                        "en-US,en;q=0.9"
                    ),
                },
            )

        return self.session

    @staticmethod
    def normalize(
        username: str,
    ) -> str:

        username = username.strip().lower()

        if username.startswith("@"):
            username = username[1:]

        return username

    @staticmethod
    def validate_username(
        username: str,
    ) -> bool:

        username = FragmentChecker.normalize(
            username
        )

        if not 5 <= len(username) <= 32:
            return False

        return username.replace(
            "_",
            ""
        ).isalnum()

    async def fetch(
        self,
        username: str,
    ) -> tuple[
        FragmentUsernameStatus,
        Optional[str],
    ]:

        username = self.normalize(
            username
        )

        if not self.validate_username(
            username
        ):

            return (
                FragmentUsernameStatus.ERROR,
                None,
            )

        url = self.BASE_URL.format(
            username
        )

        session = await self._get_session()

        for attempt in range(
            self.MAX_RETRIES + 1
        ):

            try:

                async with session.get(
                    url,
                    allow_redirects=True,
                ) as response:

                    if response.status == 404:

                        return (
                            FragmentUsernameStatus.AVAILABLE,
                            None,
                        )

                    if response.status == 429:

                        if (
                            attempt
                            < self.MAX_RETRIES
                        ):

                            await asyncio.sleep(
                                self.RETRY_DELAY
                                * (
                                    attempt + 1
                                )
                            )

                            continue

                        return (
                            FragmentUsernameStatus.ERROR,
                            "rate_limited",
                        )

                    if response.status >= 500:

                        if (
                            attempt
                            < self.MAX_RETRIES
                        ):

                            await asyncio.sleep(
                                self.RETRY_DELAY
                                * (
                                    attempt + 1
                                )
                            )

                            continue

                        return (
                            FragmentUsernameStatus.ERROR,
                            f"http_{response.status}",
                        )

                    if response.status != 200:

                        return (
                            FragmentUsernameStatus.UNKNOWN,
                            f"http_{response.status}",
                        )

                    html = await response.text(
                        errors="ignore"
                    )

                    status = self.detect_status(
                        html
                    )

                    return (
                        status,
                        None,
                    )

            except asyncio.TimeoutError:

                if (
                    attempt
                    < self.MAX_RETRIES
                ):

                    await asyncio.sleep(
                        self.RETRY_DELAY
                        * (
                            attempt + 1
                        )
                    )

                    continue

                return (
                    FragmentUsernameStatus.ERROR,
                    "timeout",
                )

            except aiohttp.ClientError as error:

                if (
                    attempt
                    < self.MAX_RETRIES
                ):

                    await asyncio.sleep(
                        self.RETRY_DELAY
                        * (
                            attempt + 1
                        )
                    )

                    continue

                return (
                    FragmentUsernameStatus.ERROR,
                    str(error),
                )

            except Exception as error:

                return (
                    FragmentUsernameStatus.ERROR,
                    str(error),
                )

        return (
            FragmentUsernameStatus.ERROR,
            "unknown_error",
        )

    @staticmethod
    def detect_status(
        html: str,
    ) -> FragmentUsernameStatus:

        text = html.lower()

        # =================================================
        # FOR SALE
        # =================================================

        sale_markers = (
            "for sale",
            "buy username",
            "place a bid",
            "make an offer",
        )

        if any(
            marker in text
            for marker in sale_markers
        ):

            return (
                FragmentUsernameStatus.FOR_SALE
            )

        # =================================================
        # AUCTION
        # =================================================

        auction_markers = (
            "auction",
            "highest bid",
            "current bid",
            "place bid",
        )

        if any(
            marker in text
            for marker in auction_markers
        ):

            return (
                FragmentUsernameStatus.AUCTION
            )

        # =================================================
        # TAKEN / OWNED
        # =================================================

        taken_markers = (
            "owned",
            "not available",
            "unavailable",
            "username is taken",
        )

        if any(
            marker in text
            for marker in taken_markers
        ):

            return (
                FragmentUsernameStatus.TAKEN
            )

        # =================================================
        # AVAILABLE
        # =================================================

        available_markers = (
            "available",
            "claim username",
            "create username",
        )

        if any(
            marker in text
            for marker in available_markers
        ):

            return (
                FragmentUsernameStatus.AVAILABLE
            )

        return (
            FragmentUsernameStatus.UNKNOWN
        )

    async def check(
        self,
        username: str,
    ) -> bool:

        status, _ = await self.fetch(
            username
        )

        return (
            status
            == FragmentUsernameStatus.AVAILABLE
        )

    async def check_detailed(
        self,
        username: str,
    ) -> FragmentUsernameStatus:

        status, _ = await self.fetch(
            username
        )

        return status

    async def close(self) -> None:

        if (
            self.session is not None
            and not self._external_session
        ):

            if not self.session.closed:

                await self.session.close()

            self.session = None
