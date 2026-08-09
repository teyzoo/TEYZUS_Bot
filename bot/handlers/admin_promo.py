from __future__ import annotations
from datetime import datetime, timezone
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from sqlalchemy import func, select
from bot.states.admin import OwnerPromoState
from database.models import (
    PromoActivation,
    PromoCode,
    User,
)
from database.repositories import (
    create_promo,
    deactivate_promo,
    get_promo_by_id,
    list_promos,
    promo_statistics,
)
from database.session import (
    async_session_factory,
)
from services.roles import (
    is_owner,
)
router = Router()
# =========================================================
# 🎟 CONSTANTS
# =========================================================
REWARD_NAMES = {
    "premium": "💎 Premium",
    "stars": "⭐ Stars",
    "balance_rub": "💰 Рубли",
    "searches": "🔎 Дополнительные поиски",
    "traps": "🚨 Дополнительные ловушки",
}
# =========================================================
# 🔐 OWNER HELPERS
# =========================================================
async def get_owner(
    telegram_id: int,
) -> User | None:
    async with async_session_factory() as session:
        result = await session.execute(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )
        return result.scalar_one_or_none()
async def require_owner(
    telegram_id: int,
) -> bool:
    user = await get_owner(
        telegram_id
    )
    if user is None:
        return False
    return is_owner(
        user.role
    )
# =========================================================
# 🧰 PARSERS
# =========================================================
def parse_optional_int(
    value: str,
) -> int | None:
    value = value.strip().lower()
    if value in {
        "нет",
        "нету",
        "none",
        "null",
        "∞",
        "безлимит",
        "без ограничений",
        "безлимитно",
    }:
        return None
    return int(value)
def parse_date(
    value: str,
) -> datetime | None:
    value = value.strip().lower()
    if value in {
        "нет",
        "none",
        "null",
        "-",
        "без срока",
    }:
        return None
    parsed = datetime.strptime(
        value,
        "%d.%m.%Y %H:%M",
    )
    return parsed.replace(
        tzinfo=timezone.utc
    )
# =========================================================
# 🎟 KEYBOARDS
# =========================================================
def promo_list_keyboard(
    promos: list[PromoCode],
) -> InlineKeyboardMarkup:
    rows = []
    for promo in promos[:50]:
        status = (
            "🟢"
            if promo.is_active
            else "🔴"
        )
        rows.append(
            [
                InlineKeyboardButton(
                    text=(
                        f"{status} {promo.code}"
                    ),
                    callback_data=(
                        f"owner_promo_view:{promo.id}"
                    ),
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text="➕ Создать промокод",
                callback_data="owner_promo_create",
            )
        ]
    )
    return InlineKeyboardMarkup(
        inline_keyboard=rows
    )
def promo_view_keyboard(
    promo: PromoCode,
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text="📊 Статистика",
                callback_data=(
                    f"owner_promo_stats:{promo.id}"
                ),
            )
        ]
    ]
    if promo.is_active:
        rows.append(
            [
                InlineKeyboardButton(
                    text="🔴 Отключить",
                    callback_data=(
                        f"owner_promo_disable:{promo.id}"
                    ),
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text="⬅️ Все промокоды",
                callback_data="owner_promos",
            )
        ]
    )
    return InlineKeyboardMarkup(
        inline_keyboard=rows
    )
def confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Создать",
                    callback_data="owner_promo_confirm",
                ),
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data="owner_promo_cancel",
                ),
            ]
        ]
    )
# =========================================================
# 🎟 OWNER PROMO MENU
# =========================================================
@router.callback_query(
    F.data == "owner_promos"
)
async def owner_promos(
    callback: CallbackQuery,
    state: FSMContext,
):
    if not await require_owner(
        callback.from_user.id
    ):
        await callback.answer(
            "⛔ Доступ запрещён.",
            show_alert=True,
        )
        return
    await state.clear()
    async with async_session_factory() as session:
        promos = await list_promos(
            session=session
        )
    if not promos:
        await callback.message.answer(
            "🎟 <b>Промокоды TEYZUS</b>\n\n"
            "Промокодов пока нет.",
            parse_mode="HTML",
            reply_markup=promo_list_keyboard(
                []
            ),
        )
        await callback.answer()
        return
    text = (
        "🎟 <b>ПРОМОКОДЫ TEYZUS</b>\n\n"
        f"Всего: <b>{len(promos)}</b>\n\n"
    )
    for promo in promos[:20]:
        status = (
            "🟢"
            if promo.is_active
            else "🔴"
        )
        limit = (
            str(
                promo.max_activations
            )
            if promo.max_activations is not None
            else "∞"
        )
        text += (
            f"{status} "
            f"<code>{promo.code}</code>\n"
            f"🎁 "
            f"{REWARD_NAMES.get("
            f"promo.reward_type"
            f", promo.reward_type)}\n"
            f"📊 "
            f"{promo.activations_count}/{limit}\n\n"
        )
    await callback.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=promo_list_keyboard(
            promos
        ),
    )
    await callback.answer()
