from __future__ import annotations
import logging
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession
from bot.states.common import (
    HunterMaskState,
    HunterSearchState,
)
from database.repositories import get_user
from database.session import get_session
from services.hunter.engine import (
    HunterEngine,
    HunterResult,
)
from services.hunter.masks import validate_mask
from services.premium import is_premium
from services.search_limits import (
    can_search,
    limit_text,
    register_successful_search,
    reset_daily_counter_if_needed,
)
logger = logging.getLogger("TEYZUS.hunter")
router = Router()
hunter = HunterEngine()
# =========================================================
# HELPERS
# =========================================================
async def get_current_user(
    message: Message,
    session: AsyncSession,
):
    if not message.from_user:
        return None
    return await get_user(
        session=session,
        telegram_id=message.from_user.id,
    )
def format_result(
    result: HunterResult,
) -> str:
    return (
        "✅ <b>НИК НАЙДЕН!</b>\n\n"
        f"<code>@{result.username}</code>\n\n"
        f"├ 📖 Читабельность — "
        f"{result.readability:.1f}/10\n"
        f"├ 🤖 Beauty Score — "
        f"{result.beauty_score:.1f}/10\n"
        f"├ 💎 Редкость — "
        f"{result.rarity:.1f}/10\n"
        f"├ 🏷 Брендовость — "
        f"{result.brand:.1f}/10\n"
        f"├ 📈 Ликвидность — "
        f"{result.liquidity:.1f}/10\n"
        f"├ 💰 Цена — "
        f"${result.price_min:,}"
        f"-"
        f"${result.price_max:,}\n"
        "└ ⚡️ Свободен"
    )
def format_results(
    results: list[HunterResult],
    title: str,
) -> str:
    if not results:
        return (
            "😔 <b>Свободных красивых username "
            "не найдено.</b>\n\n"
            "Попробуй другой режим поиска."
        )
    text = f"{title}\n\n"
    for index, result in enumerate(
        results,
        start=1,
    ):
        text += (
            f"<b>#{index}</b>\n"
            f"{format_result(result)}\n\n"
        )
    return text
async def check_free_limit(
    message: Message,
    user,
) -> bool:
    if user is None:
        await message.answer(
            "❌ Профиль пользователя не найден.\n"
            "Попробуй снова через /start."
        )
        return False
    reset_daily_counter_if_needed(user)
    if can_search(user):
        return True
    await message.answer(
        "🚫 <b>Дневной лимит исчерпан.</b>\n\n"
        "Бесплатный пользователь может "
        "найти до <b>5 свободных username "
        "в сутки</b>.\n\n"
        "💎 TEYZUS Premium открывает "
        "<b>♾️ безлимитный поиск</b>.",
        parse_mode="HTML",
    )
    return False
async def run_search_and_register(
    message: Message,
    session: AsyncSession,
    user,
    search_coro,
):
    progress = await message.answer(
        "🔎 <b>TEYZUS Hunter</b>\n\n"
        "⚙️ Генерирую красивые username...\n"
        "⏳ Проверяю доступность...",
        parse_mode="HTML",
    )
    try:
        results = await search_coro
    except Exception:
        logger.exception(
            "Hunter search error"
        )
        try:
            await progress.delete()
        except Exception:
            pass
        await message.answer(
            "⚠️ <b>Произошла ошибка поиска.</b>\n\n"
            "Попробуй ещё раз.",
            parse_mode="HTML",
        )
        return
    try:
        await progress.delete()
    except Exception:
        pass
    found_count = len(results)
    if found_count > 0:
        await register_successful_search(
            session=session,
            user=user,
            found_count=found_count,
        )
    await message.answer(
        format_results(
            results,
            "🔎 <b>TEYZUS HUNTER</b>",
        ),
        parse_mode="HTML",
    )
    if is_premium(user):
        footer = (
            "\n💎 Premium: <b>♾️ безлимитный поиск</b>"
        )
    else:
        remaining = max(
            0,
            5 - user.successful_searches_today,
        )
        footer = (
            "\n🔢 Осталось сегодня: "
            f"<b>{remaining}/5</b>"
        )
    await message.answer(
        footer,
        parse_mode="HTML",
    )
