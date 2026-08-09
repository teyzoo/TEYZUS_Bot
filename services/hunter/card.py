from services.hunter.pricing import (
    estimate_price,
)
from services.hunter.scoring import (
    score_username,
)


def build_username_card(
    username: str,
    available: bool = True,
) -> str:

    score = score_username(
        username
    )

    minimum, maximum = estimate_price(
        username
    )

    status = (
        "⚡️ Свободен"
        if available
        else "🔴 Занят"
    )

    return (
        "🤖 TEYZUS AI\n\n"
        "✅ НИК НАЙДЕН!\n"
        f"@{username}\n\n"
        "📖 Читабельность\n"
        f"{score.readability}/10\n\n"
        "🤖 AI Score\n"
        f"{score.total}/10\n\n"
        "💰 Примерная цена\n"
        f"${minimum}-${maximum}\n\n"
        "📈 Ликвидность\n"
        f"{score.liquidity}/10\n\n"
        f"{status}"
    )
