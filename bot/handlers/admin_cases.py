from __future__ import annotations

from aiogram import (
    Router,
    F,
)

from aiogram.types import (
    Message,
    CallbackQuery,
)

from aiogram.fsm.context import (
    FSMContext,
)

from sqlalchemy import (
    select,
    delete,
)

from database.models import (
    User,
    Case,
    CaseReward,
)

from database.session import (
    get_session,
)

from bot.states.cases import (
    CreateCaseState,
    CreateCaseRewardState,
)

from bot.keyboards.cases import (
    owner_cases_keyboard,
    owner_case_menu_keyboard,
    rewards_keyboard,
    reward_types_keyboard,
)


router = Router()


# =========================================================
# OWNER CHECK
# =========================================================

async def is_owner(
    telegram_id: int,
) -> bool:

    async with get_session() as session:

        result = await session.execute(
            select(User).where(
                User.telegram_id
                == telegram_id
            )
        )

        user = (
            result.scalar_one_or_none()
        )

        if user is None:
            return False

        return user.role == "owner"


# =========================================================
# OWNER CASES
# =========================================================

@router.message(
    F.text == "🎁 Управление кейсами"
)
async def admin_cases(
    message: Message,
):

    if not await is_owner(
        message.from_user.id
    ):

        await message.answer(
            "⛔ Доступ запрещён."
        )

        return

    async with get_session() as session:

        result = await session.execute(
            select(Case)
            .order_by(
                Case.sort_order.asc(),
                Case.id.asc(),
            )
        )

        cases = list(
            result.scalars().all()
        )

    await message.answer(
        "👑 <b>УПРАВЛЕНИЕ КЕЙСАМИ</b>\n\n"
        "Здесь ты можешь создавать кейсы, "
        "добавлять награды и управлять ими.",
        reply_markup=owner_cases_keyboard(
            cases
        ),
    )


# =========================================================
# OWNER CASES CALLBACK
# =========================================================

@router.callback_query(
    F.data == "admin_cases"
)
async def admin_cases_callback(
    callback: CallbackQuery,
):

    if not await is_owner(
        callback.from_user.id
    ):

        await callback.answer(
            "⛔ Доступ запрещён.",
            show_alert=True,
        )

        return

    async with get_session() as session:

        result = await session.execute(
            select(Case)
            .order_by(
                Case.sort_order.asc(),
                Case.id.asc(),
            )
        )

        cases = list(
            result.scalars().all()
        )

    await callback.message.edit_text(
        "👑 <b>УПРАВЛЕНИЕ КЕЙСАМИ</b>\n\n"
        "Выбери кейс:",
        reply_markup=owner_cases_keyboard(
            cases
        ),
    )

    await callback.answer()


# =========================================================
# CREATE CASE START
# =========================================================

@router.callback_query(
    F.data == "admin_case_create"
)
async def create_case_start(
    callback: CallbackQuery,
    state: FSMContext,
):

    if not await is_owner(
        callback.from_user.id
    ):

        await callback.answer(
            "⛔ Доступ запрещён.",
            show_alert=True,
        )

        return

    await state.set_state(
        CreateCaseState.title
    )

    await callback.message.answer(
        "➕ <b>Создание кейса</b>\n\n"
        "Введите название кейса:"
    )

    await callback.answer()


# =========================================================
# CREATE CASE TITLE
# =========================================================

@router.message(
    CreateCaseState.title
)
async def create_case_title(
    message: Message,
    state: FSMContext,
):

    title = (
        message.text or ""
    ).strip()

    if not title:

        await message.answer(
            "Название не может быть пустым."
        )

        return

    if len(title) > 255:

        await message.answer(
            "Название слишком длинное."
        )

        return

    await state.update_data(
        title=title
    )

    await state.set_state(
        CreateCaseState.description
    )

    await message.answer(
        "Введите описание кейса.\n\n"
        "Если описание не нужно, "
        "напишите: <code>-</code>"
    )


# =========================================================
# CREATE CASE DESCRIPTION
# =========================================================

