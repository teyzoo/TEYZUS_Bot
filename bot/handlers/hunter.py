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
    searches_left,
)
logger = logging.getLogger("TEYZUS.hunter")
router = Router()
hunter = HunterEngine()
# =========================================================
# USER
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
# =========================================================
# RESULT FORMAT
# =========================================================
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
    text = (
        f"{title}\n\n"
    )
    for index, result in enumerate(
        results,
        start=1,
    ):
        text += (
            f"<b>#{index}</b>\n"
            f"{format_result(result)}\n\n"
        )
    return text
# =========================================================
# LIMIT
# =========================================================
def allowed_amount(
    user,
    requested: int,
) -> int:
    if is_premium(user):
        return requested
    reset_daily_counter_if_needed(
        user
    )
    remaining = searches_left(
        user
    )
    if remaining is None:
        return requested
    return min(
        requested,
        remaining,
    )
async def ensure_search_allowed(
    message: Message,
    user,
) -> bool:
    if user is None:
        await message.answer(
            "❌ Профиль пользователя не найден.\n"
            "Попробуй снова через /start."
        )
        return False
    reset_daily_counter_if_needed(
        user
    )
    if can_search(user):
        return True
    await message.answer(
        "🚫 <b>Дневной лимит исчерпан.</b>\n\n"
        "Бесплатный пользователь может "
        "найти до <b>5 свободных username "
        "в сутки</b>.\n\n"
        "💎 <b>TEYZUS Premium</b>\n"
        "♾️ Безлимитный поиск\n"
        "🔤 5 символов\n"
        "📖 Dictionary\n"
        "🎯 Mask Search\n"
        "🚨 Trap",
        parse_mode="HTML",
    )
    return False
