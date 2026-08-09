from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    Message,
)

from database.repositories import get_or_create_user
from database.session import async_session_factory
from services.promo import promo_service


router = Router()


# =========================================================
# STATE
# =========================================================

class PromoUserState(StatesGroup):

    code = State()


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

    await state.set_state(
        PromoUserState.code
    )

    await callback.message.answer(
        "🎟 <b>Активация промокода</b>\n\n"
        "Отправь промокод сообщением.\n\n"
        "Например:\n"
        "<code>TEYZUS2026</code>",
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

    if not code:

        await message.answer(
            "❌ Промокод не может быть пустым."
        )

        return

    # -----------------------------------------------------
    # USER
    # -----------------------------------------------------

    async with async_session_factory() as session:

        user, _ = await get_or_create_user(
            session=session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            language=(
                message.from_user.language_code
                or "ru"
            ),
        )

        # -------------------------------------------------
        # ACTIVATE
        # -------------------------------------------------

        result = await promo_service.activate(
            session=session,
            user=user,
            code=code,
        )

    await state.clear()

    await message.answer(
        result.message,
        parse_mode="HTML",
    )
