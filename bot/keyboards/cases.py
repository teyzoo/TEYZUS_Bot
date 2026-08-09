from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


# =========================================================
# CASE LIST
# =========================================================

def cases_keyboard(
    cases,
) -> InlineKeyboardMarkup:

    buttons = []

    for case in cases:

        buttons.append(
            [
                InlineKeyboardButton(
                    text=(
                        f"🎁 {case.title} "
                        f"• ⭐ {case.price_stars}"
                    ),
                    callback_data=(
                        f"case:{case.id}"
                    ),
                )
            ]
        )

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


# =========================================================
# CASE DETAILS
# =========================================================

def case_open_keyboard(
    case_id: int,
) -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎁 Открыть кейс",
                    callback_data=(
                        f"case_open:{case_id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="cases",
                )
            ],
        ]
    )
