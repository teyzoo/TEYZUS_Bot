from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Iterable

from services.hunter.telegram_checker import (
    check_telegram,
)
from services.hunter.tme_checker import (
    check_tme,
)


# =========================================================
# RESULT
# =========================================================

@dataclass(slots=True)
class HunterResult:
    username: str

    telegram_available: bool
    tme_available: bool
    fragment_available: bool

    beauty_score: float = 0.0
    readability: float = 0.0
    rarity: float = 0.0
    liquidity: float = 0.0
    brand: float = 0.0

    price_min: int = 0
    price_max: int = 0

    @property
    def available(self) -> bool:
        return (
            self.telegram_available
            and self.tme_available
        )


# =========================================================
# ENGINE
# =========================================================

class HunterEngine:

    def __init__(
        self,
        max_concurrency: int = 20,
    ) -> None:

        self.max_concurrency = max(
            1,
            max_concurrency,
        )

        self.semaphore = asyncio.Semaphore(
            self.max_concurrency
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
    # VALID USERNAME
    # =====================================================

    @staticmethod
    def valid_username(
        username: str,
    ) -> bool:

        if not username:
            return False

        if len(username) < 5:
            return False

        if len(username) > 32:
            return False

        for char in username:

            if not (
                char.isascii()
                and (
                    char.isalpha()
                    or char.isdigit()
                    or char == "_"
                )
            ):
                return False

        return True

    # =====================================================
    # PREPARE CANDIDATES
    # =====================================================

    def prepare_candidates(
        self,
        length: int,
        amount: int,
    ) -> list[str]:

        from services.hunter.generator import (
            generate_candidates,
        )

        candidates = generate_candidates(
            length=length,
            limit=amount,
        )

        result: list[str] = []

        seen: set[str] = set()

        for username in candidates:

            username = self.normalize(
                username
            )

            if not self.valid_username(
                username
            ):
                continue

            if len(username) != length:
                continue

            if username in seen:
                continue

            seen.add(username)

            result.append(username)

        return result

    # =====================================================
    # CHECK TELEGRAM
    # =====================================================

    async def _check_telegram(
        self,
        username: str,
    ) -> bool:

        async with self.semaphore:

            try:

                result = await check_telegram(
                    username
                )

                return bool(result)

            except Exception:

                return False

    # =====================================================
    # CHECK T.ME
    # =====================================================

    async def _check_tme(
        self,
        username: str,
    ) -> bool:

        async with self.semaphore:

            try:

                result = await check_tme(
                    username
                )

                return bool(result)

            except Exception:

                return False

    # =====================================================
    # CHECK FRAGMENT
    # =====================================================

    async def _check_fragment(
        self,
        username: str,
    ) -> bool:

        # Fragment checker подключим отдельно.
        #
        # Пока возвращаем True, чтобы отсутствие
        # отдельного Fragment checker не ломало Hunter.
        #
        # После подключения реального Fragment API
        # этот метод заменим.

        return True

    # =====================================================
    # CHECK ONE CANDIDATE
    # =====================================================

    async def check_candidate(
        self,
        username: str,
    ) -> HunterResult | None:

        username = self.normalize(
            username
        )

        if not self.valid_username(
            username
        ):
            return None

        telegram_task = asyncio.create_task(
            self._check_telegram(
                username
            )
        )

        tme_task = asyncio.create_task(
            self._check_tme(
                username
            )
        )

        fragment_task = asyncio.create_task(
            self._check_fragment(
                username
            )
        )

        (
            telegram_available,
            tme_available,
            fragment_available,
        ) = await asyncio.gather(
            telegram_task,
            tme_task,
            fragment_task,
        )

        if not telegram_available:
            return None

        if not tme_available:
            return None

        if not fragment_available:
            return None

        result = HunterResult(
            username=username,

            telegram_available=(
                telegram_available
            ),

            tme_available=(
                tme_available
            ),

            fragment_available=(
                fragment_available
            ),
        )

        self._calculate_scores(
            result
        )

        self._calculate_price(
            result
        )

        return result

    # =====================================================
    # CHECK MANY
    # =====================================================

    async def check_many(
        self,
        candidates: Iterable[str],
        amount: int,
    ) -> list[HunterResult]:

        candidates = list(
            candidates
        )

        if not candidates:
            return []

        tasks = [
            asyncio.create_task(
                self.check_candidate(
                    username
                )
            )
            for username in candidates
        ]

        results: list[HunterResult] = []

        for task in asyncio.as_completed(
            tasks
        ):

            try:

                result = await task

            except asyncio.CancelledError:

                raise

            except Exception:

                continue

            if result is None:
                continue

            results.append(
                result
            )

            if len(results) >= amount:

                for pending in tasks:

                    if not pending.done():

                        pending.cancel()

                break

        if results:

            await asyncio.gather(
                *tasks,
                return_exceptions=True,
            )

        return results[:amount]

    # =====================================================
    # SCORE
    # =====================================================

    @staticmethod
    def _calculate_scores(
        result: HunterResult,
    ) -> None:

        username = result.username

        length = len(username)

        # -------------------------------------------------
        # READABILITY
        # -------------------------------------------------

        readability = 5.0

        if username.isalpha():

            readability += 2.0

        if username.islower():

            readability += 0.5

        if "_" not in username:

            readability += 0.5

        if not any(
            char.isdigit()
            for char in username
        ):

            readability += 1.0

        result.readability = min(
            readability,
            10.0,
        )

        # -------------------------------------------------
        # RARITY
        # -------------------------------------------------

        rarity = 4.0

        if length == 5:

            rarity += 3.0

        elif length == 6:

            rarity += 2.0

        elif length <= 8:

            rarity += 1.0

        if username.isalpha():

            rarity += 1.0

        result.rarity = min(
            rarity,
            10.0,
        )

        # -------------------------------------------------
        # BRAND
        # -------------------------------------------------

        brand = 5.0

        vowels = sum(
            char in "aeiou"
            for char in username
        )

        if vowels >= 1:

            brand += 1.0

        if vowels >= 2:

            brand += 1.0

        if username.isalpha():

            brand += 1.0

        if "_" not in username:

            brand += 1.0

        result.brand = min(
            brand,
            10.0,
        )

        # -------------------------------------------------
        # LIQUIDITY
        # -------------------------------------------------

        liquidity = (
            result.readability * 0.35
            + result.rarity * 0.25
            + result.brand * 0.40
        )

        result.liquidity = round(
            min(
                liquidity,
                10.0,
            ),
            2,
        )

        # -------------------------------------------------
        # BEAUTY
        # -------------------------------------------------

        beauty = (
            result.readability * 0.4
            + result.rarity * 0.2
            + result.liquidity * 0.2
            + result.brand * 0.2
        )

        result.beauty_score = round(
            min(
                beauty,
                10.0,
            ),
            2,
        )

    # =====================================================
    # PRICE
    # =====================================================

    @staticmethod
    def _calculate_price(
        result: HunterResult,
    ) -> None:

        score = result.beauty_score

        if score >= 9.5:

            result.price_min = 100_000
            result.price_max = 1_000_000

        elif score >= 9.0:

            result.price_min = 50_000
            result.price_max = 500_000

        elif score >= 8.0:

            result.price_min = 10_000
            result.price_max = 100_000

        elif score >= 7.0:

            result.price_min = 2_000
            result.price_max = 25_000

        else:

            result.price_min = 500
            result.price_max = 10_000
