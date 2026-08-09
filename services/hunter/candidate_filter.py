from __future__ import annotations

import re


def is_clean(
    username: str,
) -> bool:

    username = (
        username
        .strip()
        .lstrip("@")
        .lower()
    )

    if not username:
        return False

    if len(username) < 5:
        return False

    if len(username) > 32:
        return False

    if not re.fullmatch(
        r"[a-z][a-z0-9_]*",
        username,
    ):
        return False

    if "_" in username:
        return False

    if any(
        char.isdigit()
        for char in username
    ):
        return False

    return True


def has_excessive_repetition(
    username: str,
) -> bool:

    if len(username) < 3:
        return False

    for index in range(
        len(username) - 2
    ):

        if (
            username[index]
            == username[index + 1]
            == username[index + 2]
        ):
            return True

    return False


def has_random_structure(
    username: str,
) -> bool:

    if len(username) < 5:
        return True

    transitions = 0

    for index in range(
        len(username) - 1
    ):

        current = username[index]
        next_char = username[
            index + 1
        ]

        if (
            current.isalpha()
            != next_char.isalpha()
        ):
            transitions += 1

    return transitions >= 2


def is_beautiful_candidate(
    username: str,
) -> bool:

    username = (
        username
        .strip()
        .lstrip("@")
        .lower()
    )

    if not is_clean(username):
        return False

    if has_excessive_repetition(
        username
    ):
        return False

    if has_random_structure(
        username
    ):
        return False

    return True


def filter_candidates(
    usernames: list[str],
) -> list[str]:

    result = []
    seen = set()

    for username in usernames:

        username = (
            username
            .strip()
            .lstrip("@")
            .lower()
        )

        if username in seen:
            continue

        if not is_beautiful_candidate(
            username
        ):
            continue

        seen.add(username)

        result.append(
            username
        )

    return result
