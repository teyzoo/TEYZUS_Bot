from __future__ import annotations

import random
import re
from typing import Iterable


VOWELS = "aeiou"

CONSONANTS = (
    "bcdfghjklmnpqrstvwxyz"
)

COMMON_PAIRS = (
    "ai",
    "al",
    "ar",
    "as",
    "av",
    "be",
    "bi",
    "bo",
    "ca",
    "ce",
    "ci",
    "co",
    "da",
    "de",
    "di",
    "do",
    "el",
    "en",
    "er",
    "ev",
    "ex",
    "fi",
    "fo",
    "ga",
    "ge",
    "ia",
    "io",
    "la",
    "le",
    "li",
    "lo",
    "lu",
    "ma",
    "me",
    "mi",
    "mo",
    "na",
    "ne",
    "ni",
    "no",
    "nu",
    "on",
    "or",
    "os",
    "ra",
    "re",
    "ri",
    "ro",
    "ru",
    "sa",
    "se",
    "si",
    "so",
    "ta",
    "te",
    "ti",
    "to",
    "va",
    "ve",
    "vi",
    "vo",
    "za",
    "ze",
    "zi",
    "zo",
)


PREFIXES = (
    "neo",
    "nova",
    "nexa",
    "viva",
    "vivo",
    "velo",
    "vera",
    "vero",
    "zena",
    "zeno",
    "luma",
    "luna",
    "nora",
    "nori",
    "vora",
    "voro",
    "sora",
    "sori",
    "aero",
    "aura",
)


SUFFIXES = (
    "ly",
    "ix",
    "io",
    "on",
    "or",
    "us",
    "is",
    "ia",
    "a",
    "o",
    "x",
)


BAD_PATTERNS = (
    r"[0-9]{2,}",
    r"(.)\1\1",
    r"[^a-z0-9_]",
    r"^[_0-9]",
)


def normalize_username(
    username: str,
) -> str:

    username = username.lower()
    username = username.lstrip("@")

    return username


def is_valid_username(
    username: str,
) -> bool:

    username = normalize_username(
        username
    )

    if not 5 <= len(username) <= 32:
        return False

    if not re.fullmatch(
        r"[a-z][a-z0-9_]*",
        username,
    ):
        return False

    for pattern in BAD_PATTERNS:

        if re.search(
            pattern,
            username,
        ):
            return False

    return True


def vowel_ratio(
    username: str,
) -> float:

    if not username:
        return 0.0

    letters = [
        char
        for char in username
        if char.isalpha()
    ]

    if not letters:
        return 0.0

    vowels = sum(
        char in VOWELS
        for char in letters
    )

    return vowels / len(letters)


def has_good_structure(
    username: str,
) -> bool:

    ratio = vowel_ratio(
        username
    )

    if ratio < 0.20:
        return False

    if ratio > 0.75:
        return False

    for index in range(
        len(username) - 1
    ):

        pair = username[index:index + 2]

        if pair in COMMON_PAIRS:
            return True

    return False


def generate_syllable(
    length: int,
) -> str:

    result = ""

    while len(result) < length:

        consonant = random.choice(
            CONSONANTS
        )

        vowel = random.choice(
            VOWELS
        )

        result += (
            consonant + vowel
        )

    return result[:length]


def generate_from_prefix(
    length: int,
) -> str | None:

    prefixes = [
        prefix
        for prefix in PREFIXES
        if len(prefix) < length
    ]

    if not prefixes:
        return None

    prefix = random.choice(
        prefixes
    )

    remaining = (
        length - len(prefix)
    )

    if remaining <= 0:
        return prefix[:length]

    suffix = generate_syllable(
        remaining
    )

    return (
        prefix + suffix
    )[:length]


def generate_from_suffix(
    length: int,
) -> str | None:

    suffixes = [
        suffix
        for suffix in SUFFIXES
        if len(suffix) < length
    ]

    if not suffixes:
        return None

    suffix = random.choice(
        suffixes
    )

    remaining = (
        length - len(suffix)
    )

    return (
        generate_syllable(
            remaining
        )
        + suffix
    )[:length]


def generate_candidates(
    length: int,
    amount: int = 1000,
) -> list[str]:

    if not 5 <= length <= 32:
        return []

    result: set[str] = set()

    attempts = 0

    maximum_attempts = (
        amount * 20
    )

    while (
        len(result) < amount
        and attempts < maximum_attempts
    ):

        attempts += 1

        mode = random.randint(
            0,
            2,
        )

        if mode == 0:

            candidate = generate_syllable(
                length
            )

        elif mode == 1:

            candidate = generate_from_prefix(
                length
            )

        else:

            candidate = generate_from_suffix(
                length
            )

        if not candidate:
            continue

        candidate = normalize_username(
            candidate
        )

        if not is_valid_username(
            candidate
        ):
            continue

        if not has_good_structure(
            candidate
        ):
            continue

        result.add(
            candidate
        )

    return list(result)


def generate_beautiful(
    lengths: Iterable[int],
    amount_per_length: int = 500,
) -> list[str]:

    result: set[str] = set()

    for length in lengths:

        candidates = generate_candidates(
            length=length,
            amount=amount_per_length,
        )

        result.update(
            candidates
        )

    return list(result)