@router.message(
    CreateCaseState.description
)
async def create_case_description(
    message: Message,
    state: FSMContext,
):

    description = (
        message.text or ""
    ).strip()

    if description == "-":
        description = None

    await state.update_data(
        description=description
    )

    await state.set_state(
        CreateCaseState.price
    )

    await message.answer(
        "Введите цену кейса в Stars.\n\n"
        "Например:\n"
        "<code>100</code>"
    )


# =========================================================
# CREATE CASE PRICE
# =========================================================

@router.message(
    CreateCaseState.price
)
async def create_case_price(
    message: Message,
    state: FSMContext,
):

    try:

        price = int(
            (message.text or "").strip()
        )

    except ValueError:

        await message.answer(
            "Введите целое число."
        )

        return

    if price <= 0:

        await message.answer(
            "Цена должна быть больше 0."
        )

        return

    data = await state.get_data()

    async with get_session() as session:

        case = Case(
            title=data["title"],
            description=data[
                "description"
            ],
            price_stars=price,
            is_active=True,
            sort_order=0,
            created_by=(
                message.from_user.id
            ),
        )

        session.add(case)

        await session.commit()

        await session.refresh(case)

        case_id = case.id

    await state.clear()

    await message.answer(
        "✅ <b>Кейс создан!</b>\n\n"
        f"🎁 {data['title']}\n"
        f"⭐ Цена: {price}\n\n"
        "Теперь открой управление кейсами "
        "и добавь награды."
    )

    await message.answer(
        "Чтобы открыть Owner Panel, "
        "используй кнопку управления кейсами."
    )


# =========================================================
# CASE DETAILS OWNER
# =========================================================

@router.callback_query(
    F.data.startswith("admin_case:")
)
async def admin_case_details(
    callback: CallbackQuery,
):

    if not await is_owner(
        callback.from_user.id
    ):

        await callback.answer(
            "⛔ Доступ запрещён.",
            show_alert=True,
        )

        return

    case_id = int(
        callback.data.split(":")[1]
    )

    async with get_session() as session:

        result = await session.execute(
            select(Case).where(
                Case.id == case_id
            )
        )

        case = (
            result.scalar_one_or_none()
        )

    if case is None:

        await callback.answer(
            "Кейс не найден.",
            show_alert=True,
        )

        return

    status = (
        "🟢 Включён"
        if case.is_active
        else "🔴 Выключен"
    )

    text = (
        "🎁 <b>КЕЙС</b>\n\n"
        f"Название: <b>{case.title}</b>\n"
        f"Цена: ⭐ {case.price_stars}\n"
        f"Статус: {status}\n"
    )

    if case.description:

        text += (
            f"\n{case.description}\n"
        )

    await callback.message.edit_text(
        text,
        reply_markup=owner_case_menu_keyboard(
            case.id,
            case.is_active,
        ),
    )

    await callback.answer()


# =========================================================
# TOGGLE CASE
# =========================================================

@router.callback_query(
    F.data.startswith(
        "admin_case_toggle:"
    )
)
async def toggle_case(
    callback: CallbackQuery,
):

    if not await is_owner(
        callback.from_user.id
    ):

        await callback.answer(
            "⛔ Доступ запрещён.",
            show_alert=True,
        )

        return

    case_id = int(
        callback.data.split(":")[1]
    )

    async with get_session() as session:

        result = await session.execute(
            select(Case).where(
                Case.id == case_id
            )
        )

        case = (
            result.scalar_one_or_none()
        )

        if case is None:

            await callback.answer(
                "Кейс не найден.",
                show_alert=True,
            )

            return

        case.is_active = (
            not case.is_active
        )

        await session.commit()

        active = case.is_active

    await callback.message.edit_reply_markup(
        reply_markup=owner_case_menu_keyboard(
            case_id,
            active,
        )
    )

    await callback.answer(
        "Статус изменён."
    )


# =========================================================
# DELETE CASE
# =========================================================

