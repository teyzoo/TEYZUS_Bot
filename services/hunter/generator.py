from __future__ import annotations

import itertools
import random
import string
from collections.abc import Iterable, Iterator


# =========================================================
# CONSTANTS
# =========================================================

LETTERS = string.ascii_lowercase
DIGITS = string.digits
ALPHANUMERIC = LETTERS + DIGITS

DEFAULT_LIMIT = 1000
MAX_LIMIT = 100_000


# =========================================================
# NORMALIZE
# =========================================================

def normalize_username(
    username: str,
) -> str:

    username = username.strip().lower()

    if username.startswith("@"):
        username = username[1:]

    return username


# =========================================================
# VALIDATE
# =========================================================

def is_valid_username(
    username: str,
    min_length: int = 5,
    max_length: int = 32,
) -> bool:

    username = normalize_username(
        username
    )

    if not (
        min_length
        <= len(username)
        <= max_length
    ):
        return False

    for char in username:

        if not (
            char.isascii()
            and (
                char.isalpha()
                or char.isdigit()
                or char == "_"
            )
        ):
            return False

    return True


# =========================================================
# RANDOM USERNAME
# =========================================================

def random_username(
    length: int,
    *,
    letters_only: bool = False,
    allow_digits: bool = True,
    allow_underscore: bool = True,
) -> str:

    if length < 5:
        raise ValueError(
            "Минимальная длина username — 5."
        )

    if length > 32:
        raise ValueError(
            "Максимальная длина username — 32."
        )

    if letters_only:

        alphabet = LETTERS

    else:

        alphabet = LETTERS

        if allow_digits:
            alphabet += DIGITS

        if allow_underscore:
            alphabet += "_"

    # Первый символ не должен быть цифрой/underscore
    first = random.choice(
        LETTERS
    )

    if length == 1:
        return first

    rest = "".join(
        random.choice(alphabet)
        for _ in range(length - 1)
    )

    return (
        first
        + rest
    )


# =========================================================
# RANDOM BATCH
# =========================================================

def generate_random_candidates(
    length: int,
    limit: int,
    *,
    letters_only: bool = False,
    allow_digits: bool = True,
    allow_underscore: bool = True,
) -> Iterator[str]:

    limit = min(
        max(
            0,
            limit,
        ),
        MAX_LIMIT,
    )

    seen: set[str] = set()

    while len(seen) < limit:

        username = random_username(
            length=length,
            letters_only=letters_only,
            allow_digits=allow_digits,
            allow_underscore=allow_underscore,
        )

        if username in seen:
            continue

        seen.add(
            username
        )

        yield username


# =========================================================
# DICTIONARY WORDS
# =========================================================

DEFAULT_DICTIONARY = (
    "admin",
    "apple",
    "alpha",
    "angel",
    "anime",
    "audio",
    "block",
    "blue",
    "bot",
    "cloud",
    "code",
    "crypto",
    "dark",
    "data",
    "dev",
    "dream",
    "elite",
    "game",
    "gold",
    "home",
    "king",
    "light",
    "magic",
    "media",
    "moon",
    "music",
    "neo",
    "news",
    "nft",
    "nova",
    "pixel",
    "prime",
    "pro",
    "shop",
    "sky",
    "star",
    "tech",
    "token",
    "web",
    "wolf",
    "world",
)


def generate_dictionary_candidates(
    dictionary: Iterable[str],
    *,
    min_length: int = 5,
    max_length: int = 32,
    limit: int = DEFAULT_LIMIT,
) -> Iterator[str]:

    limit = min(
        max(
            0,
            limit,
        ),
        MAX_LIMIT,
    )

    seen: set[str] = set()

    for word in dictionary:

        word = normalize_username(
            word
        )

        if not is_valid_username(
            word,
            min_length=min_length,
            max_length=max_length,
        ):
            continue

        if word in seen:
            continue

        seen.add(
            word
        )

        yield word

        if len(seen) >= limit:
            return


# =========================================================
# WORD VARIATIONS
# =========================================================

def generate_word_variations(
    word: str,
    *,
    limit: int = 1000,
) -> Iterator[str]:

    word = normalize_username(
        word
    )

    if not word:
        return

    candidates: list[str] = []

    candidates.append(
        word
    )

    candidates.append(
        word + "1"
    )

    candidates.append(
        word + "2"
    )

    candidates.append(
        word + "7"
    )

    candidates.append(
        word + "8"
    )

    candidates.append(
        word + "9"
    )

    candidates.append(
        word + "_"
    )

    candidates.append(
        "_" + word
    )

    candidates.append(
        "the" + word
    )

    candidates.append(
        word + "official"
    )

    candidates.append(
        word + "pro"
    )

    candidates.append(
        word + "bot"
    )

    seen: set[str] = set()

    for candidate in candidates:

        candidate = normalize_username(
            candidate
        )

        if candidate in seen:
            continue

        if not is_valid_username(
            candidate
        ):
            continue

        seen.add(
            candidate
        )

        yield candidate

        if len(seen) >= limit:
            return


# =========================================================
# MASK
# =========================================================