# =========================================================
# ➕ CREATE PROMO
# =========================================================
@router.callback_query(
    F.data == "owner_promo_create"
)
async def owner_promo_create(
    callback: CallbackQuery,
    state: FSMContext,
):
    if not await require_owner(
        callback.from_user.id
    ):
        await callback.answer(
            "⛔ Доступ запрещён.",
            show_alert=True,
        )
        return
    await state.clear()
    await state.set_state(
        OwnerPromoState.code
    )
    await callback.message.answer(
        "🎟 <b>Создание промокода</b>\n\n"
        "Шаг <b>1/10</b>\n\n"
        "Введи код.\n\n"
        "Пример:\n"
        "<code>TEYZUS2026</code>",
        parse_mode="HTML",
    )
    await callback.answer()
# =========================================================
# STEP 1 — CODE
# =========================================================
@router.message(
    OwnerPromoState.code
)
async def promo_code(
    message: Message,
    state: FSMContext,
):
    if not await require_owner(
        message.from_user.id
    ):
        await state.clear()
        return
    code = (
        message.text.strip().upper()
        if message.text
        else ""
    )
    if not code:
        await message.answer(
            "❌ Код не может быть пустым."
        )
        return
    if len(code) > 128:
        await message.answer(
            "❌ Максимальная длина кода — 128 символов."
        )
        return
    async with async_session_factory() as session:
        result = await session.execute(
            select(PromoCode).where(
                PromoCode.code == code
            )
        )
        existing = (
            result.scalar_one_or_none()
        )
    if existing:
        await message.answer(
            "❌ Такой промокод уже существует.\n\n"
            "Введи другой код."
        )
        return
    await state.update_data(
        code=code
    )
    await state.set_state(
        OwnerPromoState.reward_type
    )
    await message.answer(
        "🎁 <b>Шаг 2/10</b>\n\n"
        "Выбери тип награды:\n\n"
        "1️⃣ Premium\n"
        "2️⃣ Stars\n"
        "3️⃣ Рублёвый баланс\n"
        "4️⃣ Дополнительные поиски\n"
        "5️⃣ Дополнительные ловушки\n\n"
        "Отправь число <b>1–5</b>.",
        parse_mode="HTML",
    )
# =========================================================
# STEP 2 — REWARD TYPE
# =========================================================
@router.message(
    OwnerPromoState.reward_type
)
async def promo_reward_type(
    message: Message,
    state: FSMContext,
):
    values = {
        "1": "premium",
        "2": "stars",
        "3": "balance_rub",
        "4": "searches",
        "5": "traps",
    }
    value = (
        message.text.strip()
        if message.text
        else ""
    )
    reward_type = values.get(
        value
    )
    if reward_type is None:
        await message.answer(
            "❌ Отправь число от 1 до 5."
        )
        return
    await state.update_data(
        reward_type=reward_type
    )
    if reward_type == "premium":
        await state.set_state(
            OwnerPromoState.premium_days
        )
        await message.answer(
            "💎 <b>Шаг 3/10</b>\n\n"
            "Сколько дней Premium выдавать?\n\n"
            "Например:\n"
            "<code>30</code>",
            parse_mode="HTML",
        )
        return
    await state.set_state(
        OwnerPromoState.reward_amount
    )
    await message.answer(
        "🎁 <b>Шаг 3/10</b>\n\n"
        "Укажи количество награды.\n\n"
        "Например:\n"
        "<code>100</code>",
        parse_mode="HTML",
    )
