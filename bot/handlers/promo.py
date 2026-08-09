from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    Message,
)
from bot.states.common import PromoState
from database.repositories import get_user
from database.session import async_session_factory
from services.promo import promo_service
router = Router()
# =========================================================
# 🎟 PROMO BUTTON
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
        "🎟 <b>Промокод</b>\n\n"
        "Введи промокод, чтобы получить "
        "свою награду.\n\n"
        "Например:\n"
        "<code>TEYZUS2026</code>",
        parse_mode="HTML",
    )
    await callback.answer()
# =========================================================
# 🎟 PROMO INPUT
# =========================================================
@router.message(
    PromoState.code
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
            "❌ Введи промокод."
        )
        return
    # =====================================================
    # DATABASE
    # =====================================================
    async with async_session_factory() as session:
        user = await get_user(
            session=session,
            telegram_id=message.from_user.id,
        )
        if user is None:
            await state.clear()
            await message.answer(
                "❌ Профиль пользователя не найден.\n\n"
                "Нажми /start и попробуй снова."
            )
            return
        # =================================================
        # ACTIVATE
        # =================================================
        result = await promo_service.activate(
            session=session,
            user=user,
            code=code,
        )
    # =====================================================
    # FINISH STATE
    # =====================================================
    await state.clear()
    # =====================================================
    # RESPONSE
    # =====================================================
    await message.answer(
        result.message,
        parse_mode="HTML",
    )
# =========================================================
# ❌ CANCEL
# =========================================================
@router.callback_query(
    F.data == "promo_cancel"
)
async def promo_cancel(
    callback: CallbackQuery,
    state: FSMContext,
):
    await state.clear()
    await callback.message.answer(
        "❌ Активация промокода отменена."
    )
    await callback.answer()
