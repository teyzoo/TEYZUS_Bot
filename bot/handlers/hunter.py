from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    Message,
)
from aiogram.fsm.context import FSMContext

from services.hunter.engine import (
    HunterEngine,
    HunterResult,
)
from services.hunter.masks import (
    validate_mask,
)

from bot.states.common import (
    HunterSearchState,
    HunterMaskState,
)


router = Router()

hunter = HunterEngine()


# =========================================================
# FORMAT RESULT
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
            "😔 <b>Ничего не найдено.</b>\n\n"
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
        "варианты, отфильтрует мусор и "
        "проверит доступность.\n\n"
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

    progress = await message.answer(
        "🔎 <b>TEYZUS Hunter</b>\n\n"
        "⚙️ Генерирую красивые username...\n"
        "⏳ Проверяю доступность...",
        parse_mode="HTML",
    )

    results = await hunter.search(
        length=6,
        amount=limit,
    )

    await progress.delete()

    await message.answer(
        format_results(
            results,
            "🔎 <b>6 SYMBOL HUNTER</b>",
        ),
        parse_mode="HTML",
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
        "TEYZUS будет искать короткие "
        "и красивые username.\n\n"
        "Укажи количество от "
        "<b>1 до 100</b>.",
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

    progress = await message.answer(
        "💎 <b>Premium Hunter</b>\n\n"
        "⚙️ Генерирую 5-символьные варианты...\n"
        "⏳ Проверяю доступность...",
        parse_mode="HTML",
    )

    results = await hunter.premium(
        length=5,
        amount=limit,
    )

    await progress.delete()

    await message.answer(
        format_results(
            results,
            "💎 <b>5 SYMBOL PREMIUM HUNTER</b>",
        ),
        parse_mode="HTML",
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
        "слова из словаря.\n\n"
        "Введи длину username:\n"
        "<code>5</code> — 5 символов\n"
        "<code>6</code> — 6 символов\n"
        "<code>7</code> — 7 символов",
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

    progress = await message.answer(
        "📖 <b>Dictionary Hunter</b>\n\n"
        "🔎 Ищу словарные username...",
        parse_mode="HTML",
    )

    results = await hunter.dictionary(
        length=length,
        amount=10,
    )

    await progress.delete()

    await message.answer(
        format_results(
            results,
            "📖 <b>DICTIONARY HUNTER</b>",
        ),
        parse_mode="HTML",
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
        "Длина: <b>5–32</b> символа.",
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
            "и символ <code>?</code>.\n\n"
            "Длина: 5–32 символа.",
            parse_mode="HTML",
        )

        return

    await state.clear()

    progress = await message.answer(
        "🎯 <b>Mask Hunter</b>\n\n"
        f"Маска: <code>{mask}</code>\n\n"
        "⚙️ Генерирую варианты...\n"
        "⏳ Проверяю доступность...",
        parse_mode="HTML",
    )

    results = await hunter.mask(
        mask=mask,
        amount=10,
    )

    await progress.delete()

    await message.answer(
        format_results(
            results,
            "🎯 <b>MASK HUNTER</b>",
        ),
        parse_mode="HTML",
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
        "⚙️ Ищу красивые username...",
        parse_mode="HTML",
    )

    results = await hunter.popular(
        amount=10
    )

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
        "⚙️ Ищу самые перспективные "
        "username...",
        parse_mode="HTML",
    )

    results = await hunter.expensive(
        amount=10
    )

    await progress.delete()

    await callback.message.answer(
        format_results(
            results,
            "💎 <b>EXPENSIVE USERNAMES</b>",
        ),
        parse_mode="HTML",
    )

    await callback.answer()
