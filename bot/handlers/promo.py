from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from database.models import User
from database.session import async_session_factory
from services.promo import promo_service


router = Router()


# =========================================================
# STATES
# =========================================================

class PromoUserState(StatesGroup):
    code = State()


# =========================================================
# GET USER
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
# PROMO BUTTON
# =========================================================

@router.callback_query(
    F.data == "promo"
)
async def promo_start(
    callback: CallbackQuery,
    state: FSMContext,
):

    await state.clear()

    user = await get_user(
        callback.from_user.id
    )

    if user is None:

        await callback.answer(
            "❌ Пользователь не найден.",
            show_alert=True,
        )

        return

    if user.is_blocked:

        await callback.answer(
            "⛔ Твой аккаунт заблокирован.",
            show_alert=True,
        )

        return

    await state.set_state(
        PromoUserState.code
    )

    await callback.message.answer(
        "🎟 <b>Активация промокода</b>\n\n"
        "Введи промокод сообщением.\n\n"
        "Например:\n"
        "<code>TEYZUS2026</code>\n\n"
        "Чтобы отменить ввод, отправь:\n"
        "<code>отмена</code>",
        parse_mode="HTML",
    )

    await callback.answer()


# =========================================================
# PROMO INPUT
# =========================================================

@router.message(
    PromoUserState.code
)
async def promo_input(
    message: Message,
    state: FSMContext,
):

    code = (
        message.text.strip()
        if message.text
        else ""
    )

    # -----------------------------------------------------
    # CANCEL
    # -----------------------------------------------------

    if code.lower() in {
        "отмена",
        "cancel",
        "/cancel",
    }:

        await state.clear()

        await message.answer(
            "❌ Активация промокода отменена."
        )

        return

    if not code:

        await message.answer(
            "❌ Введи промокод."
        )

        return

    # -----------------------------------------------------
    # GET USER
    # -----------------------------------------------------

    async with async_session_factory() as session:

        result = await session.execute(
            select(User).where(
                User.telegram_id
                == message.from_user.id
            )
        )

        user = result.scalar_one_or_none()

        if user is None:

            await state.clear()

            await message.answer(
                "❌ Пользователь не найден.\n\n"
                "Попробуй снова через /start."
            )

            return

        if user.is_blocked:

            await state.clear()

            await message.answer(
                "⛔ Твой аккаунт заблокирован."
            )

            return

        # -------------------------------------------------
        # ACTIVATE
        # -------------------------------------------------

        result = await promo_service.activate(
            session=session,
            user=user,
            code=code,
        )

    # -----------------------------------------------------
    # FINISH
    # -----------------------------------------------------

    await state.clear()

    await message.answer(
        result.message,
        parse_mode="HTML",
    )


# =========================================================
# TEXT BUTTON SUPPORT
# =========================================================

@router.message(
    F.text.casefold() == "🎟 промокод"
)
async def promo_text_button(
    message: Message,
    state: FSMContext,
):

    await state.clear()

    user = await get_user(
        message.from_user.id
    )

    if user is None:

        await message.answer(
            "❌ Пользователь не найден.\n\n"
            "Попробуй снова через /start."
        )

        return

    if user.is_blocked:

        await message.answer(
            "⛔ Твой аккаунт заблокирован."
        )

        return

    await state.set_state(
        PromoUserState.code
    )

    await message.answer(
        "🎟 <b>Активация промокода</b>\n\n"
        "Введи промокод сообщением.\n\n"
        "Например:\n"
        "<code>TEYZUS2026</code>\n\n"
        "Чтобы отменить ввод, отправь:\n"
        "<code>отмена</code>",
        parse_mode="HTML",
    )
