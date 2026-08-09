from __future__ import annotations

from services.hunter.search_modes import (
    SearchMode,
)
from services.hunter.search_service import (
    FinalSearchResult,
    HunterSearchService,
)


class HunterService:

    def __init__(self) -> None:

        self.searcher = (
            HunterSearchService()
        )

    async def close(self) -> None:

        await self.searcher.close()

    async def six_letters(
        self,
        limit: int = 10,
    ) -> list[FinalSearchResult]:

        return await self.searcher.search(
            mode=SearchMode.SIX_LETTERS,
            premium=False,
            amount=5000,
            limit=limit,
        )

    async def five_letters(
        self,
        limit: int = 10,
    ) -> list[FinalSearchResult]:

        return await self.searcher.search(
            mode=SearchMode.FIVE_LETTERS,
            premium=True,
            amount=10000,
            limit=limit,
        )

    async def dictionary(
        self,
        limit: int = 10,
    ) -> list[FinalSearchResult]:

        return await self.searcher.search(
            mode=SearchMode.DICTIONARY,
            premium=True,
            amount=5000,
            limit=limit,
        )

    async def mask(
        self,
        mask: str,
        limit: int = 10,
    ) -> list[FinalSearchResult]:

        return await self.searcher.search(
            mode=SearchMode.MASK,
            premium=True,
            mask=mask,
            amount=5000,
            limit=limit,
        )

    async def expensive(
        self,
        limit: int = 10,
    ) -> list[FinalSearchResult]:

        return await self.searcher.search(
            mode=SearchMode.EXPENSIVE,
            premium=False,
            amount=5000,
            limit=limit,
        )

    async def popular(
        self,
        limit: int = 10,
    ) -> list[FinalSearchResult]:

        return await self.searcher.search(
            mode=SearchMode.POPULAR,
            premium=False,
            amount=5000,
            limit=limit,
        )


hunter_service = HunterService()
