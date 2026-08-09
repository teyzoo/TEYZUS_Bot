from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.states.common import HunterSearchState
from database.session import async_session_factory
from services.hunter.search_service import hunter_search_service
from services.premium import is_premium
from services.search_limits import search_limit_text


router = Router()


# =========================================================
# HELPERS
# =========================================================

def format_result(
    index: int,
    result,
) -> str:

    price = (
        f"{result.price_min:,}".replace(",", " ")
        + "–"
        + f"{result.price_max:,}".replace(",", " ")
        + " ₽"
    )

    return (
        f"{index}. <code>@{result.username}</code>\n"
        f"   🤖 Beauty: <b>{result.beauty_score:.1f}/10</b>\n"
        f"   📖 Readability: <b>{result.readability:.1f}/10</b>\n"
        f"   💎 Rarity: <b>{result.rarity:.1f}/10</b>\n"
        f"   🏷 Brand: <b>{result.brand:.1f}/10</b>\n"
        f"   💧 Liquidity: <b>{result.liquidity:.1f}/10</b>\n"
        f"   💰 Estimate: <b>{price}</b>\n"
        f"   📱 Telegram: <b>{result.telegram_status}</b>\n"
        f"   🌐 t.me: <b>{'Доступен' if result.tme_available else 'Недоступен'}</b>\n"
    )


async def send_results(
    message: Message,
    results,
    header: str,
    footer: str | None = None,
) -> None:

    text = f"{header}\n\n"

    for index, result in enumerate(
        results,
        start=1,
    ):
        text += format_result(
            index=index,
            result=result,
        )
        text += "\n"

    if footer:
        text += f"\n{footer}"

    # Telegram ограничивает сообщение примерно 4096 символами.
    # Разбиваем результаты при необходимости.

    chunks: list[str] = []

    current = ""

    for line in text.splitlines(
        keepends=True
    ):

        if len(current) + len(line) > 3800:

            if current:
                chunks.append(current)

            current = line

        else:

            current += line

    if current:
        chunks.append(current)

    for chunk in chunks:

        await message.answer(
            chunk,
            parse_mode="HTML",
        )


# =========================================================
# 6 SYMBOL SEARCH
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
        "TEYZUS сгенерирует красивые варианты "
        "и проверит их доступность.\n\n"
        "Укажи количество результатов:\n"
        "<b>от 1 до 100</b>.",
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

        amount = int(
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

    if not 1 <= amount <= 100:

        await message.answer(
            "❌ Количество должно быть от 1 до 100."
        )

        return

    await state.clear()

    async with async_session_factory() as session:

        result = await session.get(
            # Получаем User через telegram_id
            # ниже используется отдельный запрос.
            # Импорт сделан внутри для чистоты файла.
            __import__(
                "database.models",
                fromlist=["User"],
            ).User,
            message.from_user.id,
        )

        # SQLAlchemy get() работает только с PK,
        # поэтому если не найдено — используем запрос ниже.

        if result is None:

            from sqlalchemy import select
            from database.models import User

            query = await session.execute(
                select(User).where(
                    User.telegram_id
                    == message.from_user.id
                )
            )

            result = query.scalar_one_or_none()

        user = result

        if user is None:

            await message.answer(
                "❌ Пользователь не найден.\n\n"
                "Выполни /start."
            )

            return

        await message.answer(
            "🔎 <b>Запускаю Hunter...</b>\n\n"
            "Генерирую кандидатов и проверяю "
            "доступность.",
            parse_mode="HTML",
        )

        response = await hunter_search_service.search(
            session=session,
            user=user,
            length=6,
            amount=amount,
        )

    if not response.success:

        await message.answer(
            response.message,
            parse_mode="HTML",
        )

        return

    await send_results(
        message=message,
        results=response.results,
        header="✨ <b>Найденные username</b>",
        footer=response.message,
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

    async with async_session_factory() as session:

        from sqlalchemy import select
        from database.models import User

        query = await session.execute(
            select(User).where(
                User.telegram_id
                == callback.from_user.id
            )
        )

        user = query.scalar_one_or_none()

    if user is None:

        await callback.answer(
            "❌ Пользователь не найден.",
            show_alert=True,
        )

        return

    if not is_premium(user):

        await callback.answer(
            "💎 Эта функция доступна только Premium.",
            show_alert=True,
        )

        return

    await state.set_state(
        HunterSearchState.length_5
    )

    await callback.message.answer(
        "💎 <b>Premium Hunter</b>\n\n"
        "Длина: <b>5 символов</b>\n\n"
        "Укажи количество результатов:\n"
        "<b>от 1 до 100</b>.",
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

        amount = int(
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

    if not 1 <= amount <= 100:

        await message.answer(
            "❌ Количество должно быть от 1 до 100."
        )

        return

    await state.clear()

    async with async_session_factory() as session:

        from sqlalchemy import select
        from database.models import User

        query = await session.execute(
            select(User).where(
                User.telegram_id
                == message.from_user.id
            )
        )

        user = query.scalar_one_or_none()

        if user is None:

            await message.answer(
                "❌ Пользователь не найден."
            )

            return

        if not is_premium(user):

            await message.answer(
                "💎 Для пятисимвольного Hunter нужен Premium."
            )

            return

        await message.answer(
            "💎 <b>Premium Hunter запускается...</b>",
            parse_mode="HTML",
        )

        response = await hunter_search_service.search(
            session=session,
            user=user,
            length=5,
            amount=amount,
        )

    if not response.success:

        await message.answer(
            response.message,
            parse_mode="HTML",
        )

        return

    await send_results(
        message=message,
        results=response.results,
        header="💎 <b>Premium Hunter</b>",
        footer=response.message,
    )


# =========================================================
# SEARCH LIMIT
# =========================================================

@router.callback_query(
    F.data == "hunter_limit"
)
async def hunter_limit(
    callback: CallbackQuery,
):

    async with async_session_factory() as session:

        from sqlalchemy import select
        from database.models import User

        query = await session.execute(
            select(User).where(
                User.telegram_id
                == callback.from_user.id
            )
        )

        user = query.scalar_one_or_none()

        if user is None:

            await callback.answer(
                "❌ Пользователь не найден.",
                show_alert=True,
            )

            return

        text = await search_limit_text(
            session=session,
            user=user,
        )

    await callback.message.answer(
        "📊 <b>Лимит поиска</b>\n\n"
        f"{text}",
        parse_mode="HTML",
    )

    await callback.answer()