# =========================================================
# STEP 3A — PREMIUM DAYS
# =========================================================
@router.message(
    OwnerPromoState.premium_days
)
async def promo_premium_days(
    message: Message,
    state: FSMContext,
):
    try:
        days = int(
            message.text.strip()
        )
    except (
        ValueError,
        AttributeError,
    ):
        await message.answer(
            "❌ Введи целое число дней."
        )
        return
    if days <= 0:
        await message.answer(
            "❌ Количество дней должно быть больше 0."
        )
        return
    await state.update_data(
        premium_days=days,
        reward_amount=0,
    )
    await state.set_state(
        OwnerPromoState.max_activations
    )
    await message.answer(
        "📊 <b>Шаг 4/10</b>\n\n"
        "Общий лимит активаций.\n\n"
        "Например:\n"
        "<code>1000</code>\n\n"
        "Или:\n"
        "<code>∞</code> — без ограничений.",
        parse_mode="HTML",
    )
# =========================================================
# STEP 3B — REWARD AMOUNT
# =========================================================
@router.message(
    OwnerPromoState.reward_amount
)
async def promo_reward_amount(
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
            "❌ Введи целое число."
        )
        return
    if amount <= 0:
        await message.answer(
            "❌ Количество должно быть больше 0."
        )
        return
    await state.update_data(
        reward_amount=amount,
        premium_days=0,
    )
    await state.set_state(
        OwnerPromoState.max_activations
    )
    await message.answer(
        "📊 <b>Шаг 4/10</b>\n\n"
        "Общий лимит активаций.\n\n"
        "Например:\n"
        "<code>1000</code>\n\n"
        "Или:\n"
        "<code>∞</code> — без ограничений.",
        parse_mode="HTML",
    )
# =========================================================
# STEP 4 — GLOBAL LIMIT
# =========================================================
@router.message(
    OwnerPromoState.max_activations
)
async def promo_max_activations(
    message: Message,
    state: FSMContext,
):
    try:
        limit = parse_optional_int(
            message.text or ""
        )
    except ValueError:
        await message.answer(
            "❌ Введи число или <code>∞</code>.",
            parse_mode="HTML",
        )
        return
    await state.update_data(
        max_activations=limit
    )
    await state.set_state(
        OwnerPromoState.max_activations_per_user
    )
    await message.answer(
        "👤 <b>Шаг 5/10</b>\n\n"
        "Сколько раз один пользователь "
        "может активировать этот код?\n\n"
        "Например:\n"
        "<code>1</code>\n"
        "<code>5</code>\n"
        "<code>∞</code>",
        parse_mode="HTML",
    )
# =========================================================
# STEP 5 — USER LIMIT
# =========================================================
@router.message(
    OwnerPromoState.max_activations_per_user
)
async def promo_user_limit(
    message: Message,
    state: FSMContext,
):
    try:
        limit = parse_optional_int(
            message.text or ""
        )
    except ValueError:
        await message.answer(
            "❌ Введи число или <code>∞</code>.",
            parse_mode="HTML",
        )
        return
    await state.update_data(
        max_activations_per_user=limit
    )
    await state.set_state(
        OwnerPromoState.starts_at
    )
    await message.answer(
        "📅 <b>Шаг 6/10</b>\n\n"
        "Дата начала действия.\n\n"
        "Формат:\n"
        "<code>09.08.2026 12:00</code>\n\n"
        "Или:\n"
        "<code>нет</code>",
        parse_mode="HTML",
    )
# =========================================================
# STEP 6 — START DATE
# =========================================================
@router.message(
    OwnerPromoState.starts_at
)
async def promo_starts_at(
    message: Message,
    state: FSMContext,
):
    try:
        starts_at = parse_date(
            message.text or ""
        )
    except ValueError:
        await message.answer(
            "❌ Неверный формат.\n\n"
            "Используй:\n"
            "<code>ДД.ММ.ГГГГ ЧЧ:ММ</code>\n\n"
            "Или <code>нет</code>.",
            parse_mode="HTML",
        )
        return
    await state.update_data(
        starts_at=starts_at
    )
    await state.set_state(
        OwnerPromoState.expires_at
    )
    await message.answer(
        "📅 <b>Шаг 7/10</b>\n\n"
        "Дата окончания действия.\n\n"
        "Формат:\n"
        "<code>31.12.2026 23:59</code>\n\n"
        "Или:\n"
        "<code>нет</code>",
        parse_mode="HTML",
    )
