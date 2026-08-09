from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.session import get_session
from services.shop import (
    get_shop_page,
)


router = Router(
    name="shop"
)


# =========================================================
# SHOP KEYBOARD
# =========================================================

def shop_keyboard():

    builder = InlineKeyboardBuilder()

    builder.button(
        text="🏪 Открыть TEYZUS SHOP",
        callback_data="open_shop",
    )

    builder.button(
        text="🛒 Корзина",
        callback_data="shop_cart",
    )

    builder.button(
        text="❤️ Избранное",
        callback_data="shop_favorites",
    )

    builder.adjust(1)

    return builder.as_markup()


# =========================================================
# SHOP
# =========================================================

@router.callback_query(
    F.data == "open_shop"
)
async def open_shop(
    callback: CallbackQuery,
):

    await callback.answer()

    await callback.message.answer(
        "🏪 <b>TEYZUS SHOP</b>\n\n"
        "Открой Mini App, чтобы покупать "
        "и продавать Telegram username.",
        reply_markup=shop_keyboard(),
    )


# =========================================================
# SHOP LIST
# =========================================================

@router.callback_query(
    F.data == "shop_list"
)
async def shop_list(
    callback: CallbackQuery,
):

    await callback.answer()

    async with get_session() as session:

        data = await get_shop_page(
            session=session,
            user_id=0,
            search="",
            category="all",
            sort="new",
            page=1,
            per_page=10,
        )

    if not data["items"]:

        await callback.message.answer(
            "🏪 <b>TEYZUS SHOP</b>\n\n"
            "Пока опубликованных объявлений нет."
        )

        return

    lines = [
        "🏪 <b>TEYZUS SHOP</b>",
        "",
    ]

    for item in data["items"]:

        lines.append(
            f"@{item['username']} — "
            f"<b>{item['price_rub']:,} ₽</b>"
        )

    await callback.message.answer(
        "\n".join(lines)
    )
