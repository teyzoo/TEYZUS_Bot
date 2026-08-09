from dataclasses import dataclass
from enum import StrEnum

from services.hunter.batch import (
    BatchHunterChecker,
)
from services.hunter.pricing import (
    estimate_price,
)
from services.hunter.scorer import (
    score_username,
)


class SearchMode(StrEnum):
    BEAUTIFUL = "beautiful"
    EXPENSIVE = "expensive"
    POPULAR = "popular"
    DICTIONARY = "dictionary"
    MASK = "mask"
    PREMIUM = "premium"


@dataclass
class SearchResult:
    username: str
    ai_score: float
    readability: float
    price_min: int
    price_max: int
    available: bool


class SearchPipeline:

    def __init__(
        self,
        checker: BatchHunterChecker | None = None,
    ) -> None:

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
        candidates: list[str],
        limit: int = 10,
        only_available: bool = True,
    ) -> list[SearchResult]:

        if not candidates:
            return []

        checked = await self.checker.check_many(
            candidates
        )

        results: list[SearchResult] = []

        for item in checked:

            if (
                only_available
                and not item.available
            ):
                continue

            score = score_username(
                item.username
            )

            price_min, price_max = (
                estimate_price(
                    item.username
                )
            )

            results.append(
                SearchResult(
                    username=item.username,
                    ai_score=score.total,
                    readability=score.readability,
                    price_min=price_min,
                    price_max=price_max,
                    available=item.available,
                )
            )

        results.sort(
            key=lambda result: (
                result.ai_score,
                result.readability,
            ),
            reverse=True,
        )

        return results[:limit]

    async def beautiful(
        self,
        candidates: list[str],
        limit: int = 10,
    ) -> list[SearchResult]:

        return await self.search(
            candidates=candidates,
            limit=limit,
            only_available=True,
        )

    async def expensive(
        self,
        candidates: list[str],
        limit: int = 10,
    ) -> list[SearchResult]:

        results = await self.search(
            candidates=candidates,
            limit=len(candidates),
            only_available=True,
        )

        results.sort(
            key=lambda result: (
                result.price_max,
                result.ai_score,
            ),
            reverse=True,
        )

        return results[:limit]

    async def popular(
        self,
        candidates: list[str],
        limit: int = 10,
    ) -> list[SearchResult]:

        results = await self.search(
            candidates=candidates,
            limit=len(candidates),
            only_available=True,
        )

        results.sort(
            key=lambda result: (
                result.ai_score,
                result.readability,
            ),
            reverse=True,
        )

        return results[:limit]

    async def dictionary(
        self,
        candidates: list[str],
        limit: int = 10,
    ) -> list[SearchResult]:

        return await self.search(
            candidates=candidates,
            limit=limit,
            only_available=True,
        )

    async def mask(
        self,
        candidates: list[str],
        limit: int = 10,
    ) -> list[SearchResult]:

        return await self.search(
            candidates=candidates,
            limit=limit,
            only_available=True,
        )

    async def premium(
        self,
        candidates: list[str],
        limit: int = 10,
    ) -> list[SearchResult]:

        return await self.search(
            candidates=candidates,
            limit=limit,
            only_available=True,
        )