# =========================================================
# STEP 7 — END DATE
# =========================================================
@router.message(
    OwnerPromoState.expires_at
)
async def promo_expires_at(
    message: Message,
    state: FSMContext,
):
    try:
        expires_at = parse_date(
            message.text or ""
        )
    except ValueError:
        await message.answer(
            "❌ Неверный формат.\n\n"
            "Используй:\n"
            "<code>ДД.ММ.ГГГГ ЧЧ:ММ</code>\n\n"
            "Или <code>нет</code>.",
            parse_mode="HTML",
        )
        return
    data = await state.get_data()
    starts_at = data.get(
        "starts_at"
    )
    if (
        starts_at is not None
        and expires_at is not None
        and expires_at <= starts_at
    ):
        await message.answer(
            "❌ Дата окончания должна быть "
            "позже даты начала."
        )
        return
    await state.update_data(
        expires_at=expires_at
    )
    await state.set_state(
        OwnerPromoState.only_new_users
    )
    await message.answer(
        "👶 <b>Шаг 8/10</b>\n\n"
        "Только для новых пользователей?\n\n"
        "Отправь:\n"
        "<code>да</code>\n"
        "или\n"
        "<code>нет</code>",
        parse_mode="HTML",
    )
# =========================================================
# STEP 8 — NEW USERS
# =========================================================
@router.message(
    OwnerPromoState.only_new_users
)
async def promo_only_new_users(
    message: Message,
    state: FSMContext,
):
    value = (
        message.text.strip().lower()
        if message.text
        else ""
    )
    if value not in {
        "да",
        "нет",
    }:
        await message.answer(
            "❌ Напиши <code>да</code> или <code>нет</code>.",
            parse_mode="HTML",
        )
        return
    await state.update_data(
        only_new_users=value == "да"
    )
    await state.set_state(
        OwnerPromoState.only_premium
    )
    await message.answer(
        "💎 <b>Шаг 9/10</b>\n\n"
        "Только для Premium пользователей?\n\n"
        "Отправь:\n"
        "<code>да</code>\n"
        "или\n"
        "<code>нет</code>",
        parse_mode="HTML",
    )
# =========================================================
# STEP 9 — PREMIUM ONLY
# =========================================================
@router.message(
    OwnerPromoState.only_premium
)
async def promo_only_premium(
    message: Message,
    state: FSMContext,
):
    value = (
        message.text.strip().lower()
        if message.text
        else ""
    )
    if value not in {
        "да",
        "нет",
    }:
        await message.answer(
            "❌ Напиши <code>да</code> или <code>нет</code>.",
            parse_mode="HTML",
        )
        return
    await state.update_data(
        only_premium=value == "да"
    )
    await state.set_state(
        OwnerPromoState.allowed_user_ids
    )
    await message.answer(
        "🔐 <b>Шаг 10/10</b>\n\n"
        "Можно ограничить промокод "
        "конкретными Telegram ID.\n\n"
        "Пример:\n"
        "<code>123456789,987654321</code>\n\n"
        "Для доступа всем отправь:\n"
        "<code>все</code>",
        parse_mode="HTML",
    )
