from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    Message,
)
from aiogram.fsm.context import FSMContext

from services.hunter.engine import HunterEngine
from services.hunter.filters import HunterFilters
from services.hunter.masks import validate_mask

from bot.states.common import (
    HunterSearchState,
    HunterMaskState,
)


router = Router()

hunter = HunterEngine()


# =========================================================
# 🔎 6 SYMBOL SEARCH
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
        "TEYZUS автоматически создаст "
        "красивые варианты и начнёт их проверку.\n\n"
        "Отправь количество результатов "
        "от <b>1 до 100</b>.",
        parse_mode="HTML",
    )

    await callback.answer()


# =========================================================
# 💎 EXPENSIVE
# =========================================================

@router.callback_query(
    F.data == "hunter_expensive_6"
)
async def hunter_expensive(
    callback: CallbackQuery,
    state: FSMContext,
):

    await state.clear()

    await state.set_state(
        HunterSearchState.expensive
    )

    await callback.message.answer(
        "💎 <b>Поиск дорогих username</b>\n\n"
        "Длина: <b>6 символов</b>\n\n"
        "TEYZUS будет отдавать приоритет "
        "редким, красивым и коммерческим именам.\n\n"
        "Сколько результатов показать?\n"
        "От <b>1 до 100</b>.",
        parse_mode="HTML",
    )

    await callback.answer()


# =========================================================
# 📖 DICTIONARY
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
        "словарные слова и красивые "
        "коммерческие варианты.\n\n"
        "Укажи длину username:\n\n"
        "Например:\n"
        "<code>5</code>\n"
        "<code>6</code>\n"
        "<code>7</code>",
        parse_mode="HTML",
    )

    await callback.answer()


# =========================================================
# 🔥 POPULAR
# =========================================================

@router.callback_query(
    F.data == "hunter_popular"
)
async def hunter_popular(
    callback: CallbackQuery,
):

    results = hunter.beautiful(
        length=6,
        limit=50,
    )

    if not results:
        await callback.message.answer(
            "😔 Подходящих username пока не найдено."
        )

        await callback.answer()
        return

    text = (
        "🔥 <b>Популярные username</b>\n\n"
    )

    for index, result in enumerate(
        results[:20],
        start=1,
    ):

        text += (
            f"{index}. "
            f"@{result.username} "
            f"— {result.beauty}/10\n"
        )

    text += (
        "\n"
        "Нажми «🔎 Поиск», чтобы запустить "
        "полную проверку доступности."
    )

    await callback.message.answer(
        text,
        parse_mode="HTML",
    )

    await callback.answer()


# =========================================================
# 💎 5 SYMBOL PREMIUM
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
        "Это Premium-функция.\n\n"
        "Укажи количество результатов "
        "от <b>1 до 100</b>.",
        parse_mode="HTML",
    )

    await callback.answer()


# =========================================================
# 🎯 MASK
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
        "для любой буквы.\n\n"
        "Примеры:\n\n"
        "<code>?nova?</code>\n"
        "<code>v?l?r?</code>\n"
        "<code>?a??a?</code>\n\n"
        "Длина маски: от 5 до 32 символов.",
        parse_mode="HTML",
    )

    await callback.answer()


# =========================================================
# 🔎 6 SYMBOL RESULT
# =========================================================

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

    await message.answer(
        "🔎 Генерирую красивые username..."
    )

    results = hunter.beautiful(
        length=6,
        limit=limit,
    )

    await state.clear()

    if not results:

        await message.answer(
            "😔 Подходящих вариантов не найдено."
        )

        return

    text = (
        "✨ <b>Красивые username</b>\n\n"
    )

    for index, result in enumerate(
        results,
        start=1,
    ):

        text += (
            f"{index}. "
            f"<code>@{result.username}</code>\n"
            f"   🤖 AI: {result.beauty}/10\n"
            f"   📖 Читабельность: "
            f"{result.readability}/10\n\n"
        )

    await message.answer(
        text,
        parse_mode="HTML",
    )


# =========================================================
# 💎 EXPENSIVE RESULT
# =========================================================

@router.message(
    HunterSearchState.expensive
)
async def hunter_expensive_count(
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

    await message.answer(
        "💎 Ищу самые перспективные username..."
    )

    results = hunter.beautiful(
        length=6,
        limit=100,
    )

    await state.clear()

    if not results:

        await message.answer(
            "😔 Ничего подходящего не найдено."
        )

        return

    # Для дорогих username берём
    # самые высокооценённые результаты.
    results = sorted(
        results,
        key=lambda item: item.beauty,
        reverse=True,
    )[:limit]

    text = (
        "💎 <b>Дорогие username</b>\n\n"
    )

    for index, result in enumerate(
        results,
        start=1,
    ):

        text += (
            f"{index}. "
            f"<code>@{result.username}</code>\n"
            f"   💎 Score: "
            f"{result.beauty}/10\n"
            f"   📖 Readability: "
            f"{result.readability}/10\n\n"
        )

    await message.answer(
        text,
        parse_mode="HTML",
    )


# =========================================================
# 📖 DICTIONARY RESULT
# =========================================================

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
            "от 5 до 32 символов."
        )

        return

    results = hunter.dictionary(
        length=length,
        limit=100,
    )

    await state.clear()

    if not results:

        await message.answer(
            "📖 Словарных username такой "
            "длины пока нет."
        )

        return

    text = (
        "📖 <b>Dictionary</b>\n\n"
    )

    for index, result in enumerate(
        results,
        start=1,
    ):

        text += (
            f"{index}. "
            f"<code>@{result.username}</code>\n"
            f"   🤖 AI: {result.beauty}/10\n\n"
        )

    await message.answer(
        text,
        parse_mode="HTML",
    )


# =========================================================
# 💎 PREMIUM 5
# =========================================================

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

    await message.answer(
        "💎 Запускаю Premium Hunter..."
    )

    results = hunter.premium(
        length=5,
        limit=limit,
    )

    await state.clear()

    if not results:

        await message.answer(
            "😔 Пятисимвольных вариантов "
            "не найдено."
        )

        return

    text = (
        "💎 <b>Premium Hunter</b>\n\n"
    )

    for index, result in enumerate(
        results,
        start=1,
    ):

        text += (
            f"{index}. "
            f"<code>@{result.username}</code>\n"
            f"   🤖 AI: {result.beauty}/10\n"
            f"   📖 {result.readability}/10\n\n"
        )

    await message.answer(
        text,
        parse_mode="HTML",
    )


# =========================================================
# 🎯 MASK RESULT
# =========================================================

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
            "Используй только:\n"
            "• английские буквы\n"
            "• ?\n\n"
            "Длина: 5–32."
        )

        return

    await message.answer(
        "🎯 Генерирую варианты по маске..."
    )

    results = hunter.mask(
        mask=mask,
        limit=100,
    )

    await state.clear()

    if not results:

        await message.answer(
            "😔 По этой маске ничего "
            "красивого не найдено."
        )

        return

    text = (
        "🎯 <b>Результаты по маске</b>\n\n"
        f"Маска: <code>{mask}</code>\n\n"
    )

    for index, result in enumerate(
        results,
        start=1,
    ):

        text += (
            f"{index}. "
            f"<code>@{result.username}</code>\n"
            f"   🤖 AI: {result.beauty}/10\n"
            f"   📖 {result.readability}/10\n\n"
        )

    await message.answer(
        text,
        parse_mode="HTML",
    )