# =========================================================
# SEARCH EXECUTION
# =========================================================
async def execute_search(
    message: Message,
    session: AsyncSession,
    user,
    search,
    requested_amount: int,
    title: str,
) -> None:
    amount = allowed_amount(
        user,
        requested_amount,
    )
    if amount <= 0:
        await message.answer(
            "🚫 <b>Лимит поиска исчерпан.</b>\n\n"
            "💎 TEYZUS Premium открывает "
            "♾️ безлимитный поиск.",
            parse_mode="HTML",
        )
        return
    progress = await message.answer(
        "🔎 <b>TEYZUS Hunter</b>\n\n"
        "⚙️ Генерирую красивые username...\n"
        "⏳ Проверяю Telegram...\n"
        "⏳ Проверяю t.me...",
        parse_mode="HTML",
    )
    try:
        results = await search(
            amount=amount
        )
    except Exception:
        logger.exception(
            "Hunter search failed"
        )
        try:
            await progress.delete()
        except Exception:
            pass
        await message.answer(
            "⚠️ <b>Ошибка Hunter.</b>\n\n"
            "Попробуй ещё раз.",
            parse_mode="HTML",
        )
        return
    try:
        await progress.delete()
    except Exception:
        pass
    found_count = len(
        results
    )
    # -----------------------------------------------------
    # Учитываем только реально найденные username.
    # -----------------------------------------------------
    if found_count > 0:
        await register_successful_search(
            session=session,
            user=user,
            found_count=found_count,
        )
    await message.answer(
        format_results(
            results,
            title,
        ),
        parse_mode="HTML",
    )
    # -----------------------------------------------------
    # LIMIT STATUS
    # -----------------------------------------------------
    if is_premium(user):
        await message.answer(
            "💎 Premium: <b>♾️ безлимитный поиск</b>",
            parse_mode="HTML",
        )
    else:
        reset_daily_counter_if_needed(
            user
        )
        remaining = searches_left(
            user
        )
        await message.answer(
            "🔢 Лимит сегодня: "
            f"<b>{remaining}/5</b>",
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
        "🔎 <b>6 SYMBOL HUNTER</b>\n\n"
        "TEYZUS сам генерирует красивые "
        "username и проверяет их "
        "доступность.\n\n"
        "Можно указать от "
        "<b>1 до 100</b> результатов.\n\n"
        "Для Free действует лимит "
        "<b>5 найденных username в сутки</b>.",
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
    try:
        requested = int(
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
    if not 1 <= requested <= 100:
        await message.answer(
            "❌ Количество должно быть "
            "от 1 до 100."
        )
        return
    await state.clear()
    async with get_session() as session:
        user = await get_current_user(
            message,
            session,
        )
        if not await ensure_search_allowed(
            message,
            user,
        ):
            return
        await execute_search(
            message=message,
            session=session,
            user=user,
            search=lambda amount:
                hunter.search(
                    length=6,
                    amount=amount,
                ),
            requested_amount=requested,
            title="🔎 <b>6 SYMBOL HUNTER</b>",
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
        "💎 <b>5 SYMBOL HUNTER</b>\n\n"
        "Поиск 5-символьных username.\n\n"
        "🔒 Только для TEYZUS Premium.\n\n"
        "Количество: <b>1–100</b>.",
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
    try:
        requested = int(
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
    if not 1 <= requested <= 100:
        await message.answer(
            "❌ Количество должно быть "
            "от 1 до 100."
        )
        return
    await state.clear()
    async with get_session() as session:
        user = await get_current_user(
            message,
            session,
        )
        if user is None:
            await message.answer(
                "❌ Профиль не найден."
            )
            return
        if not is_premium(user):
            await message.answer(
                "💎 <b>TEYZUS Premium</b>\n\n"
                "5-символьный поиск доступен "
                "только Premium.",
                parse_mode="HTML",
            )
            return
        await execute_search(
            message=message,
            session=session,
            user=user,
            search=lambda amount:
                hunter.premium(
                    length=5,
                    amount=amount,
                ),
            requested_amount=requested,
            title="💎 <b>5 SYMBOL PREMIUM</b>",
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
        "📖 <b>DICTIONARY HUNTER</b>\n\n"
        "TEYZUS ищет реальные слова "
        "и красивые коммерческие username.\n\n"
        "🔒 Только Premium.\n\n"
        "Укажи длину от <b>5 до 32</b>.",
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
    async with get_session() as session:
        user = await get_current_user(
            message,
            session,
        )
        if user is None:
            await message.answer(
                "❌ Профиль не найден."
            )
            return
        if not is_premium(user):
            await message.answer(
                "💎 <b>TEYZUS Premium</b>\n\n"
                "Dictionary доступен "
                "только Premium.",
                parse_mode="HTML",
            )
            return
        await execute_search(
            message=message,
            session=session,
            user=user,
            search=lambda amount:
                hunter.dictionary(
                    length=length,
                    amount=amount,
                ),
            requested_amount=10,
            title="📖 <b>DICTIONARY HUNTER</b>",
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
        "🎯 <b>MASK HUNTER</b>\n\n"
        "Используй <code>?</code> "
        "для неизвестной буквы.\n\n"
        "Примеры:\n"
        "<code>?nova?</code>\n"
        "<code>v?l?r?</code>\n"
        "<code>?a??a?</code>\n\n"
        "🔒 Только Premium.",
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
    mask = (
        message.text.strip()
        if message.text
        else ""
    )
    if not validate_mask(mask):
        await message.answer(
            "❌ Неверная маска.\n\n"
            "Используй английские буквы "
            "и <code>?</code>.\n\n"
            "Длина: 5–32.",
            parse_mode="HTML",
        )
        return
    await state.clear()
    async with get_session() as session:
        user = await get_current_user(
            message,
            session,
        )
        if user is None:
            await message.answer(
                "❌ Профиль не найден."
            )
            return
        if not is_premium(user):
            await message.answer(
                "💎 <b>TEYZUS Premium</b>\n\n"
                "Mask Search доступен "
                "только Premium.",
                parse_mode="HTML",
            )
            return
        await execute_search(
            message=message,
            session=session,
            user=user,
            search=lambda amount:
                hunter.mask(
                    mask=mask,
                    amount=amount,
                ),
            requested_amount=10,
            title="🎯 <b>MASK HUNTER</b>",
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
        "🔥 <b>POPULAR HUNTER</b>\n\n"
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
            "⚠️ Ошибка поиска."
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
        "💎 <b>EXPENSIVE HUNTER</b>\n\n"
        "⚙️ Ищу редкие и дорогие username...\n"
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
            "⚠️ Ошибка поиска."
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