@router.callback_query(
    F.data.startswith(
        "admin_case_delete:"
    )
)
async def delete_case(
    callback: CallbackQuery,
):

    if not await is_owner(
        callback.from_user.id
    ):

        await callback.answer(
            "⛔ Доступ запрещён.",
            show_alert=True,
        )

        return

    case_id = int(
        callback.data.split(":")[1]
    )

    async with get_session() as session:

        result = await session.execute(
            select(Case).where(
                Case.id == case_id
            )
        )

        case = (
            result.scalar_one_or_none()
        )

        if case is None:

            await callback.answer(
                "Кейс уже удалён.",
                show_alert=True,
            )

            return

        await session.delete(
            case
        )

        await session.commit()

    await callback.message.edit_text(
        "🗑 <b>Кейс удалён.</b>"
    )

    await callback.answer(
        "Кейс удалён."
    )


# =========================================================
# REWARDS
# =========================================================

@router.callback_query(
    F.data.startswith(
        "admin_rewards:"
    )
)
async def admin_rewards(
    callback: CallbackQuery,
):

    if not await is_owner(
        callback.from_user.id
    ):

        await callback.answer(
            "⛔ Доступ запрещён.",
            show_alert=True,
        )

        return

    case_id = int(
        callback.data.split(":")[1]
    )

    async with get_session() as session:

        case_result = await session.execute(
            select(Case).where(
                Case.id == case_id
            )
        )

        case = (
            case_result.scalar_one_or_none()
        )

        if case is None:

            await callback.answer(
                "Кейс не найден.",
                show_alert=True,
            )

            return

        reward_result = await session.execute(
            select(CaseReward)
            .where(
                CaseReward.case_id
                == case_id
            )
            .order_by(
                CaseReward.sort_order.asc(),
                CaseReward.id.asc(),
            )
        )

        rewards = list(
            reward_result.scalars().all()
        )

    total = sum(
        float(
            reward.chance
        )
        for reward in rewards
        if reward.is_active
    )

    await callback.message.edit_text(
        "🎯 <b>НАГРАДЫ КЕЙСА</b>\n\n"
        f"🎁 {case.title}\n\n"
        f"Сумма активных шансов: "
        f"<b>{total:.2f}%</b>\n\n"
        "Должно быть ровно <b>100%</b>.",
        reply_markup=rewards_keyboard(
            case_id,
            rewards,
        ),
    )

    await callback.answer()


# =========================================================
# ADD REWARD
# =========================================================

@router.callback_query(
    F.data.startswith(
        "admin_reward_add:"
    )
)
async def add_reward_start(
    callback: CallbackQuery,
    state: FSMContext,
):

    if not await is_owner(
        callback.from_user.id
    ):

        await callback.answer(
            "⛔ Доступ запрещён.",
            show_alert=True,
        )

        return

    case_id = int(
        callback.data.split(":")[1]
    )

    await state.update_data(
        case_id=case_id
    )

    await callback.message.answer(
        "🎁 <b>Добавление награды</b>\n\n"
        "Выбери тип награды:"
    )

    await callback.message.answer(
        "Тип награды:",
        reply_markup=reward_types_keyboard(
            case_id
        ),
    )

    await callback.answer()


# =========================================================
# REWARD TYPE
# =========================================================

@router.callback_query(
    F.data.startswith(
        "reward_type:"
    )
)
async def reward_type(
    callback: CallbackQuery,
    state: FSMContext,
):

    if not await is_owner(
        callback.from_user.id
    ):

        await callback.answer(
            "⛔ Доступ запрещён.",
            show_alert=True,
        )

        return

    _, reward_type, case_id = (
        callback.data.split(":")
    )

    await state.update_data(
        case_id=int(case_id),
        reward_type=reward_type,
    )

    await state.set_state(
        CreateCaseRewardState.title
    )

    await callback.message.answer(
        "Введите название награды.\n\n"
        "Например:\n"
        "<code>Premium 30 дней</code>"
    )

    await callback.answer()


# =========================================================
# REWARD TITLE
# =========================================================