# =========================================================
# STEP 10 — ALLOWED USERS
# =========================================================
@router.message(
    OwnerPromoState.allowed_user_ids
)
async def promo_allowed_users(
    message: Message,
    state: FSMContext,
):
    value = (
        message.text.strip()
        if message.text
        else ""
    )
    if value.lower() in {
        "все",
        "all",
        "нет",
    }:
        allowed_user_ids = None
    else:
        ids: list[int] = []
        for item in value.split(","):
            item = item.strip()
            if not item:
                continue
            try:
                telegram_id = int(
                    item
                )
            except ValueError:
                await message.answer(
                    "❌ Неверный Telegram ID:\n"
                    f"<code>{item}</code>",
                    parse_mode="HTML",
                )
                return
            if telegram_id <= 0:
                await message.answer(
                    "❌ Telegram ID должен быть "
                    "положительным числом."
                )
                return
            if telegram_id not in ids:
                ids.append(
                    telegram_id
                )
        if not ids:
            await message.answer(
                "❌ Укажи Telegram ID "
                "или отправь <code>все</code>.",
                parse_mode="HTML",
            )
            return
        allowed_user_ids = ",".join(
            str(item)
            for item in ids
        )
    await state.update_data(
        allowed_user_ids=allowed_user_ids
    )
    data = await state.get_data()
    reward_type = data.get(
        "reward_type"
    )
    reward_name = REWARD_NAMES.get(
        reward_type,
        reward_type,
    )
    reward_amount = data.get(
        "reward_amount",
        0,
    )
    premium_days = data.get(
        "premium_days",
        0,
    )
    max_activations = data.get(
        "max_activations"
    )
    max_per_user = data.get(
        "max_activations_per_user"
    )
    starts_at = data.get(
        "starts_at"
    )
    expires_at = data.get(
        "expires_at"
    )
    only_new_users = data.get(
        "only_new_users",
        False,
    )
    only_premium = data.get(
        "only_premium",
        False,
    )
    code = data.get(
        "code"
    )
    if reward_type == "premium":
        reward_text = (
            f"{reward_name}: "
            f"<b>{premium_days} дн.</b>"
        )
    else:
        reward_text = (
            f"{reward_name}: "
            f"<b>{reward_amount}</b>"
        )
    global_limit_text = (
        str(max_activations)
        if max_activations is not None
        else "∞"
    )
    user_limit_text = (
        str(max_per_user)
        if max_per_user is not None
        else "∞"
    )
    starts_text = (
        starts_at.strftime(
            "%d.%m.%Y %H:%M"
        )
        if starts_at
        else "Нет"
    )
    expires_text = (
        expires_at.strftime(
            "%d.%m.%Y %H:%M"
        )
        if expires_at
        else "Нет"
    )
    users_text = (
        allowed_user_ids
        if allowed_user_ids
        else "Все пользователи"
    )
    text = (
        "🎟 <b>ПРОВЕРКА ПРОМОКОДА</b>\n\n"
        f"🔑 Код: <code>{code}</code>\n"
        f"🎁 {reward_text}\n"
        f"📊 Общий лимит: "
        f"<b>{global_limit_text}</b>\n"
        f"👤 На пользователя: "
        f"<b>{user_limit_text}</b>\n"
        f"📅 Начало: "
        f"<b>{starts_text}</b>\n"
        f"⌛ Окончание: "
        f"<b>{expires_text}</b>\n"
        f"👶 Новые пользователи: "
        f"<b>{'Да' if only_new_users else 'Нет'}</b>\n"
        f"💎 Только Premium: "
        f"<b>{'Да' if only_premium else 'Нет'}</b>\n"
        f"🔐 Доступ: "
        f"<b>{users_text}</b>\n\n"
        "Создать этот промокод?"
    )
    await state.set_state(
        OwnerPromoState.confirmation
    )
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=confirmation_keyboard(),
    )
# =========================================================
# ✅ CONFIRM
# =========================================================
@router.callback_query(
    F.data == "owner_promo_confirm"
)
async def owner_promo_confirm(
    callback: CallbackQuery,
    state: FSMContext,
):
    if not await require_owner(
        callback.from_user.id
    ):
        await state.clear()
        await callback.answer(
            "⛔ Доступ запрещён.",
            show_alert=True,
        )
        return
    data = await state.get_data()
    try:
        async with async_session_factory() as session:
            promo = await create_promo(
                session=session,
                code=data["code"],
                reward_type=data["reward_type"],
                reward_amount=data.get(
                    "reward_amount",
                    0,
                ),
                premium_days=data.get(
                    "premium_days",
                    0,
                ),
                max_activations=data.get(
                    "max_activations"
                ),
                max_activations_per_user=data.get(
                    "max_activations_per_user"
                ),
                starts_at=data.get(
                    "starts_at"
                ),
                expires_at=data.get(
                    "expires_at"
                ),
                only_new_users=data.get(
                    "only_new_users",
                    False,
                ),
                only_premium=data.get(
                    "only_premium",
                    False,
                ),
                allowed_user_ids=data.get(
                    "allowed_user_ids"
                ),
                created_by=callback.from_user.id,
            )
    except (
        ValueError,
        KeyError,
    ) as error:
        await state.clear()
        await callback.message.answer(
            "❌ <b>Промокод не создан.</b>\n\n"
            f"{error}",
            parse_mode="HTML",
        )
        await callback.answer()
        return
    await state.clear()
    await callback.message.answer(
        "✅ <b>ПРОМОКОД СОЗДАН!</b>\n\n"
        f"🎟 Код: <code>{promo.code}</code>\n"
        f"🎁 Награда: "
        f"<b>{REWARD_NAMES.get("
        f"promo.reward_type"
        f", promo.reward_type)}</b>\n"
        f"📊 Общий лимит: "
        f"<b>{promo.max_activations or '∞'}</b>\n"
        f"👤 На пользователя: "
        f"<b>{promo.max_activations_per_user or '∞'}</b>",
        parse_mode="HTML",
    )
    await callback.answer(
        "Промокод создан!"
    )
