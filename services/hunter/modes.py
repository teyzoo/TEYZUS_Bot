from __future__ import annotations

from itertools import product
from typing import Iterable


ALPHABET = "abcdefghijklmnopqrstuvwxyz"


# =========================================================
# BEAUTIFUL / BASIC
# =========================================================

def generate_basic_candidates(
    length: int,
    limit: int,
) -> list[str]:

    from services.hunter.generator import generate_candidates
    from services.hunter.filters import is_beautiful_candidate
    from services.hunter.scorer import beauty_score

    generated = generate_candidates(
        length=length,
        limit=limit * 10,
    )

    candidates = [
        username
        for username in generated
        if is_beautiful_candidate(username)
    ]

    candidates.sort(
        key=beauty_score,
        reverse=True,
    )

    return candidates[:limit]


# =========================================================
# DICTIONARY
# =========================================================

def generate_dictionary_candidates(
    words: Iterable[str],
    length: int,
    limit: int,
) -> list[str]:

    result: list[str] = []

    seen: set[str] = set()

    for word in words:

        username = (
            word.strip()
            .lower()
            .replace(" ", "")
            .replace("-", "")
        )

        if not username:
            continue

        if len(username) != length:
            continue

        if not username.isalnum():
            continue

        if username in seen:
            continue

        seen.add(username)

        result.append(username)

        if len(result) >= limit:
            break

    return result


# =========================================================
# MASK
# =========================================================

def generate_mask_candidates(
    mask: str,
    limit: int,
) -> list[str]:

    mask = mask.strip().lower()

    if not mask:
        return []

    result: list[str] = []

    slots = [
        index
        for index, char in enumerate(mask)
        if char == "?"
    ]

    if not slots:

        if (
            mask.isalnum()
            and len(mask) >= 5
            and len(mask) <= 32
        ):
            return [mask]

        return []

    for replacement in product(
        ALPHABET,
        repeat=len(slots),
    ):

        chars = list(mask)

        for index, value in zip(
            slots,
            replacement,
        ):
            chars[index] = value

        username = "".join(chars)

        if not username.isalnum():
            continue

        result.append(username)

        if len(result) >= limit:
            break

    return result


# =========================================================
# EXPENSIVE
# =========================================================

def sort_expensive_candidates(
    candidates: list[str],
) -> list[str]:

    from services.hunter.scorer import (
        beauty_score,
        brand_score,
        rarity_score,
        liquidity_score,
    )

    return sorted(
        candidates,
        key=lambda username: (
            brand_score(username),
            rarity_score(username),
            liquidity_score(username),
            beauty_score(username),
        ),
        reverse=True,
    )


# =========================================================
# POPULAR
# =========================================================

def sort_popular_candidates(
    candidates: list[str],
) -> list[str]:

    from services.hunter.scorer import (
        brand_score,
        liquidity_score,
        readability_score,
        beauty_score,
    )

    return sorted(
        candidates,
        key=lambda username: (
            liquidity_score(username),
            brand_score(username),
            readability_score(username),
            beauty_score(username),
        ),
        reverse=True,
    )