@router.message(
    CreateCaseRewardState.title
)
async def reward_title(
    message: Message,
    state: FSMContext,
):

    title = (
        message.text or ""
    ).strip()

    if not title:

        await message.answer(
            "Название не может быть пустым."
        )

        return

    await state.update_data(
        title=title
    )

    await state.set_state(
        CreateCaseRewardState.emoji
    )

    await message.answer(
        "Введите emoji награды.\n\n"
        "Например: 💎\n\n"
        "Или отправьте <code>-</code>."
    )


# =========================================================
# REWARD EMOJI
# =========================================================

@router.message(
    CreateCaseRewardState.emoji
)
async def reward_emoji(
    message: Message,
    state: FSMContext,
):

    emoji = (
        message.text or ""
    ).strip()

    if emoji == "-":
        emoji = "🎁"

    await state.update_data(
        emoji=emoji
    )

    data = await state.get_data()

    if data["reward_type"] == "premium":

        await state.set_state(
            CreateCaseRewardState.premium_days
        )

        await message.answer(
            "Введите количество дней Premium.\n\n"
            "Например:\n"
            "<code>30</code>"
        )

    else:

        await state.set_state(
            CreateCaseRewardState.amount
        )

        await message.answer(
            "Введите количество награды.\n\n"
            "Например:\n"
            "<code>100</code>"
        )


# =========================================================
# PREMIUM DAYS
# =========================================================

@router.message(
    CreateCaseRewardState.premium_days
)
async def reward_premium_days(
    message: Message,
    state: FSMContext,
):

    try:

        days = int(
            (message.text or "").strip()
        )

    except ValueError:

        await message.answer(
            "Введите целое число дней."
        )

        return

    if days <= 0:

        await message.answer(
            "Количество дней должно быть больше 0."
        )

        return

    await state.update_data(
        premium_days=days,
        amount=0,
    )

    await state.set_state(
        CreateCaseRewardState.chance
    )

    await message.answer(
        "Введите шанс этой награды в %.\n\n"
        "Например:\n"
        "<code>5</code>"
    )


# =========================================================
# NORMAL AMOUNT
# =========================================================

@router.message(
    CreateCaseRewardState.amount
)
async def reward_amount(
    message: Message,
    state: FSMContext,
):

    try:

        amount = int(
            (message.text or "").strip()
        )

    except ValueError:

        await message.answer(
            "Введите целое число."
        )

        return

    if amount <= 0:

        await message.answer(
            "Количество должно быть больше 0."
        )

        return

    await state.update_data(
        amount=amount,
        premium_days=0,
    )

    await state.set_state(
        CreateCaseRewardState.chance
    )

    await message.answer(
        "Введите шанс награды в %.\n\n"
        "Например:\n"
        "<code>10</code>"
    )


# =========================================================
# REWARD CHANCE
# =========================================================

@router.message(
    CreateCaseRewardState.chance
)
async def reward_chance(
    message: Message,
    state: FSMContext,
):

    try:

        chance = float(
            (message.text or "")
            .strip()
            .replace(",", ".")
        )

    except ValueError:

        await message.answer(
            "Введите число.\n\n"
            "Например: 5 или 2.5"
        )

        return

    if chance <= 0:

        await message.answer(
            "Шанс должен быть больше 0."
        )

        return

    if chance > 100:

        await message.answer(
            "Шанс не может быть больше 100%."
        )

        return

    data = await state.get_data()

    case_id = int(
        data["case_id"]
    )

    async with get_session() as session:

        reward = CaseReward(
            case_id=case_id,
            title=data["title"],
            emoji=data["emoji"],
            reward_type=data[
                "reward_type"
            ],
            reward_amount=int(
                data.get("amount", 0)
            ),
            premium_days=int(
                data.get(
                    "premium_days",
                    0,
                )
            ),
            chance=chance,
            is_active=True,
            sort_order=0,
        )

        session.add(reward)

        await session.commit()

    await state.clear()

    await message.answer(
        "✅ <b>Награда добавлена!</b>\n\n"
        f"{data['emoji']} "
        f"{data['title']}\n"
        f"🎯 Шанс: {chance:g}%\n\n"
        "Теперь можешь добавить следующую "
        "награду."
    )
