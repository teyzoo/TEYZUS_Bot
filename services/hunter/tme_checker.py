from __future__ import annotations

import asyncio
from typing import Optional

import aiohttp


# =========================================================
# CONSTANTS
# =========================================================

BASE_URL = "https://t.me/"

DEFAULT_TIMEOUT = 10.0
DEFAULT_CONCURRENCY = 20


# =========================================================
# CHECKER
# =========================================================

class TMeChecker:

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT,
        max_concurrency: int = DEFAULT_CONCURRENCY,
    ) -> None:

        self.timeout = timeout

        self.semaphore = asyncio.Semaphore(
            max(
                1,
                max_concurrency,
            )
        )

        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 "
                "(iPhone; CPU iPhone OS 17_0 like Mac OS X) "
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
                "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"
            ),
        }

    # =====================================================
    # NORMALIZE
    # =====================================================

    @staticmethod
    def normalize(
        username: str,
    ) -> str:

        username = username.strip()

        if username.startswith("@"):
            username = username[1:]

        if username.startswith(
            "https://t.me/"
        ):
            username = username[
                len("https://t.me/"):
            ]

        if username.startswith(
            "http://t.me/"
        ):
            username = username[
                len("http://t.me/"):
            ]

        return username.lower()

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
            f"{BASE_URL}"
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
                    headers=self.headers,
                ) as session:

                    async with session.get(
                        url,
                        allow_redirects=True,
                    ) as response:

                        html = await response.text()

                        return self._parse_response(
                            status=response.status,
                            html=html,
                            final_url=str(
                                response.url
                            ),
                        )

            except asyncio.CancelledError:

                raise

            except (
                asyncio.TimeoutError,
                aiohttp.ClientError,
            ):

                return None

            except Exception:

                return None

    # =====================================================
    # PARSE
    # =====================================================

    @staticmethod
    def _parse_response(
        status: int,
        html: str,
        final_url: str,
    ) -> Optional[bool]:

        if not html:
            return None

        text = html.lower()

        # -------------------------------------------------
        # USERNAME DOES NOT EXIST
        # -------------------------------------------------

        unavailable_markers = (
            "if you have telegram",
            "this username is not available",
            "username is not occupied",
            "username not found",
            "page not found",
        )

        for marker in unavailable_markers:

            if marker in text:

                return True

        # -------------------------------------------------
        # EXISTING PROFILE / CHANNEL
        # -------------------------------------------------

        occupied_markers = (
            "tgme_page_title",
            "tgme_page_extra",
            "tgme_page_photo",
            "tgme_page_description",
            "tgme_action_web_button",
        )

        for marker in occupied_markers:

            if marker in text:

                return False

        # -------------------------------------------------
        # HTTP 404
        # -------------------------------------------------

        if status == 404:

            return True

        # -------------------------------------------------
        # HTTP 429 / SERVER ERRORS
        # -------------------------------------------------

        if status == 429:

            return None

        if status >= 500:

            return None

        # -------------------------------------------------
        # REDIRECT
        # -------------------------------------------------

        if (
            final_url
            and "/+" not in final_url
        ):

            # Сам по себе redirect недостаточен,
            # поэтому не делаем предположение.
            pass

        # -------------------------------------------------
        # UNKNOWN
        # -------------------------------------------------

        return None


# =========================================================
# SINGLETON
# =========================================================

tme_checker = TMeChecker()


# =========================================================
# PUBLIC FUNCTION
# =========================================================

async def check_tme(
    username: str,
) -> bool:

    result = await tme_checker.check(
        username
    )

    return result is True