# =========================================================
# 6 SYMBOL
# =========================================================
@router.callback_query(
    F.data == "hunter_6"
)
async def hunter_6(
    callback: CallbackQuery,
    state: FSMContext,
):
    await state.clear()
    await state.set_state(
        HunterSearchState.length_6
    )
    await callback.message.answer(
        "🔎 <b>Поиск красивых username</b>\n\n"
        "Длина: <b>6 символов</b>\n\n"
        "TEYZUS сам создаст красивые "
        "варианты, отфильтрует мусор "
        "и проверит доступность.\n\n"
        "Отправь количество результатов "
        "от <b>1 до 100</b>.",
        parse_mode="HTML",
    )
    await callback.answer()
@router.message(
    HunterSearchState.length_6
)
async def hunter_6_count(
    message: Message,
    state: FSMContext,
):
    async with get_session() as session:
        user = await get_current_user(
            message,
            session,
        )
        if not await check_free_limit(
            message,
            user,
        ):
            await state.clear()
            return
        try:
            limit = int(
                message.text.strip()
            )
        except (
            ValueError,
            AttributeError,
        ):
            await message.answer(
                "❌ Введи число от 1 до 100."
            )
            return
        if not 1 <= limit <= 100:
            await message.answer(
                "❌ Количество должно быть "
                "от 1 до 100."
            )
            return
        await state.clear()
        await run_search_and_register(
            message=message,
            session=session,
            user=user,
            search_coro=hunter.search(
                length=6,
                amount=limit,
            ),
        )
# =========================================================
# 5 SYMBOL PREMIUM
# =========================================================
@router.callback_query(
    F.data == "hunter_5"
)
async def hunter_5(
    callback: CallbackQuery,
    state: FSMContext,
):
    await state.clear()
    await state.set_state(
        HunterSearchState.length_5
    )
    await callback.message.answer(
        "💎 <b>Premium Hunter</b>\n\n"
        "Длина: <b>5 символов</b>\n\n"
        "Доступно только Premium.\n\n"
        "Укажи количество результатов "
        "от <b>1 до 100</b>.",
        parse_mode="HTML",
    )
    await callback.answer()
@router.message(
    HunterSearchState.length_5
)
async def hunter_5_count(
    message: Message,
    state: FSMContext,
):
    async with get_session() as session:
        user = await get_current_user(
            message,
            session,
        )
        if user is None:
            await message.answer(
                "❌ Профиль не найден."
            )
            await state.clear()
            return
        if not is_premium(user):
            await message.answer(
                "💎 <b>Эта функция доступна "
                "только TEYZUS Premium.</b>\n\n"
                "5-символьный поиск входит "
                "в Premium.",
                parse_mode="HTML",
            )
            await state.clear()
            return
        try:
            limit = int(
                message.text.strip()
            )
        except (
            ValueError,
            AttributeError,
        ):
            await message.answer(
                "❌ Введи число от 1 до 100."
            )
            return
        if not 1 <= limit <= 100:
            await message.answer(
                "❌ Количество должно быть "
                "от 1 до 100."
            )
            return
        await state.clear()
        await run_search_and_register(
            message=message,
            session=session,
            user=user,
            search_coro=hunter.premium(
                length=5,
                amount=limit,
            ),
        )
# =========================================================
# DICTIONARY
# =========================================================
@router.callback_query(
    F.data == "hunter_dictionary"
)
async def hunter_dictionary(
    callback: CallbackQuery,
    state: FSMContext,
):
    await state.clear()
    await state.set_state(
        HunterSearchState.dictionary
    )
    await callback.message.answer(
        "📖 <b>Dictionary Search</b>\n\n"
        "TEYZUS будет искать реальные "
        "слова и красивые коммерческие "
        "username.\n\n"
        "Введи длину:\n\n"
        "<code>5</code>\n"
        "<code>6</code>\n"
        "<code>7</code>\n\n"
        "Функция доступна Premium.",
        parse_mode="HTML",
    )
    await callback.answer()
