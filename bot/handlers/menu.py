from __future__ import annotations

from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from services.hunter.service import HunterService


router = Router()

hunter = HunterService()


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔎 Поиск",
                    callback_data="search",
                ),
                InlineKeyboardButton(
                    text="📋 Задания",
                    callback_data="tasks",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="💎 Premium",
                    callback_data="premium",
                ),
                InlineKeyboardButton(
                    text="👤 Профиль",
                    callback_data="profile",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🏪 TEYZUS SHOP",
                    web_app=None,
                    callback_data="shop",
                ),
            ],
        ]
    )


@router.message(F.text == "🏠 Меню")
async def menu_message(
    message: Message,
) -> None:
    await message.answer(
        "🏠 <b>TEYZUS</b>\n\n"
        "Выберите нужный раздел:",
        reply_markup=main_menu_keyboard(),
    )


@router.callback_query(F.data == "menu")
async def menu_callback(
    callback: CallbackQuery,
) -> None:
    await callback.answer()

    if callback.message is None:
        return

    await callback.message.edit_text(
        "🏠 <b>TEYZUS</b>\n\n"
        "Выберите нужный раздел:",
        reply_markup=main_menu_keyboard(),
    )


@router.callback_query(F.data == "shop")
async def shop_callback(
    callback: CallbackQuery,
) -> None:
    await callback.answer()

    if callback.message is None:
        return

    await callback.message.answer(
        "🏪 <b>TEYZUS SHOP</b>\n\n"
        "Магазин username находится в Mini App.\n\n"
        "Откройте Mini App через кнопку запуска магазина.",
    )


@router.callback_query(F.data == "search")
async def search_callback(
    callback: CallbackQuery,
) -> None:
    await callback.answer()

    if callback.message is None:
        return

    await callback.message.answer(
        "🔎 <b>Поиск username</b>\n\n"
        "Введите username для поиска.",
    )
