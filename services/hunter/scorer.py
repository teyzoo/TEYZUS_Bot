from __future__ import annotations

from services.hunter.beauty import (
    beauty_score,
    readability_score,
)


# =========================================================
# CONSTANTS
# =========================================================

COMMON_LETTERS = set(
    "aeinorst"
)

PREMIUM_LETTERS = set(
    "aeimnorstuv"
)

RARE_LETTERS = set(
    "qzxj"
)

COMMON_BIGRAMS = {
    "an",
    "ar",
    "as",
    "at",
    "al",
    "am",
    "en",
    "er",
    "es",
    "et",
    "in",
    "is",
    "it",
    "on",
    "or",
    "os",
    "re",
    "ri",
    "ro",
    "st",
    "ta",
    "te",
    "ti",
    "to",
    "ra",
    "la",
    "le",
    "li",
    "lo",
    "na",
    "ne",
    "ni",
    "no",
}


# =========================================================
# NORMALIZE
# =========================================================

def normalize_username(
    username: str,
) -> str:

    return (
        username
        .strip()
        .lower()
        .lstrip("@")
    )


# =========================================================
# LETTER BALANCE
# =========================================================

def letter_balance_score(
    username: str,
) -> float:

    username = normalize_username(
        username
    )

    if not username:
        return 0.0

    common = sum(
        1
        for char in username
        if char in COMMON_LETTERS
    )

    ratio = (
        common / len(username)
    )

    return min(
        10.0,
        ratio * 10.0,
    )


# =========================================================
# RARE LETTER SCORE
# =========================================================

def rare_letter_score(
    username: str,
) -> float:

    username = normalize_username(
        username
    )

    if not username:
        return 0.0

    rare_count = sum(
        1
        for char in username
        if char in RARE_LETTERS
    )

    # Редкие буквы могут повышать
    # уникальность, но слишком большое
    # количество ухудшает читаемость.

    if rare_count == 0:
        return 4.0

    if rare_count == 1:
        return 8.0

    if rare_count == 2:
        return 6.0

    return 3.0


# =========================================================
# BRAND SCORE
# =========================================================

def brand_score(
    username: str,
) -> float:

    username = normalize_username(
        username
    )

    if not username:
        return 0.0

    score = 4.0

    beauty = beauty_score(
        username
    )

    readability = readability_score(
        username
    )

    # -----------------------------------------------------
    # Красивые имена лучше подходят брендам
    # -----------------------------------------------------

    score += (
        beauty - 5.0
    ) * 0.45

    # -----------------------------------------------------
    # Читаемость
    # -----------------------------------------------------

    score += (
        readability - 5.0
    ) * 0.35

    # -----------------------------------------------------
    # Короткие username ценнее для брендинга
    # -----------------------------------------------------

    length = len(username)

    if length == 5:
        score += 1.5

    elif length == 6:
        score += 1.3

    elif length == 7:
        score += 0.8

    elif length == 8:
        score += 0.4

    elif length > 12:
        score -= 1.0

    # -----------------------------------------------------
    # Популярные буквы
    # -----------------------------------------------------

    score += (
        letter_balance_score(
            username
        )
        - 5.0
    ) * 0.15

    return round(
        max(
            0.0,
            min(
                score,
                10.0,
            ),
        ),
        2,
    )


# =========================================================
# RARITY SCORE
# =========================================================

def rarity_score(
    username: str,
) -> float:

    username = normalize_username(
        username
    )

    if not username:
        return 0.0

    score = 5.0

    length = len(username)

    # -----------------------------------------------------
    # Короткие username значительно более редкие
    # -----------------------------------------------------

    if length == 5:
        score += 4.0

    elif length == 6:
        score += 3.0

    elif length == 7:
        score += 2.0

    elif length == 8:
        score += 1.0

    elif length >= 12:
        score -= 1.0

    # -----------------------------------------------------
    # Редкие буквы
    # -----------------------------------------------------

    rare = rare_letter_score(
        username
    )

    score += (
        rare - 5.0
    ) * 0.35

    # -----------------------------------------------------
    # Уникальные символы
    # -----------------------------------------------------

    unique_ratio = (
        len(set(username))
        / len(username)
    )

    if unique_ratio >= 0.85:
        score += 1.0

    elif unique_ratio >= 0.70:
        score += 0.5

    elif unique_ratio < 0.45:
        score -= 0.5

    return round(
        max(
            0.0,
            min(
                score,
                10.0,
            ),
        ),
        2,
    )


# =========================================================
# LIQUIDITY SCORE
# =========================================================

def liquidity_score(
    username: str,
) -> float:

    username = normalize_username(
        username
    )

    if not username:
        return 0.0

    score = 4.0

    beauty = beauty_score(
        username
    )

    readability = readability_score(
        username
    )

    brand = brand_score(
        username
    )

    # -----------------------------------------------------
    # Красивые username легче продавать
    # -----------------------------------------------------

    score += (
        beauty - 5.0
    ) * 0.35

    # -----------------------------------------------------
    # Читаемые username легче запоминаются
    # -----------------------------------------------------

    score += (
        readability - 5.0
    ) * 0.30

    # -----------------------------------------------------
    # Брендовый потенциал
    # -----------------------------------------------------

    score += (
        brand - 5.0
    ) * 0.30

    # -----------------------------------------------------
    # Длина
    # -----------------------------------------------------

    length = len(username)

    if length == 5:
        score += 1.5

    elif length == 6:
        score += 1.2

    elif length == 7:
        score += 0.8

    elif length == 8:
        score += 0.3

    elif length > 12:
        score -= 1.0

    return round(
        max(
            0.0,
            min(
                score,
                10.0,
            ),
        ),
        2,
    )


# =========================================================
# COMMERCIAL SCORE
# =========================================================

def commercial_score(
    username: str,
) -> float:

    username = normalize_username(
        username
    )

    if not username:
        return 0.0

    beauty = beauty_score(
        username
    )

    rarity = rarity_score(
        username
    )

    brand = brand_score(
        username
    )

    liquidity = liquidity_score(
        username
    )

    score = (
        beauty * 0.25
        + rarity * 0.20
        + brand * 0.25
        + liquidity * 0.30
    )

    return round(
        min(
            10.0,
            max(
                0.0,
                score,
            ),
        ),
        2,
    )


# =========================================================
# TOTAL SCORE
# =========================================================

def total_score(
    username: str,
) -> float:

    username = normalize_username(
        username
    )

    if not username:
        return 0.0

    beauty = beauty_score(
        username
    )

    readability = readability_score(
        username
    )

    rarity = rarity_score(
        username
    )

    brand = brand_score(
        username
    )

    liquidity = liquidity_score(
        username
    )

    score = (
        beauty * 0.25
        + readability * 0.15
        + rarity * 0.20
        + brand * 0.20
        + liquidity * 0.20
    )

    return round(
        min(
            10.0,
            max(
                0.0,
                score,
            ),
        ),
        2,
    )