def generate_mask_candidates(
    mask: str,
    *,
    limit: int = DEFAULT_LIMIT,
) -> Iterator[str]:

    mask = normalize_username(
        mask
    )

    if not mask:
        return

    limit = min(
        max(
            0,
            limit,
        ),
        MAX_LIMIT,
    )

    alphabet = LETTERS

    positions = [
        index
        for index, char in enumerate(mask)
        if char == "?"
    ]

    # -----------------------------------------------------
    # Нет ? — это готовый username
    # -----------------------------------------------------

    if not positions:

        if is_valid_username(
            mask
        ):

            yield mask

        return

    # -----------------------------------------------------
    # Слишком много комбинаций
    # -----------------------------------------------------

    total = len(alphabet) ** len(
        positions
    )

    # -----------------------------------------------------
    # Полный перебор для небольшого пространства
    # -----------------------------------------------------

    if total <= limit:

        counter = 0

        for values in itertools.product(
            alphabet,
            repeat=len(positions),
        ):

            chars = list(
                mask
            )

            for index, value in zip(
                positions,
                values,
            ):

                chars[index] = value

            candidate = "".join(
                chars
            )

            if not is_valid_username(
                candidate
            ):
                continue

            yield candidate

            counter += 1

            if counter >= limit:
                return

        return

    # -----------------------------------------------------
    # Случайная выборка
    # -----------------------------------------------------

    seen: set[str] = set()

    while len(seen) < limit:

        chars = list(
            mask
        )

        for index in positions:

            chars[index] = random.choice(
                alphabet
            )

        candidate = "".join(
            chars
        )

        if not is_valid_username(
            candidate
        ):
            continue

        if candidate in seen:
            continue

        seen.add(
            candidate
        )

        yield candidate


# =========================================================
# PREFIX
# =========================================================

def generate_prefix_candidates(
    prefix: str,
    length: int,
    *,
    limit: int = DEFAULT_LIMIT,
) -> Iterator[str]:

    prefix = normalize_username(
        prefix
    )

    if length < len(prefix):
        return

    if not is_valid_username(
        prefix,
        min_length=1,
        max_length=32,
    ):
        return

    remaining = (
        length
        - len(prefix)
    )

    if remaining == 0:

        yield prefix
        return

    alphabet = LETTERS

    total = len(alphabet) ** remaining

    # -----------------------------------------------------
    # FULL ENUMERATION
    # -----------------------------------------------------

    if total <= limit:

        counter = 0

        for values in itertools.product(
            alphabet,
            repeat=remaining,
        ):

            candidate = (
                prefix
                + "".join(values)
            )

            yield candidate

            counter += 1

            if counter >= limit:
                return

        return

    # -----------------------------------------------------
    # RANDOM
    # -----------------------------------------------------

    seen: set[str] = set()

    while len(seen) < limit:

        suffix = "".join(
            random.choice(alphabet)
            for _ in range(remaining)
        )

        candidate = (
            prefix
            + suffix
        )

        if candidate in seen:
            continue

        seen.add(
            candidate
        )

        yield candidate


# =========================================================
# SUFFIX
# =========================================================

def generate_suffix_candidates(
    suffix: str,
    length: int,
    *,
    limit: int = DEFAULT_LIMIT,
) -> Iterator[str]:

    suffix = normalize_username(
        suffix
    )

    if length < len(suffix):
        return

    remaining = (
        length
        - len(suffix)
    )

    alphabet = LETTERS

    if remaining == 0:

        yield suffix
        return

    total = len(alphabet) ** remaining

    if total <= limit:

        counter = 0

        for values in itertools.product(
            alphabet,
            repeat=remaining,
        ):

            candidate = (
                "".join(values)
                + suffix
            )

            if not is_valid_username(
                candidate
            ):
                continue

            yield candidate

            counter += 1

            if counter >= limit:
                return

        return

    seen: set[str] = set()

    while len(seen) < limit:

        prefix = "".join(
            random.choice(alphabet)
            for _ in range(remaining)
        )

        candidate = (
            prefix
            + suffix
        )

        if not is_valid_username(
            candidate
        ):
            continue

        if candidate in seen:
            continue

        seen.add(
            candidate
        )

        yield candidate


# =========================================================
# MAIN GENERATOR
# =========================================================

def generate_candidates(
    length: int,
    limit: int = DEFAULT_LIMIT,
    *,
    mode: str = "random",
    mask: str | None = None,
    prefix: str | None = None,
    suffix: str | None = None,
    dictionary: Iterable[str] | None = None,
    letters_only: bool = False,
    allow_digits: bool = True,
    allow_underscore: bool = True,
) -> Iterator[str]:

    limit = min(
        max(
            0,
            limit,
        ),
        MAX_LIMIT,
    )

    if limit == 0:
        return

    # -----------------------------------------------------
    # MASK
    # -----------------------------------------------------

    if mask:

        yield from generate_mask_candidates(
            mask,
            limit=limit,
        )

        return

    # -----------------------------------------------------
    # PREFIX
    # -----------------------------------------------------

    if prefix:

        yield from generate_prefix_candidates(
            prefix,
            length,
            limit=limit,
        )

        return

    # -----------------------------------------------------
    # SUFFIX
    # -----------------------------------------------------

    if suffix:

        yield from generate_suffix_candidates(
            suffix,
            length,
            limit=limit,
        )

        return

    # -----------------------------------------------------
    # DICTIONARY
    # -----------------------------------------------------

    if mode == "dictionary":

        words = (
            dictionary
            if dictionary is not None
            else DEFAULT_DICTIONARY
        )

        yield from generate_dictionary_candidates(
            words,
            min_length=length,
            max_length=length,
            limit=limit,
        )

        return

    # -----------------------------------------------------
    # RANDOM
    # -----------------------------------------------------

    yield from generate_random_candidates(
        length=length,
        limit=limit,
        letters_only=letters_only,
        allow_digits=allow_digits,
        allow_underscore=allow_underscore,
    )


# =========================================================
# LIST HELPER
# =========================================================

def generate_candidate_list(
    length: int,
    limit: int = DEFAULT_LIMIT,
    **kwargs,
) -> list[str]:

    return list(
        generate_candidates(
            length=length,
            limit=limit,
            **kwargs,
        )
    )
