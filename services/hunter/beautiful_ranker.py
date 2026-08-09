from __future__ import annotations

from dataclasses import dataclass

from services.hunter.beauty_rules import (
    calculate_beauty,
    calculate_human_readability,
)


@dataclass
class BeautifulCandidate:

    username: str
    beauty: float
    readability: float


def rank_beautiful(
    usernames: list[str],
) -> list[BeautifulCandidate]:

    results: list[
        BeautifulCandidate
    ] = []

    for username in usernames:

        beauty = calculate_beauty(
            username
        )

        readability = (
            calculate_human_readability(
                username
            )
        )

        results.append(
            BeautifulCandidate(
                username=username,
                beauty=beauty,
                readability=readability,
            )
        )

    results.sort(
        key=lambda item: (
            item.beauty,
            item.readability,
            -len(item.username),
        ),
        reverse=True,
    )

    return results
