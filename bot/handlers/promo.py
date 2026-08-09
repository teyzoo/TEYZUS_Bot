from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from database.repositories import (
    activate_promo,
    get_promo,
    get_user,
)
from database.session import (
    async_session_factory,
)
router = Router()
# =========================================================
# 🎟 PROMO STATE
# =========================================================
class PromoState(StatesGroup):
    code = State()
# =========================================================
# 🎟 PROMO KEYBOARD
# =========================================================
def promo_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎟 Ввести промокод",
                    callback_data="promo_enter",
                )
            ],
        ]
    )
# =========================================================
# 🎟 OPEN PROMO
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
        "🎟 <b>Промокод TEYZUS</b>\n\n"
        "Введи промокод сообщением.\n\n"
        "Например:\n"
        "<code>TEYZUS2026</code>",
        parse_mode="HTML",
    )
    await callback.answer()
# =========================================================
# 🎟 ENTER PROMO
# =========================================================
@router.callback_query(
    F.data == "promo_enter"
)
async def promo_enter(
    callback: CallbackQuery,
    state: FSMContext,
):
    await state.set_state(
        PromoState.code
    )
    await callback.message.answer(
        "🎟 Введи промокод:",
        parse_mode="HTML",
    )
    await callback.answer()
# =========================================================
# 🎟 ACTIVATE
# =========================================================
@router.message(
    PromoState.code
)
async def promo_activate(
    message: Message,
    state: FSMContext,
):
    code = (
        message.text.strip().upper()
        if message.text
        else ""
    )
    if not code:
        await message.answer(
            "❌ Промокод не может быть пустым."
        )
        return
    await message.answer(
        "⏳ Проверяю промокод..."
    )
    async with async_session_factory() as session:
        user = await get_user(
            session=session,
            telegram_id=message.from_user.id,
        )
        if user is None:
            await state.clear()
            await message.answer(
                "❌ Пользователь не найден.\n\n"
                "Сначала нажми /start."
            )
            return
        promo = await get_promo(
            session=session,
            code=code,
        )
        if promo is None:
            await state.clear()
            await message.answer(
                "❌ <b>Промокод не найден.</b>\n\n"
                "Проверь правильность написания.",
                parse_mode="HTML",
            )
            return
        try:
            activation = await activate_promo(
                session=session,
                promo=promo,
                user=user,
            )
        except ValueError as error:
            await state.clear()
            await message.answer(
                f"❌ <b>Промокод недоступен.</b>\n\n"
                f"{error}",
                parse_mode="HTML",
            )
            return
    await state.clear()
    # -----------------------------------------------------
    # REWARD TEXT
    # -----------------------------------------------------
    if activation.reward_type == "premium":
        reward_text = (
            "💎 Premium на "
            f"<b>{activation.premium_days} дн.</b>"
        )
    elif activation.reward_type == "stars":
        reward_text = (
            "⭐ "
            f"<b>{activation.reward_amount}</b> Stars"
        )
    elif activation.reward_type == "balance_rub":
        reward_text = (
            "💰 "
            f"<b>{activation.reward_amount} ₽</b>"
        )
    elif activation.reward_type == "searches":
        reward_text = (
            "🔎 "
            f"<b>{activation.reward_amount}</b> дополнительных поисков"
        )
    elif activation.reward_type == "traps":
        reward_text = (
            "🚨 "
            f"<b>{activation.reward_amount}</b> дополнительных ловушек"
        )
    else:
        reward_text = (
            f"🎁 {activation.reward_amount}"
        )
    await message.answer(
        "🎉 <b>ПРОМОКОД АКТИВИРОВАН!</b>\n\n"
        f"🎟 Код: <code>{code}</code>\n"
        f"🎁 Награда: {reward_text}\n\n"
        "Награда уже зачислена на твой аккаунт.",
        parse_mode="HTML",
    )
