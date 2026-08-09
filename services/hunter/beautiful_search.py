from __future__ import annotations

from dataclasses import dataclass

from services.hunter.beautiful_generator import (
    generate_candidates,
)
from services.hunter.beautiful_ranker import (
    BeautifulCandidate,
    rank_beautiful,
)
from services.hunter.candidate_filter import (
    filter_candidates,
)


@dataclass
class BeautifulSearchConfig:

    length: int = 6

    candidates: int = 2000

    results: int = 50


class BeautifulSearch:

    def __init__(
        self,
        config: BeautifulSearchConfig | None = None,
    ) -> None:

        self.config = (
            config
            or BeautifulSearchConfig()
        )

    def generate(
        self,
    ) -> list[BeautifulCandidate]:

        candidates = generate_candidates(
            length=self.config.length,
            amount=self.config.candidates,
        )

        candidates = filter_candidates(
            candidates
        )

        ranked = rank_beautiful(
            candidates
        )

        return ranked[
            :self.config.results
        ]
