from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import StrEnum

from services.hunter.dictionary import (
    dictionary_candidates,
)
from services.hunter.filters import (
    HunterFilters,
    apply_filters,
)
from services.hunter.generator import (
    generate_candidates,
)
from services.hunter.masks import (
    generate_from_mask,
    validate_mask,
)
from services.hunter.pricing import (
    estimate_price,
)
from services.hunter.scorer import (
    beauty_score,
    brand_score,
    liquidity_score,
    rarity_score,
    readability_score,
)
from services.hunter.telegram_checker import (
    TelegramChecker,
    TelegramUsernameStatus,
)
from services.hunter.tme_checker import (
    TMeChecker,
)


class HunterMode(StrEnum):
    SIX = "six"
    FIVE = "five"
    DICTIONARY = "dictionary"
    MASK = "mask"
    EXPENSIVE = "expensive"
    POPULAR = "popular"


@dataclass
class HunterResult:
    username: str

    available: bool

    beauty_score: float
    readability: float
    rarity: float
    brand: float
    liquidity: float

    price_min: int
    price_max: int

    telegram_status: str
    tme_available: bool


class HunterEngine:

    def __init__(self) -> None:
        self.telegram = TelegramChecker()
        self.tme = TMeChecker()

        self._check_semaphore = asyncio.Semaphore(20)

    async def close(self) -> None:
        await self.telegram.close()

        close_tme = getattr(
            self.tme,
            "close",
            None,
        )

        if close_tme is not None:
            result = close_tme()

            if asyncio.iscoroutine(result):
                await result

    # =====================================================
    # CANDIDATE GENERATION
    # =====================================================

    def generate_six(
        self,
        amount: int = 5000,
    ) -> list[str]:

        generated = generate_candidates(
            length=6,
            limit=amount,
        )

        return self._beautify(
            generated,
            premium=False,
        )

    def generate_five(
        self,
        amount: int = 10000,
    ) -> list[str]:

        generated = generate_candidates(
            length=5,
            limit=amount,
        )

        return self._beautify(
            generated,
            premium=True,
        )

    def generate_dictionary(
        self,
        length: int,
    ) -> list[str]:

        generated = dictionary_candidates(
            length
        )

        return self._beautify(
            generated,
            premium=True,
        )

    def generate_mask(
        self,
        mask: str,
        limit: int = 5000,
    ) -> list[str]:

        if not validate_mask(mask):
            return []

        generated = generate_from_mask(
            mask=mask,
            limit=limit,
        )

        return self._beautify(
            generated,
            premium=True,
        )

    # =====================================================
    # FILTERING
    # =====================================================

    def _beautify(
        self,
        usernames: list[str],
        premium: bool,
    ) -> list[str]:

        filters = HunterFilters(
            min_beauty=7.0 if premium else 6.0,
            min_readability=7.0 if premium else 6.0,
            letters_only=True,
            no_underscore=True,
            no_digits=True,
            max_length=32,
        )

        filtered = apply_filters(
            usernames,
            filters,
        )

        unique = list(
            dict.fromkeys(
                username.lower()
                for username in filtered
            )
        )

        unique.sort(
            key=lambda username: (
                beauty_score(username),
                readability_score(username),
                liquidity_score(username),
            ),
            reverse=True,
        )

        return unique

    # =====================================================
    # CHECK ONE USERNAME
    # =====================================================

    async def check_candidate(
        self,
        username: str,
    ) -> HunterResult | None:

        async with self._check_semaphore:

            telegram_status = (
                await self.telegram.check(
                    username
                )
            )

            if (
                telegram_status
                != TelegramUsernameStatus.AVAILABLE
            ):
                return None

            tme_available = (
                await self.tme.check(
                    username
                )
            )

            if not tme_available:
                return None

            readability = round(
                readability_score(username),
                2,
            )

            rarity = round(
                rarity_score(username),
                2,
            )

            brand = round(
                brand_score(username),
                2,
            )

            liquidity = round(
                liquidity_score(username),
                2,
            )

            beauty = round(
                beauty_score(username),
                2,
            )

            price_min, price_max = (
                estimate_price(
                    username
                )
            )

            return HunterResult(
                username=username,
                available=True,
                beauty_score=beauty,
                readability=readability,
                rarity=rarity,
                brand=brand,
                liquidity=liquidity,
                price_min=price_min,
                price_max=price_max,
                telegram_status=(
                    telegram_status.value
                ),
                tme_available=tme_available,
            )

    # =====================================================
    # PARALLEL CHECK
    # =====================================================

    async def check_many(
        self,
        candidates: list[str],
        amount: int,
    ) -> list[HunterResult]:

        if not candidates:
            return []

        results = await asyncio.gather(
            *(
                self.check_candidate(
                    username
                )
                for username in candidates
            ),
            return_exceptions=True,
        )

        valid: list[HunterResult] = []

        for result in results:

            if isinstance(
                result,
                HunterResult,
            ):
                valid.append(result)

        valid.sort(
            key=lambda item: (
                item.beauty_score,
                item.liquidity,
                item.brand,
                item.price_max,
            ),
            reverse=True,
        )

        return valid[:amount]

    # =====================================================
    # STANDARD 6 LETTER SEARCH
    # =====================================================

    async def search(
        self,
        length: int = 6,
        amount: int = 10,
    ) -> list[HunterResult]:

        if length == 5:
            candidates = self.generate_five(
                amount=max(
                    amount * 100,
                    5000,
                )
            )

        else:
            candidates = self.generate_six(
                amount=max(
                    amount * 100,
                    5000,
                )
            )

        return await self.check_many(
            candidates=candidates,
            amount=amount,
        )

    # =====================================================
    # PREMIUM 5 LETTER SEARCH
    # =====================================================

    async def premium(
        self,
        length: int = 5,
        amount: int = 10,
    ) -> list[HunterResult]:

        if length != 5:
            length = 5

        candidates = self.generate_five(
            amount=max(
                amount * 100,
                5000,
            )
        )

        return await self.check_many(
            candidates=candidates,
            amount=amount,
        )

    # =====================================================
    # DICTIONARY SEARCH
    # =====================================================

    async def dictionary(
        self,
        length: int,
        amount: int = 10,
    ) -> list[HunterResult]:

        candidates = self.generate_dictionary(
            length=length
        )

        return await self.check_many(
            candidates=candidates,
            amount=amount,
        )

    # =====================================================
    # MASK SEARCH
    # =====================================================

    async def mask(
        self,
        mask: str,
        amount: int = 10,
    ) -> list[HunterResult]:

        candidates = self.generate_mask(
            mask=mask,
            limit=max(
                amount * 100,
                1000,
            ),
        )

        return await self.check_many(
            candidates=candidates,
            amount=amount,
        )

    # =====================================================
    # POPULAR
    # =====================================================

    async def popular(
        self,
        amount: int = 10,
    ) -> list[HunterResult]:

        candidates = self.generate_six(
            amount=10000
        )

        candidates.sort(
            key=lambda username: (
                brand_score(username),
                readability_score(username),
                beauty_score(username),
            ),
            reverse=True,
        )

        return await self.check_many(
            candidates=candidates,
            amount=amount,
        )

    # =====================================================
    # EXPENSIVE
    # =====================================================

    async def expensive(
        self,
        amount: int = 10,
    ) -> list[HunterResult]:

        candidates = self.generate_six(
            amount=10000
        )

        candidates.sort(
            key=lambda username: (
                estimate_price(username)[1],
                liquidity_score(username),
                beauty_score(username),
            ),
            reverse=True,
        )

        return await self.check_many(
            candidates=candidates,
            amount=amount,
        )