@router.message(
    HunterSearchState.dictionary
)
async def hunter_dictionary_length(
    message: Message,
    state: FSMContext,
):
    async with get_session() as session:
        user = await get_current_user(
            message,
            session,
        )
        if user is None:
            await message.answer(
                "❌ Профиль не найден."
            )
            await state.clear()
            return
        if not is_premium(user):
            await message.answer(
                "💎 <b>Dictionary Hunter</b>\n\n"
                "Эта функция доступна "
                "только Premium.",
                parse_mode="HTML",
            )
            await state.clear()
            return
        try:
            length = int(
                message.text.strip()
            )
        except (
            ValueError,
            AttributeError,
        ):
            await message.answer(
                "❌ Введи длину от 5 до 32."
            )
            return
        if not 5 <= length <= 32:
            await message.answer(
                "❌ Длина должна быть "
                "от 5 до 32."
            )
            return
        await state.clear()
        await run_search_and_register(
            message=message,
            session=session,
            user=user,
            search_coro=hunter.dictionary(
                length=length,
                amount=10,
            ),
        )
# =========================================================
# MASK
# =========================================================
@router.callback_query(
    F.data == "hunter_mask"
)
async def hunter_mask(
    callback: CallbackQuery,
    state: FSMContext,
):
    await state.clear()
    await state.set_state(
        HunterMaskState.mask
    )
    await callback.message.answer(
        "🎯 <b>Поиск по маске</b>\n\n"
        "Используй <code>?</code> "
        "для неизвестной буквы.\n\n"
        "Примеры:\n"
        "<code>?nova?</code>\n"
        "<code>v?l?r?</code>\n"
        "<code>?a??a?</code>\n\n"
        "Длина: <b>5–32</b>.\n\n"
        "Функция доступна Premium.",
        parse_mode="HTML",
    )
    await callback.answer()
@router.message(
    HunterMaskState.mask
)
async def hunter_mask_input(
    message: Message,
    state: FSMContext,
):
    async with get_session() as session:
        user = await get_current_user(
            message,
            session,
        )
        if user is None:
            await message.answer(
                "❌ Профиль не найден."
            )
            await state.clear()
            return
        if not is_premium(user):
            await message.answer(
                "💎 <b>Mask Hunter</b>\n\n"
                "Эта функция доступна "
                "только Premium.",
                parse_mode="HTML",
            )
            await state.clear()
            return
        mask = (
            message.text.strip()
            if message.text
            else ""
        )
        if not validate_mask(mask):
            await message.answer(
                "❌ Неверная маска.\n\n"
                "Используй английские буквы "
                "и символ <code>?</code>.\n\n"
                "Длина: 5–32.",
                parse_mode="HTML",
            )
            return
        await state.clear()
        await run_search_and_register(
            message=message,
            session=session,
            user=user,
            search_coro=hunter.mask(
                mask=mask,
                amount=10,
            ),
        )
# =========================================================
# POPULAR
# =========================================================
@router.callback_query(
    F.data == "hunter_popular"
)
async def hunter_popular(
    callback: CallbackQuery,
):
    progress = await callback.message.answer(
        "🔥 <b>Popular Hunter</b>\n\n"
        "⚙️ Ищу красивые username...\n"
        "⏳ Проверяю доступность...",
        parse_mode="HTML",
    )
    try:
        results = await hunter.popular(
            amount=10
        )
    except Exception:
        logger.exception(
            "Popular hunter error"
        )
        await progress.delete()
        await callback.message.answer(
            "⚠️ Ошибка поиска.",
        )
        await callback.answer()
        return
    await progress.delete()
    await callback.message.answer(
        format_results(
            results,
            "🔥 <b>POPULAR USERNAMES</b>",
        ),
        parse_mode="HTML",
    )
    await callback.answer()
# =========================================================
# EXPENSIVE
# =========================================================
@router.callback_query(
    F.data == "hunter_expensive_6"
)
async def hunter_expensive(
    callback: CallbackQuery,
):
    progress = await callback.message.answer(
        "💎 <b>Expensive Hunter</b>\n\n"
        "⚙️ Ищу дорогие и перспективные "
        "username...\n"
        "⏳ Проверяю доступность...",
        parse_mode="HTML",
    )
    try:
        results = await hunter.expensive(
            amount=10
        )
    except Exception:
        logger.exception(
            "Expensive hunter error"
        )
        await progress.delete()
        await callback.message.answer(
            "⚠️ Ошибка поиска.",
        )
        await callback.answer()
        return
    await progress.delete()
    await callback.message.answer(
        format_results(
            results,
            "💎 <b>EXPENSIVE USERNAMES</b>",
        ),
        parse_mode="HTML",
    )
    await callback.answer()
