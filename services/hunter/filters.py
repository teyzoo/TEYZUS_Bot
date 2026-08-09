from dataclasses import dataclass

from services.hunter.beauty import (
    beauty_score,
    readability_score,
)


@dataclass
class HunterFilters:

    min_beauty: float = 0.0

    min_readability: float = 0.0

    letters_only: bool = True

    no_underscore: bool = True

    no_digits: bool = True

    max_length: int = 32


def is_beautiful_candidate(
    username: str,
) -> bool:

    username = (
        username
        .lower()
        .strip()
        .lstrip("@")
    )

    if not username:
        return False

    if not 5 <= len(username) <= 32:
        return False

    if not username.isalpha():
        return False

    if "_" in username:
        return False

    if any(
        char.isdigit()
        for char in username
    ):
        return False

    if beauty_score(username) < 6.0:
        return False

    if readability_score(username) < 6.0:
        return False

    return True


def apply_filters(
    usernames: list[str],
    filters: HunterFilters,
) -> list[str]:

    result: list[str] = []

    for username in usernames:

        username = (
            username
            .lower()
            .strip()
            .lstrip("@")
        )

        if not username:
            continue

        if len(username) > filters.max_length:
            continue

        if (
            filters.letters_only
            and not username.isalpha()
        ):
            continue

        if (
            filters.no_underscore
            and "_" in username
        ):
            continue

        if (
            filters.no_digits
            and any(
                char.isdigit()
                for char in username
            )
        ):
            continue

        if (
            beauty_score(username)
            < filters.min_beauty
        ):
            continue

        if (
            readability_score(username)
            < filters.min_readability
        ):
            continue

        result.append(username)

    return result
