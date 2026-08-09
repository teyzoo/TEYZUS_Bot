from __future__ import annotations

from services.hunter.filters import (
    HunterFilters,
    apply_filters,
)


def default_filters() -> HunterFilters:

    return HunterFilters(
        min_beauty=6.0,
        min_readability=6.0,
        letters_only=True,
        no_underscore=True,
        no_digits=True,
        max_length=32,
    )


def premium_filters() -> HunterFilters:

    return HunterFilters(
        min_beauty=7.0,
        min_readability=7.0,
        letters_only=True,
        no_underscore=True,
        no_digits=True,
        max_length=32,
    )


def filter_candidates(
    usernames: list[str],
    premium: bool = False,
) -> list[str]:

    filters = (
        premium_filters()
        if premium
        else default_filters()
    )

    return apply_filters(
        usernames,
        filters,
    )
