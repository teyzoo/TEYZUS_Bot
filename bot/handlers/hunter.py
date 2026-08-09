from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from database.models import User
from database.session import async_session_factory

from services.hunter.search_service import (
    hunter_search_service,
)

router = Router()


# =========================================================
# USER
# =========================================================

async def get_user(
    telegram_id: int,
) -> User | None:

    async with async_session_factory() as session:

        result = await session.execute(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        return result.scalar_one_or_none()


# =========================================================
# HUNTER MENU
# =========================================================

@router.callback_query(
    F.data == "hunter"
)
async def hunter_menu(
    callback: CallbackQuery,
    state: FSMContext,
):

    await state.clear()

    await callback.message.answer(
        "🔎 <b>TEYZUS HUNTER</b>\n\n"
        "Выбери режим поиска:\n\n"
        "6️⃣ <b>6 символов</b>\n"
        "💎 <b>5 символов</b> — Premium\n"
        "💰 <b>Дорогие</b>\n"
        "📖 <b>Dictionary</b>\n"
        "🎯 <b>Mask</b>\n"
        "🔥 <b>Popular</b>",
        parse_mode="HTML",
    )

    await callback.answer()


# =========================================================
# 6 CHARACTERS
# =========================================================

@router.callback_query(
    F.data == "hunter_6"
)
async def hunter_6(
    callback: CallbackQuery,
):

    user = await get_user(
        callback.from_user.id
    )

    if user is None:
        await callback.answer(
            "❌ Пользователь не найден.",
            show_alert=True,
        )
        return

    await callback.message.answer(
        "🔎 <b>Ищу username из 6 символов...</b>\n\n"
        "Проверяю доступность через Hunter.",
        parse_mode="HTML",
    )

    async with async_session_factory() as session:

        response = await hunter_search_service.six_characters(
            session=session,
            user=user,
            amount=10,
        )

    if not response.success:

        await callback.message.answer(
            response.message,
            parse_mode="HTML",
        )

        await callback.answer()

        return

    await callback.message.answer(
        format_results(response.results),
        parse_mode="HTML",
    )

    await callback.message.answer(
        response.message,
        parse_mode="HTML",
    )

    await callback.answer()


# =========================================================
# 5 CHARACTERS
# =========================================================

@router.callback_query(
    F.data == "hunter_5"
)
async def hunter_5(
    callback: CallbackQuery,
):

    user = await get_user(
        callback.from_user.id
    )

    if user is None:
        await callback.answer(
            "❌ Пользователь не найден.",
            show_alert=True,
        )
        return

    await callback.message.answer(
        "💎 <b>Premium Hunter</b>\n\n"
        "Ищу username из 5 символов...",
        parse_mode="HTML",
    )

    async with async_session_factory() as session:

        response = await hunter_search_service.five_characters(
            session=session,
            user=user,
            amount=10,
        )

    await callback.message.answer(
        response.message
        if not response.success
        else format_results(response.results),
        parse_mode="HTML",
    )

    if response.success:

        await callback.message.answer(
            response.message,
            parse_mode="HTML",
        )

    await callback.answer()


# =========================================================
# EXPENSIVE
# =========================================================

@router.callback_query(
    F.data == "hunter_expensive"
)
async def hunter_expensive(
    callback: CallbackQuery,
):

    user = await get_user(
        callback.from_user.id
    )

    if user is None:
        await callback.answer(
            "❌ Пользователь не найден.",
            show_alert=True,
        )
        return

    await callback.message.answer(
        "💰 <b>Дорогие username</b>\n\n"
        "Ищу наиболее ценные варианты...",
        parse_mode="HTML",
    )

    async with async_session_factory() as session:

        response = await hunter_search_service.expensive(
            session=session,
            user=user,
            length=6,
            amount=10,
        )

    await send_response(
        callback.message,
        response,
    )

    await callback.answer()


# =========================================================
# POPULAR
# =========================================================

@router.callback_query(
    F.data == "hunter_popular"
)
async def hunter_popular(
    callback: CallbackQuery,
):

    user = await get_user(
        callback.from_user.id
    )

    if user is None:
        await callback.answer(
            "❌ Пользователь не найден.",
            show_alert=True,
        )
        return

    await callback.message.answer(
        "🔥 <b>Popular Hunter</b>\n\n"
        "Ищу наиболее популярные username...",
        parse_mode="HTML",
    )

    async with async_session_factory() as session:

        response = await hunter_search_service.popular(
            session=session,
            user=user,
            length=6,
            amount=10,
        )

    await send_response(
        callback.message,
        response,
    )

    await callback.answer()


# =========================================================
# DICTIONARY
# =========================================================

@router.callback_query(
    F.data == "hunter_dictionary"
)
async def hunter_dictionary(
    callback: CallbackQuery,
):

    user = await get_user(
        callback.from_user.id
    )

    if user is None:
        await callback.answer(
            "❌ Пользователь не найден.",
            show_alert=True,
        )
        return

    await callback.message.answer(
        "📖 <b>Dictionary Hunter</b>\n\n"
        "Ищу красивые английские слова...",
        parse_mode="HTML",
    )

    # Пока используем базовый словарь.
    # Позже он будет загружаться из database/cache.

    words = [
        "planet",
        "rocket",
        "future",
        "hunter",
        "market",
        "gaming",
        "crypto",
        "global",
        "master",
        "digital",
        "system",
        "vision",
        "studio",
        "network",
        "premium",
    ]

    async with async_session_factory() as session:

        response = await hunter_search_service.dictionary(
            session=session,
            user=user,
            words=words,
            length=6,
            amount=10,
        )

    await send_response(
        callback.message,
        response,
    )

    await callback.answer()


# =========================================================
# MASK
# =========================================================

@router.callback_query(
    F.data == "hunter_mask"
)
async def hunter_mask_start(
    callback: CallbackQuery,
    state: FSMContext,
):

    await state.set_state(
        "hunter_mask"
    )

    await callback.message.answer(
        "🎯 <b>Mask Hunter</b>\n\n"
        "Введи маску username.\n\n"
        "Например:\n"
        "<code>te??us</code>\n"
        "<code>?rypto</code>\n"
        "<code>??????</code>",
        parse_mode="HTML",
    )

    await callback.answer()


# =========================================================
# MASK INPUT
# =========================================================

@router.message(
    F.text,
    lambda message: message.text is not None,
)
async def hunter_mask_input(
    message: Message,
    state: FSMContext,
):

    current_state = await state.get_state()

    if current_state != "hunter_mask":
        return

    user = await get_user(
        message.from_user.id
    )

    if user is None:

        await state.clear()

        await message.answer(
            "❌ Пользователь не найден."
        )

        return

    mask = message.text.strip()

    if len(mask) < 5:

        await message.answer(
            "❌ Маска должна содержать минимум 5 символов."
        )

        return

    await state.clear()

    await message.answer(
        "🎯 <b>Проверяю маску...</b>\n\n"
        f"<code>{mask}</code>",
        parse_mode="HTML",
    )

    async with async_session_factory() as session:

        response = await hunter_search_service.mask(
            session=session,
            user=user,
            mask=mask,
            amount=10,
        )

    await send_response(
        message,
        response,
    )


# =========================================================
# SEND RESPONSE
# =========================================================

async def send_response(
    message: Message,
    response,
) -> None:

    if not response.success:

        await message.answer(
            response.message,
            parse_mode="HTML",
        )

        return

    await message.answer(
        format_results(
            response.results
        ),
        parse_mode="HTML",
    )

    await message.answer(
        response.message,
        parse_mode="HTML",
    )


# =========================================================
# FORMAT RESULTS
# =========================================================

def format_results(
    results,
) -> str:

    if not results:

        return (
            "😔 <b>Ничего не найдено.</b>"
        )

    text = (
        "✅ <b>НАЙДЕННЫЕ USERNAME</b>\n\n"
    )

    for index, result in enumerate(
        results,
        start=1,
    ):

        username = getattr(
            result,
            "username",
            "unknown",
        )

        score = getattr(
            result,
            "beauty_score",
            0,
        )

        liquidity = getattr(
            result,
            "liquidity",
            0,
        )

        price_min = getattr(
            result,
            "price_min",
            0,
        )

        price_max = getattr(
            result,
            "price_max",
            0,
        )

        text += (
            f"<b>{index}.</b> "
            f"@{username}\n"
            f"⭐ Красота: <b>{score}/10</b>\n"
            f"💧 Ликвидность: <b>{liquidity}/10</b>\n"
            f"💰 Цена: "
            f"<b>{price_min}–{price_max} ₽</b>\n\n"
        )

    return text