# =========================================================
# ❌ CANCEL
# =========================================================
@router.callback_query(
    F.data == "owner_promo_cancel"
)
async def owner_promo_cancel(
    callback: CallbackQuery,
    state: FSMContext,
):
    if not await require_owner(
        callback.from_user.id
    ):
        await callback.answer(
            "⛔ Доступ запрещён.",
            show_alert=True,
        )
        return
    await state.clear()
    await callback.message.answer(
        "❌ Создание промокода отменено."
    )
    await callback.answer()
# =========================================================
# 👁 VIEW PROMO
# =========================================================
@router.callback_query(
    F.data.startswith(
        "owner_promo_view:"
    )
)
async def owner_promo_view(
    callback: CallbackQuery,
):
    if not await require_owner(
        callback.from_user.id
    ):
        await callback.answer(
            "⛔ Доступ запрещён.",
            show_alert=True,
        )
        return
    try:
        promo_id = int(
            callback.data.split(":")[1]
        )
    except (
        ValueError,
        IndexError,
    ):
        await callback.answer(
            "❌ Неверный ID.",
            show_alert=True,
        )
        return
    async with async_session_factory() as session:
        promo = await get_promo_by_id(
            session=session,
            promo_id=promo_id,
        )
        if promo is None:
            await callback.answer(
                "❌ Промокод не найден.",
                show_alert=True,
            )
            return
        stats = await get_promo_stats(
            session=session,
            promo_id=promo.id,
        )
    status = (
        "🟢 Активен"
        if promo.is_active
        else "🔴 Отключён"
    )
    reward_name = REWARD_NAMES.get(
        promo.reward_type,
        promo.reward_type,
    )
    if promo.reward_type == "premium":
        reward_text = (
            f"{reward_name} — "
            f"{promo.premium_days} дней"
        )
    else:
        reward_text = (
            f"{reward_name} — "
            f"{promo.reward_amount}"
        )
    global_limit = (
        str(promo.max_activations)
        if promo.max_activations is not None
        else "∞"
    )
    user_limit = (
        str(
            promo.max_activations_per_user
        )
        if promo.max_activations_per_user is not None
        else "∞"
    )
    starts_text = (
        promo.starts_at.strftime(
            "%d.%m.%Y %H:%M"
        )
        if promo.starts_at
        else "Нет"
    )
    expires_text = (
        promo.expires_at.strftime(
            "%d.%m.%Y %H:%M"
        )
        if promo.expires_at
        else "Нет"
    )
    allowed_text = (
        promo.allowed_user_ids
        if promo.allowed_user_ids
        else "Все"
    )
    text = (
        "🎟 <b>ПРОМОКОД</b>\n\n"
        f"🔑 Код: <code>{promo.code}</code>\n"
        f"📌 Статус: <b>{status}</b>\n\n"
        f"🎁 Награда: <b>{reward_text}</b>\n"
        f"🔥 Активаций: "
        f"<b>{stats['total']}</b> / {global_limit}\n"
        f"👥 Уникальных пользователей: "
        f"<b>{stats['unique_users']}</b>\n"
        f"👤 Лимит на пользователя: "
        f"<b>{user_limit}</b>\n\n"
        f"📅 Начало: <b>{starts_text}</b>\n"
        f"⌛ Окончание: <b>{expires_text}</b>\n"
        f"👶 Только новые: "
        f"<b>{'Да' if promo.only_new_users else 'Нет'}</b>\n"
        f"💎 Только Premium: "
        f"<b>{'Да' if promo.only_premium else 'Нет'}</b>\n"
        f"🔐 Доступ: <b>{allowed_text}</b>\n\n"
        f"🆔 ID: <code>{promo.id}</code>"
    )
    await callback.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=promo_view_keyboard(
            promo
        ),
    )
    await callback.answer()
