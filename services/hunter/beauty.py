from __future__ import annotations

from itertools import product


# =========================================================
# CONSTANTS
# =========================================================

LETTERS = "abcdefghijklmnopqrstuvwxyz"

MIN_USERNAME_LENGTH = 5
MAX_USERNAME_LENGTH = 32


# =========================================================
# VALIDATION
# =========================================================

def validate_length(
    length: int,
) -> bool:

    return (
        MIN_USERNAME_LENGTH
        <= length
        <= MAX_USERNAME_LENGTH
    )


# =========================================================
# BASIC CANDIDATE CHECK
# =========================================================

def is_valid_candidate(
    username: str,
) -> bool:

    if not username:
        return False

    username = username.lower()

    if not (
        MIN_USERNAME_LENGTH
        <= len(username)
        <= MAX_USERNAME_LENGTH
    ):
        return False

    if not username[0].isalpha():
        return False

    return all(
        char in LETTERS
        for char in username
    )


# =========================================================
# PATTERN GENERATOR
# =========================================================

def generate_candidates(
    length: int,
    limit: int = 1000,
) -> list[str]:

    if not validate_length(length):
        return []

    if limit <= 0:
        return []

    result: list[str] = []

    seen: set[str] = set()

    # -----------------------------------------------------
    # Для небольших username полный перебор невозможен:
    #
    # 5 букв = 11 881 376
    # 6 букв = 308 915 776
    #
    # Поэтому используем набор красивых шаблонов.
    # -----------------------------------------------------

    patterns = [
        # Повторы
        "aabb",
        "abab",
        "abba",

        # Чередование
        "ababab",
        "abcabc",
        "abccba",

        # Повтор одной буквы
        "aaab",
        "abaa",
        "baaa",

        # Последовательности
        "abc",
        "cba",

        # Более коммерческие структуры
        "aabbcc",
        "abac",
        "abca",
        "acba",
    ]

    # -----------------------------------------------------
    # Для каждой позиции создаём комбинации букв.
    # -----------------------------------------------------

    for pattern in patterns:

        if len(result) >= limit:
            break

        if len(pattern) > length:
            continue

        # -------------------------------------------------
        # Дополняем шаблон до нужной длины.
        # -------------------------------------------------

        template = pattern

        while len(template) < length:
            template += "ab"

        template = template[:length]

        # -------------------------------------------------
        # Определяем уникальные символы шаблона.
        # -------------------------------------------------

        unique_symbols = []

        for char in template:

            if char not in unique_symbols:
                unique_symbols.append(char)

        # -------------------------------------------------
        # Не больше 4 переменных букв на шаблон.
        # -------------------------------------------------

        unique_symbols = unique_symbols[:4]

        for values in product(
            LETTERS,
            repeat=len(unique_symbols),
        ):

            mapping = dict(
                zip(
                    unique_symbols,
                    values,
                )
            )

            username = "".join(
                mapping[char]
                for char in template
            )

            if not is_valid_candidate(
                username
            ):
                continue

            if username in seen:
                continue

            seen.add(username)

            result.append(
                username
            )

            if len(result) >= limit:
                return result

    return result


# =========================================================
# RANDOM-LIKE CANDIDATES
# =========================================================

def generate_random_candidates(
    length: int,
    limit: int = 1000,
) -> list[str]:

    if not validate_length(length):
        return []

    if limit <= 0:
        return []

    result: list[str] = []

    seen: set[str] = set()

    # Используем детерминированные комбинации,
    # чтобы одинаковый запрос давал стабильные
    # результаты и не создавал огромную нагрузку.

    for first in LETTERS:

        if len(result) >= limit:
            break

        for second in LETTERS:

            if len(result) >= limit:
                break

            prefix = first + second

            remaining = length - 2

            if remaining <= 0:
                candidate = prefix

                if (
                    candidate not in seen
                    and is_valid_candidate(candidate)
                ):
                    seen.add(candidate)
                    result.append(candidate)

                continue

            for suffix in product(
                LETTERS,
                repeat=min(
                    remaining,
                    2,
                ),
            ):

                candidate = (
                    prefix
                    + "".join(suffix)
                )

                # Если username ещё короткий,
                # дополняем повторением шаблона.

                while len(candidate) < length:
                    candidate += (
                        candidate[-1]
                        if candidate
                        else "a"
                    )

                candidate = candidate[:length]

                if not is_valid_candidate(
                    candidate
                ):
                    continue

                if candidate in seen:
                    continue

                seen.add(candidate)

                result.append(
                    candidate
                )

                if len(result) >= limit:
                    return result

    return result


# =========================================================
# MASK GENERATOR
# =========================================================

def generate_from_mask(
    mask: str,
    limit: int = 5000,
) -> list[str]:

    mask = mask.lower().strip()

    if not (
        MIN_USERNAME_LENGTH
        <= len(mask)
        <= MAX_USERNAME_LENGTH
    ):
        return []

    if not all(
        char == "?"
        or char in LETTERS
        for char in mask
    ):
        return []

    if limit <= 0:
        return []

    unknown_count = mask.count("?")

    if unknown_count == 0:

        if is_valid_candidate(mask):
            return [mask]

        return []

    # -----------------------------------------------------
    # Без ограничения количество вариантов может
    # взорваться:
    #
    # 5 ? = 11 881 376
    # 6 ? = 308 915 776
    #
    # Поэтому разрешаем максимум 5 неизвестных.
    # -----------------------------------------------------

    if unknown_count > 5:
        return []

    positions = [
        index
        for index, char in enumerate(mask)
        if char == "?"
    ]

    result: list[str] = []

    seen: set[str] = set()

    for letters in product(
        LETTERS,
        repeat=unknown_count,
    ):

        chars = list(mask)

        for position, letter in zip(
            positions,
            letters,
        ):
            chars[position] = letter

        username = "".join(chars)

        if not is_valid_candidate(
            username
        ):
            continue

        if username in seen:
            continue

        seen.add(username)

        result.append(
            username
        )

        if len(result) >= limit:
            break

    return result
