from __future__ import annotations

from dataclasses import dataclass

from services.hunter.batch import (
    BatchHunterChecker,
    BatchCheckResult,
)
from services.hunter.mode_search import (
    ModeSearchEngine,
)
from services.hunter.search_modes import (
    SearchMode,
)


@dataclass
class FinalSearchResult:

    username: str

    beauty: float

    readability: float

    available: bool

    telegram_status: str

    tme_available: bool

    price_min: int

    price_max: int


class HunterSearchService:

    def __init__(
        self,
        checker: BatchHunterChecker | None = None,
    ) -> None:

        self.modes = ModeSearchEngine()

        self.checker = (
            checker
            or BatchHunterChecker(
                concurrency=20
            )
        )

    async def close(self) -> None:

        await self.checker.close()

    async def search(
        self,
        mode: SearchMode,
        premium: bool = False,
        mask: str | None = None,
        amount: int = 5000,
        limit: int = 10,
    ) -> list[FinalSearchResult]:

        candidates = self.modes.search(
            mode=mode,
            premium=premium,
            mask=mask,
            amount=amount,
            limit=amount,
        )

        if not candidates:
            return []

        checked = await self.checker.check_many(
            candidates
        )

        available = [
            item
            for item in checked
            if item.available
        ]

        if not available:
            return []

        ranked = self.modes.prepare(
            [
                item.username
                for item in available
            ],
            premium=premium,
        )

        ranking = {
            username: index
            for index, username
            in enumerate(ranked)
        }

        available.sort(
            key=lambda item: ranking.get(
                item.username,
                999999,
            )
        )

        results: list[
            FinalSearchResult
        ] = []

        for item in available[:limit]:

            beauty = self._beauty(
                item.username
            )

            readability = self._readability(
                item.username
            )

            price_min, price_max = (
                self._price(
                    item.username,
                    beauty,
                )
            )

            results.append(
                FinalSearchResult(
                    username=item.username,
                    beauty=beauty,
                    readability=readability,
                    available=True,
                    telegram_status=(
                        item.telegram.value
                    ),
                    tme_available=(
                        item.tme_available
                    ),
                    price_min=price_min,
                    price_max=price_max,
                )
            )

        return results

    @staticmethod
    def _beauty(
        username: str,
    ) -> float:

        from services.hunter.beauty import (
            beauty_score,
        )

        return round(
            beauty_score(username),
            2,
        )

    @staticmethod
    def _readability(
        username: str,
    ) -> float:

        from services.hunter.beauty import (
            readability_score,
        )

        return round(
            readability_score(username),
            2,
        )

    @staticmethod
    def _price(
        username: str,
        beauty: float,
    ) -> tuple[int, int]:

        base = len(username)

        multiplier = max(
            1.0,
            beauty / 5.0,
        )

        minimum = int(
            base
            * 100
            * multiplier
        )

        maximum = int(
            minimum * 2.5
        )

        return (
            minimum,
            maximum,
        )
