from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.states.common import PromoState
from database.session import async_session_factory
from database.repositories import get_user
from services.promo import promo_service


router = Router()


# =========================================================
# 🎟 PROMO MENU
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
        PromoState.code
    )

    await callback.message.answer(
        "🎟 <b>Активация промокода</b>\n\n"
        "Введи промокод сообщением.\n\n"
        "Например:\n"
        "<code>TEYZUS2026</code>",
        parse_mode="HTML",
    )

    await callback.answer()


# =========================================================
# 🎟 ENTER PROMO CODE
# =========================================================

@router.message(
    PromoState.code
)
async def promo_enter_code(
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
            "❌ <b>Промокод не может быть пустым.</b>\n\n"
            "Введи код ещё раз.",
            parse_mode="HTML",
        )
        return

    # -----------------------------------------------------
    # GET USER
    # -----------------------------------------------------

    async with async_session_factory() as session:

        user = await get_user(
            session=session,
            telegram_id=message.from_user.id,
        )

        if user is None:
            await state.clear()

            await message.answer(
                "❌ Пользователь не найден.\n\n"
                "Попробуй сначала открыть главное меню "
                "и зарегистрироваться."
            )

            return

        # -------------------------------------------------
        # ACTIVATE PROMO
        # -------------------------------------------------

        result = await promo_service.activate(
            session=session,
            user=user,
            code=code,
        )

    # -----------------------------------------------------
    # FINISH STATE
    # -----------------------------------------------------

    await state.clear()

    # -----------------------------------------------------
    # RESULT
    # -----------------------------------------------------

    await message.answer(
        result.message,
        parse_mode="HTML",
    )
