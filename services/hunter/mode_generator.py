from __future__ import annotations

from services.hunter.beautiful_generator import (
    generate_candidates,
)
from services.hunter.dictionary import (
    dictionary_candidates,
)
from services.hunter.masks import (
    generate_from_mask,
)


def generate_six_letter_candidates(
    amount: int = 5000,
) -> list[str]:

    return generate_candidates(
        length=6,
        amount=amount,
    )


def generate_five_letter_candidates(
    amount: int = 10000,
) -> list[str]:

    return generate_candidates(
        length=5,
        amount=amount,
    )


def generate_dictionary_candidates(
    length: int | None = None,
) -> list[str]:

    if length is None:
        length = 6

    return dictionary_candidates(
        length
    )


def generate_mask_candidates(
    mask: str,
    limit: int = 5000,
) -> list[str]:

    return generate_from_mask(
        mask=mask,
        limit=limit,
    )