# =========================================================
# 📊 STATISTICS
# =========================================================
async def get_promo_stats(
    session,
    promo_id: int,
) -> dict[str, int]:
    total_result = await session.execute(
        select(
            func.count(
                PromoActivation.id
            )
        ).where(
            PromoActivation.promo_id
            == promo_id
        )
    )
    total = int(
        total_result.scalar_one() or 0
    )
    unique_result = await session.execute(
        select(
            func.count(
                func.distinct(
                    PromoActivation.user_id
                )
            )
        ).where(
            PromoActivation.promo_id
            == promo_id
        )
    )
    unique_users = int(
        unique_result.scalar_one() or 0
    )
    return {
        "total": total,
        "unique_users": unique_users,
    }
@router.callback_query(
    F.data.startswith(
        "owner_promo_stats:"
    )
)
async def owner_promo_stats(
    callback: CallbackQuery,
):
    if not await require_owner(
        callback.from_user.id
    ):
        await callback.answer(
            "⛔ Доступ запрещён.",
            show_alert=True,
        )
        return
    try:
        promo_id = int(
            callback.data.split(":")[1]
        )
    except (
        ValueError,
        IndexError,
    ):
        await callback.answer(
            "❌ Неверный ID.",
            show_alert=True,
        )
        return
    async with async_session_factory() as session:
        promo = await get_promo_by_id(
            session=session,
            promo_id=promo_id,
        )
        if promo is None:
            await callback.answer(
                "❌ Промокод не найден.",
                show_alert=True,
            )
            return
        stats = await get_promo_stats(
            session=session,
            promo_id=promo.id,
        )
    limit_text = (
        str(promo.max_activations)
        if promo.max_activations is not None
        else "∞"
    )
    percent = 0.0
    if (
        promo.max_activations
        and promo.max_activations > 0
    ):
        percent = (
            stats["total"]
            / promo.max_activations
        ) * 100
    await callback.message.answer(
        "📊 <b>СТАТИСТИКА ПРОМОКОДА</b>\n\n"
        f"🎟 Код: <code>{promo.code}</code>\n"
        f"🎁 Награда: "
        f"<b>{REWARD_NAMES.get("
        f"promo.reward_type"
        f", promo.reward_type)}</b>\n\n"
        f"🔥 Активаций: "
        f"<b>{stats['total']}</b>\n"
        f"👥 Уникальных пользователей: "
        f"<b>{stats['unique_users']}</b>\n"
        f"📈 Использовано: "
        f"<b>{percent:.1f}%</b>\n"
        f"📊 Лимит: <b>{limit_text}</b>\n"
        f"🟢 Активен: "
        f"<b>{'Да' if promo.is_active else 'Нет'}</b>",
        parse_mode="HTML",
        reply_markup=promo_view_keyboard(
            promo
        ),
    )
    await callback.answer()
# =========================================================
# 🔴 DEACTIVATE
# =========================================================
@router.callback_query(
    F.data.startswith(
        "owner_promo_disable:"
    )
)
async def owner_promo_disable(
    callback: CallbackQuery,
):
    if not await require_owner(
        callback.from_user.id
    ):
        await callback.answer(
            "⛔ Доступ запрещён.",
            show_alert=True,
        )
        return
    try:
        promo_id = int(
            callback.data.split(":")[1]
        )
    except (
        ValueError,
        IndexError,
    ):
        await callback.answer(
            "❌ Неверный ID.",
            show_alert=True,
        )
        return
    async with async_session_factory() as session:
        success = await deactivate_promo(
            session=session,
            promo_id=promo_id,
        )
    if not success:
        await callback.answer(
            "❌ Промокод не найден.",
            show_alert=True,
        )
        return
    await callback.message.answer(
        "🔴 <b>Промокод отключён.</b>\n\n"
        "Новые активации этого кода "
        "больше невозможны.",
        parse_mode="HTML",
    )
    await callback.answer(
        "Промокод отключён."
    )
# =========================================================
# 🔄 BACK TO PROMOS
# =========================================================
@router.callback_query(
    F.data == "owner_promos_back"
)
async def owner_promos_back(
    callback: CallbackQuery,
):
    if not await require_owner(
        callback.from_user.id
    ):
        await callback.answer(
            "⛔ Доступ запрещён.",
            show_alert=True,
        )
        return
    async with async_session_factory() as session:
        promos = await list_promos(
            session=session
        )
    await callback.message.answer(
        "🎟 <b>Промокоды TEYZUS</b>\n\n"
        f"Всего: <b>{len(promos)}</b>",
        parse_mode="HTML",
        reply_markup=promo_list_keyboard(
            promos
        ),
    )
    await callback.answer()
