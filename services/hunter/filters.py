from __future__ import annotations

from dataclasses import dataclass

from services.hunter.beauty import (
    beauty_score,
    readability_score,
)


# =========================================================
# FILTER CONFIG
# =========================================================

@dataclass
class HunterFilters:
    """
    Настройки фильтрации username.
    """

    min_beauty: float = 0.0
    min_readability: float = 0.0

    letters_only: bool = True
    no_underscore: bool = True
    no_digits: bool = True

    max_length: int = 32


# =========================================================
# BASIC VALIDATION
# =========================================================

def is_valid_username(
    username: str,
) -> bool:

    if not username:
        return False

    username = username.lower().strip()

    if not 5 <= len(username) <= 32:
        return False

    # Telegram username должен начинаться
    # с буквы или цифры.
    if not username[0].isalnum():
        return False

    for char in username:

        if (
            not char.isalpha()
            and not char.isdigit()
            and char != "_"
        ):
            return False

    return True


# =========================================================
# BEAUTIFUL CANDIDATE
# =========================================================

def is_beautiful_candidate(
    username: str,
) -> bool:

    if not is_valid_username(username):
        return False

    username = username.lower().strip()

    # -----------------------------------------------------
    # Только латинские символы для Hunter
    # -----------------------------------------------------

    if not username.isalpha():
        return False

    # -----------------------------------------------------
    # Не допускаем слишком длинные имена
    # -----------------------------------------------------

    if len(username) > 32:
        return False

    # -----------------------------------------------------
    # Beauty score
    # -----------------------------------------------------

    beauty = beauty_score(
        username
    )

    # -----------------------------------------------------
    # Readability
    # -----------------------------------------------------

    readability = readability_score(
        username
    )

    # -----------------------------------------------------
    # Минимальный базовый порог
    # -----------------------------------------------------

    if beauty < 4:
        return False

    if readability < 3:
        return False

    return True


# =========================================================
# APPLY FILTERS
# =========================================================

def apply_filters(
    usernames: list[str],
    filters: HunterFilters,
) -> list[str]:

    result: list[str] = []

    seen: set[str] = set()

    for username in usernames:

        if not username:
            continue

        username = username.lower().strip()

        # -------------------------------------------------
        # DUPLICATES
        # -------------------------------------------------

        if username in seen:
            continue

        seen.add(username)

        # -------------------------------------------------
        # LENGTH
        # -------------------------------------------------

        if len(username) > filters.max_length:
            continue

        if len(username) < 5:
            continue

        # -------------------------------------------------
        # LETTERS ONLY
        # -------------------------------------------------

        if (
            filters.letters_only
            and not username.isalpha()
        ):
            continue

        # -------------------------------------------------
        # UNDERSCORE
        # -------------------------------------------------

        if (
            filters.no_underscore
            and "_" in username
        ):
            continue

        # -------------------------------------------------
        # DIGITS
        # -------------------------------------------------

        if (
            filters.no_digits
            and any(
                char.isdigit()
                for char in username
            )
        ):
            continue

        # -------------------------------------------------
        # VALID CHARACTERS
        # -------------------------------------------------

        if not is_valid_username(
            username
        ):
            continue

        # -------------------------------------------------
        # BEAUTY
        # -------------------------------------------------

        beauty = beauty_score(
            username
        )

        if beauty < filters.min_beauty:
            continue

        # -------------------------------------------------
        # READABILITY
        # -------------------------------------------------

        readability = readability_score(
            username
        )

        if readability < filters.min_readability:
            continue

        result.append(
            username
        )

    return result


# =========================================================
# DEFAULT FILTER
# =========================================================

def default_filters() -> HunterFilters:

    return HunterFilters(
        min_beauty=0.0,
        min_readability=0.0,
        letters_only=True,
        no_underscore=True,
        no_digits=True,
        max_length=32,
    )


# =========================================================
# BEAUTIFUL FILTER
# =========================================================

def beautiful_filters() -> HunterFilters:

    return HunterFilters(
        min_beauty=4.0,
        min_readability=3.0,
        letters_only=True,
        no_underscore=True,
        no_digits=True,
        max_length=32,
    )


# =========================================================
# PREMIUM FILTER
# =========================================================

def premium_filters() -> HunterFilters:

    return HunterFilters(
        min_beauty=5.0,
        min_readability=4.0,
        letters_only=True,
        no_underscore=True,
        no_digits=True,
        max_length=32,
    )
