from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SearchMode(StrEnum):
    SIX_LETTERS = "six_letters"
    FIVE_LETTERS = "five_letters"
    DICTIONARY = "dictionary"
    MASK = "mask"
    EXPENSIVE = "expensive"
    POPULAR = "popular"


@dataclass(frozen=True)
class SearchModeConfig:
    mode: SearchMode
    length: int
    premium_required: bool
    default_candidates: int
    default_results: int


SEARCH_MODES: dict[
    SearchMode,
    SearchModeConfig,
] = {
    SearchMode.SIX_LETTERS: SearchModeConfig(
        mode=SearchMode.SIX_LETTERS,
        length=6,
        premium_required=False,
        default_candidates=5000,
        default_results=10,
    ),
    SearchMode.FIVE_LETTERS: SearchModeConfig(
        mode=SearchMode.FIVE_LETTERS,
        length=5,
        premium_required=True,
        default_candidates=10000,
        default_results=10,
    ),
    SearchMode.DICTIONARY: SearchModeConfig(
        mode=SearchMode.DICTIONARY,
        length=6,
        premium_required=True,
        default_candidates=5000,
        default_results=10,
    ),
    SearchMode.MASK: SearchModeConfig(
        mode=SearchMode.MASK,
        length=6,
        premium_required=True,
        default_candidates=5000,
        default_results=10,
    ),
    SearchMode.EXPENSIVE: SearchModeConfig(
        mode=SearchMode.EXPENSIVE,
        length=6,
        premium_required=False,
        default_candidates=5000,
        default_results=10,
    ),
    SearchMode.POPULAR: SearchModeConfig(
        mode=SearchMode.POPULAR,
        length=6,
        premium_required=False,
        default_candidates=5000,
        default_results=10,
    ),
}


def get_mode_config(
    mode: SearchMode,
) -> SearchModeConfig:

    return SEARCH_MODES[mode]
