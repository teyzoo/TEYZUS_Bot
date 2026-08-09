from __future__ import annotations
import asyncio
from dataclasses import dataclass
from services.hunter.dictionary import (
    dictionary_candidates,
)
from services.hunter.filters import (
    is_beautiful_candidate,
)
from services.hunter.generator import (
    generate_candidates,
)
from services.hunter.masks import (
    generate_from_mask,
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
        self._check_semaphore = asyncio.Semaphore(
            10
        )
    async def close(self) -> None:
        await self.telegram.close()
    # =====================================================
    # CANDIDATES
    # =====================================================
    def prepare_candidates(
        self,
        length: int,
        amount: int = 1000,
    ) -> list[str]:
        generated = generate_candidates(
            length=length,
            limit=max(
                amount * 20,
                1000,
            ),
        )
        beautiful = [
            username
            for username in generated
            if is_beautiful_candidate(
                username
            )
        ]
        beautiful = list(
            dict.fromkeys(
                beautiful
            )
        )
        beautiful.sort(
            key=lambda username: (
                beauty_score(username),
                readability_score(username),
                brand_score(username),
                liquidity_score(username),
            ),
            reverse=True,
        )
        return beautiful[:amount]
    # =====================================================
    # CHECK ONE USERNAME
    # =====================================================
    async def check_candidate(
        self,
        username: str,
    ) -> HunterResult | None:
        username = (
            username
            .lstrip("@")
            .lower()
            .strip()
        )
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
            readability = readability_score(
                username
            )
            rarity = rarity_score(
                username
            )
            brand = brand_score(
                username
            )
            liquidity = liquidity_score(
                username
            )
            beauty = beauty_score(
                username
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
    # CHECK MANY
    # =====================================================
    async def check_candidates(
        self,
        candidates: list[str],
        amount: int,
    ) -> list[HunterResult]:
        if not candidates:
            return []
        results: list[HunterResult] = []
        batch_size = 10
        for start in range(
            0,
            len(candidates),
            batch_size,
        ):
            batch = candidates[
                start:start + batch_size
            ]
            checked = await asyncio.gather(
                *(
                    self.check_candidate(
                        username
                    )
                    for username in batch
                ),
                return_exceptions=True,
            )
            for result in checked:
                if isinstance(
                    result,
                    HunterResult,
                ):
                    results.append(result)
                if len(results) >= amount:
                    break
            if len(results) >= amount:
                break
        results.sort(
            key=lambda item: (
                item.beauty_score,
                item.readability,
                item.liquidity,
                item.brand,
                item.price_max,
            ),
            reverse=True,
        )
        return results[:amount]
    # =====================================================
    # NORMAL SEARCH
    # =====================================================
    async def search(
        self,
        length: int,
        amount: int = 10,
    ) -> list[HunterResult]:
        candidates = self.prepare_candidates(
            length=length,
            amount=max(
                amount * 20,
                200,
            ),
        )
        return await self.check_candidates(
            candidates=candidates,
            amount=amount,
        )
    # =====================================================
    # PREMIUM SEARCH
    # =====================================================
    async def premium(
        self,
        length: int,
        amount: int = 10,
    ) -> list[HunterResult]:
        candidates = self.prepare_candidates(
            length=length,
            amount=max(
                amount * 30,
                300,
            ),
        )
        return await self.check_candidates(
            candidates=candidates,
            amount=amount,
        )
    # =====================================================
    # BEAUTIFUL
    # =====================================================
    async def beautiful(
        self,
        length: int = 6,
        amount: int = 10,
    ) -> list[HunterResult]:
        return await self.search(
            length=length,
            amount=amount,
        )
    # =====================================================
    # DICTIONARY
    # =====================================================
    async def dictionary(
        self,
        length: int,
        amount: int = 10,
    ) -> list[HunterResult]:
        candidates = (
            dictionary_candidates(
                length
            )
        )
        candidates = [
            username
            for username in candidates
            if is_beautiful_candidate(
                username
            )
        ]
        candidates.sort(
            key=lambda username: (
                beauty_score(username),
                brand_score(username),
                liquidity_score(username),
            ),
            reverse=True,
        )
        return await self.check_candidates(
            candidates=candidates,
            amount=amount,
        )
    # =====================================================
    # MASK
    # =====================================================
    async def mask(
        self,
        mask: str,
        amount: int = 10,
    ) -> list[HunterResult]:
        candidates = generate_from_mask(
            mask=mask,
            limit=max(
                amount * 100,
                500,
            ),
        )
        candidates = [
            username
            for username in candidates
            if is_beautiful_candidate(
                username
            )
        ]
        candidates.sort(
            key=lambda username: (
                beauty_score(username),
                readability_score(username),
                brand_score(username),
            ),
            reverse=True,
        )
        return await self.check_candidates(
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
        candidates = self.prepare_candidates(
            length=6,
            amount=500,
        )
        candidates.sort(
            key=lambda username: (
                brand_score(username),
                beauty_score(username),
                readability_score(username),
            ),
            reverse=True,
        )
        return await self.check_candidates(
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
        candidates = self.prepare_candidates(
            length=6,
            amount=1000,
        )
        candidates.sort(
            key=lambda username: (
                liquidity_score(username),
                rarity_score(username),
                brand_score(username),
                beauty_score(username),
            ),
            reverse=True,
        )
        return await self.check_candidates(
            candidates=candidates,
            amount=amount,
        )
