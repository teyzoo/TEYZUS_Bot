from __future__ import annotations

import math


VOWELS = set(
    "aeiou"
)


def calculate_vowel_balance(
    username: str,
) -> float:

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

    ratio = (
        vowels / len(letters)
    )

    distance = abs(
        ratio - 0.42
    )

    score = (
        10.0
        - distance * 18.0
    )

    return max(
        0.0,
        min(
            10.0,
            score,
        ),
    )


def calculate_length_score(
    username: str,
) -> float:

    length = len(username)

    if length == 5:
        return 10.0

    if length == 6:
        return 9.5

    if length == 7:
        return 8.8

    if length == 8:
        return 8.0

    if length == 9:
        return 7.2

    if length <= 12:
        return 6.0

    return 4.0


def calculate_repetition_score(
    username: str,
) -> float:

    if not username:
        return 0.0

    unique = len(
        set(username)
    )

    total = len(username)

    ratio = (
        unique / total
    )

    score = (
        ratio * 10.0
    )

    for index in range(
        total - 1
    ):

        if username[index] == username[
            index + 1
        ]:

            score -= 1.5

    return max(
        0.0,
        min(
            10.0,
            score,
        ),
    )


def calculate_pattern_score(
    username: str,
) -> float:

    if not username:
        return 0.0

    score = 5.0

    for index in range(
        len(username) - 1
    ):

        current = username[index]
        next_char = username[
            index + 1
        ]

        if (
            current.isalpha()
            and next_char.isalpha()
        ):

            if (
                current not in VOWELS
                and next_char in VOWELS
            ):

                score += 0.7

            elif (
                current in VOWELS
                and next_char not in VOWELS
            ):

                score += 0.5

    return max(
        0.0,
        min(
            10.0,
            score,
        ),
    )


def calculate_human_readability(
    username: str,
) -> float:

    if not username:
        return 0.0

    scores = [
        calculate_vowel_balance(
            username
        ),
        calculate_repetition_score(
            username
        ),
        calculate_pattern_score(
            username
        ),
    ]

    return round(
        sum(scores) / len(scores),
        2,
    )


def calculate_beauty(
    username: str,
) -> float:

    readability = (
        calculate_human_readability(
            username
        )
    )

    length = (
        calculate_length_score(
            username
        )
    )

    result = (
        readability * 0.65
        + length * 0.35
    )

    return round(
        max(
            0.0,
            min(
                10.0,
                result,
            ),
        ),
        2,
    )
