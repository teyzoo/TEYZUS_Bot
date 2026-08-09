from __future__ import annotations

from services.hunter.search_service import (
    FinalSearchResult,
)


def format_search_result(
    result: FinalSearchResult,
) -> str:

    return (
        "✅ <b>НИК НАЙДЕН!</b>\n"
        f"@{result.username}\n\n"
        f"├ 📖 Читабельность — "
        f"{result.readability:.1f}/10\n"
        f"├ 🤖 Beauty Score — "
        f"{result.beauty:.1f}/10\n"
        f"├ 💰 Примерная цена — "
        f"${result.price_min:,}"
        f"-"
        f"${result.price_max:,}\n"
        f"├ 📈 Ликвидность — "
        f"{result.beauty:.1f}/10\n"
        "└ ⚡️ Свободен"
    )


def format_search_results(
    results: list[FinalSearchResult],
) -> str:

    if not results:

        return (
            "😔 <b>Ничего не найдено.</b>\n\n"
            "Попробуй другой поиск."
        )

    blocks = []

    for result in results:

        blocks.append(
            format_search_result(
                result
            )
        )

    return "\n\n".join(
        blocks
    )
