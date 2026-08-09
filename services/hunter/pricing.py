from __future__ import annotations

from dataclasses import dataclass

from services.hunter.scorer import (
    brand_score,
    beauty_score,
    liquidity_score,
    rarity_score,
    readability_score,
)


# =========================================================
# PRICE RANGE
# =========================================================

@dataclass(frozen=True)
class PriceRange:
    minimum: int
    maximum: int


# =========================================================
# BASE PRICES
# =========================================================

BASE_PRICES = {
    5: 15_000,
    6: 8_000,
    7: 4_000,
    8: 2_500,
    9: 1_500,
    10: 1_000,
}


# =========================================================
# HELPERS
# =========================================================

def clamp(
    value: float,
    minimum: float,
    maximum: float,
) -> float:

    return max(
        minimum,
        min(
            value,
            maximum,
        ),
    )


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
# LENGTH MULTIPLIER
# =========================================================

def length_multiplier(
    username: str,
) -> float:

    length = len(username)

    if length <= 5:
        return 2.5

    if length == 6:
        return 1.8

    if length == 7:
        return 1.35

    if length == 8:
        return 1.0

    if length == 9:
        return 0.8

    if length == 10:
        return 0.65

    if length <= 12:
        return 0.5

    return 0.35


# =========================================================
# BEAUTY MULTIPLIER
# =========================================================

def beauty_multiplier(
    username: str,
) -> float:

    score = beauty_score(
        username
    )

    if score >= 9.5:
        return 2.5

    if score >= 9.0:
        return 2.0

    if score >= 8.5:
        return 1.6

    if score >= 8.0:
        return 1.3

    if score >= 7.0:
        return 1.0

    if score >= 6.0:
        return 0.75

    return 0.5


# =========================================================
# READABILITY MULTIPLIER
# =========================================================

def readability_multiplier(
    username: str,
) -> float:

    score = readability_score(
        username
    )

    if score >= 9.5:
        return 1.5

    if score >= 9.0:
        return 1.35

    if score >= 8.0:
        return 1.2

    if score >= 7.0:
        return 1.0

    if score >= 6.0:
        return 0.85

    return 0.7


# =========================================================
# BRAND MULTIPLIER
# =========================================================

def brand_multiplier(
    username: str,
) -> float:

    score = brand_score(
        username
    )

    if score >= 9.5:
        return 1.8

    if score >= 9.0:
        return 1.55

    if score >= 8.0:
        return 1.3

    if score >= 7.0:
        return 1.1

    if score >= 6.0:
        return 0.9

    return 0.75


# =========================================================
# RARITY MULTIPLIER
# =========================================================

def rarity_multiplier(
    username: str,
) -> float:

    score = rarity_score(
        username
    )

    if score >= 9.5:
        return 1.8

    if score >= 9.0:
        return 1.55

    if score >= 8.0:
        return 1.3

    if score >= 7.0:
        return 1.1

    if score >= 6.0:
        return 0.9

    return 0.75


# =========================================================
# LIQUIDITY MULTIPLIER
# =========================================================

def liquidity_multiplier(
    username: str,
) -> float:

    score = liquidity_score(
        username
    )

    if score >= 9.5:
        return 1.7

    if score >= 9.0:
        return 1.5

    if score >= 8.0:
        return 1.3

    if score >= 7.0:
        return 1.1

    if score >= 6.0:
        return 0.9

    return 0.7


# =========================================================
# BASE PRICE
# =========================================================

def base_price(
    username: str,
) -> int:

    username = normalize_username(
        username
    )

    length = len(username)

    if length in BASE_PRICES:
        return BASE_PRICES[
            length
        ]

    if length < 5:
        return 50_000

    if length > 10:
        return 500

    return 1_000


# =========================================================
# PRICE CALCULATION
# =========================================================

def estimate_price(
    username: str,
) -> tuple[int, int]:

    username = normalize_username(
        username
    )

    if not username:
        return 0, 0

    base = base_price(
        username
    )

    multiplier = (
        length_multiplier(username)
        * beauty_multiplier(username)
        * readability_multiplier(username)
        * brand_multiplier(username)
        * rarity_multiplier(username)
        * liquidity_multiplier(username)
    )

    # -----------------------------------------------------
    # Не даём оценке улететь в бесконечность.
    # -----------------------------------------------------

    multiplier = clamp(
        multiplier,
        0.25,
        100.0,
    )

    estimated = (
        base * multiplier
    )

    # -----------------------------------------------------
    # Минимальная цена
    # -----------------------------------------------------

    minimum = int(
        estimated * 0.65
    )

    # -----------------------------------------------------
    # Максимальная цена
    # -----------------------------------------------------

    maximum = int(
        estimated * 1.45
    )

    # -----------------------------------------------------
    # Минимум 100 ₽
    # -----------------------------------------------------

    minimum = max(
        minimum,
        100,
    )

    maximum = max(
        maximum,
        minimum,
    )

    # -----------------------------------------------------
    # Округление
    # -----------------------------------------------------

    minimum = round_price(
        minimum
    )

    maximum = round_price(
        maximum
    )

    return (
        minimum,
        maximum,
    )


# =========================================================
# ROUND PRICE
# =========================================================

def round_price(
    value: int,
) -> int:

    if value < 1_000:
        step = 100

    elif value < 10_000:
        step = 500

    elif value < 100_000:
        step = 1_000

    elif value < 1_000_000:
        step = 10_000

    else:
        step = 50_000

    return (
        round(value / step)
        * step
    )


# =========================================================
# PRICE LABEL
# =========================================================

def format_price(
    minimum: int,
    maximum: int,
) -> str:

    return (
        f"₽{minimum:,}"
        .replace(",", " ")
        + " — "
        + f"₽{maximum:,}"
        .replace(",", " ")
    )


# =========================================================
# FULL PRICE INFO
# =========================================================

def get_price_info(
    username: str,
) -> dict[str, int | str]:

    username = normalize_username(
        username
    )

    minimum, maximum = estimate_price(
        username
    )

    return {
        "username": username,
        "price_min": minimum,
        "price_max": maximum,
        "price_text": format_price(
            minimum,
            maximum,
        ),
    }
