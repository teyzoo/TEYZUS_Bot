from __future__ import annotations

from dataclasses import dataclass

from services.hunter.beautiful_ranker import (
    rank_beautiful,
)
from services.hunter.mode_filters import (
    filter_candidates,
)
from services.hunter.mode_generator import (
    generate_dictionary_candidates,
    generate_five_letter_candidates,
    generate_mask_candidates,
    generate_six_letter_candidates,
)
from services.hunter.search_modes import (
    SearchMode,
)


@dataclass
class ModeSearchResult:

    username: str

    beauty: float

    readability: float

    available: bool = False


class ModeSearchEngine:

    def generate(
        self,
        mode: SearchMode,
        mask: str | None = None,
        amount: int = 5000,
    ) -> list[str]:

        if mode == SearchMode.SIX_LETTERS:

            return generate_six_letter_candidates(
                amount=amount
            )

        if mode == SearchMode.FIVE_LETTERS:

            return generate_five_letter_candidates(
                amount=amount
            )

        if mode == SearchMode.DICTIONARY:

            return generate_dictionary_candidates()

        if mode == SearchMode.MASK:

            if not mask:
                return []

            return generate_mask_candidates(
                mask=mask,
                limit=amount,
            )

        if mode in (
            SearchMode.EXPENSIVE,
            SearchMode.POPULAR,
        ):

            return generate_six_letter_candidates(
                amount=amount
            )

        return []

    def prepare(
        self,
        candidates: list[str],
        premium: bool = False,
    ) -> list[str]:

        candidates = filter_candidates(
            candidates,
            premium=premium,
        )

        ranked = rank_beautiful(
            candidates
        )

        return [
            item.username
            for item in ranked
        ]

    def search(
        self,
        mode: SearchMode,
        premium: bool = False,
        mask: str | None = None,
        amount: int = 5000,
        limit: int = 100,
    ) -> list[str]:

        candidates = self.generate(
            mode=mode,
            mask=mask,
            amount=amount,
        )

        candidates = self.prepare(
            candidates,
            premium=premium,
        )

        return candidates[:limit]
