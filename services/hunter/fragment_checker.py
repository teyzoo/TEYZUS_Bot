from __future__ import annotations

import asyncio
from typing import Optional

import aiohttp


class FragmentChecker:
    """
    Проверка username через Fragment.

    Важно:
    Fragment не предоставляет нам здесь гарантированный
    официальный публичный API для проверки доступности,
    поэтому checker работает через HTTP и не считает
    результат достоверным при ошибке сети.

    При любой ошибке возвращается None.
    """

    BASE_URL = "https://fragment.com/username/"

    def __init__(
        self,
        timeout: float = 10.0,
        max_concurrency: int = 5,
    ) -> None:

        self.timeout = timeout

        self.semaphore = asyncio.Semaphore(
            max_concurrency
        )

    # =====================================================
    # NORMALIZE
    # =====================================================

    @staticmethod
    def normalize(
        username: str,
    ) -> str:

        username = username.strip().lower()

        if username.startswith("@"):
            username = username[1:]

        return username

    # =====================================================
    # URL
    # =====================================================

    def build_url(
        self,
        username: str,
    ) -> str:

        username = self.normalize(
            username
        )

        return (
            f"{self.BASE_URL}"
            f"{username}"
        )

    # =====================================================
    # CHECK
    # =====================================================

    async def check(
        self,
        username: str,
    ) -> Optional[bool]:

        username = self.normalize(
            username
        )

        if not username:
            return None

        url = self.build_url(
            username
        )

        timeout = aiohttp.ClientTimeout(
            total=self.timeout
        )

        async with self.semaphore:

            try:

                async with aiohttp.ClientSession(
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
                        "Accept-Language": "en-US,en;q=0.9",
                    },
                ) as session:

                    async with session.get(
                        url,
                        allow_redirects=True,
                    ) as response:

                        if response.status != 200:
                            return None

                        html = await response.text()

            except (
                asyncio.TimeoutError,
                aiohttp.ClientError,
            ):

                return None

            except Exception:

                return None

        return self._parse_response(
            html
        )

    # =====================================================
    # PARSE
    # =====================================================

    @staticmethod
    def _parse_response(
        html: str,
    ) -> Optional[bool]:

        if not html:
            return None

        html_lower = html.lower()

        # -------------------------------------------------
        # AVAILABLE
        # -------------------------------------------------

        available_markers = (
            "username is available",
            "buy username",
            "place a bid",
            "this username is available",
        )

        for marker in available_markers:

            if marker in html_lower:

                return True

        # -------------------------------------------------
        # TAKEN
        # -------------------------------------------------

        taken_markers = (
            "username is taken",
            "username unavailable",
            "already taken",
            "not available",
        )

        for marker in taken_markers:

            if marker in html_lower:

                return False

        # -------------------------------------------------
        # UNKNOWN
        # -------------------------------------------------

        return None


# =========================================================
# SINGLETON
# =========================================================

fragment_checker = FragmentChecker()
