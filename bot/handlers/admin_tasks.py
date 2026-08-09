from __future__ import annotations

from datetime import datetime, timezone

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from sqlalchemy import select

from database.models import User, Task
from database.session import get_session


router = Router()


# =========================================================
# FSM
# =========================================================

class CreateTaskState(StatesGroup):
    title = State()
    description = State()
    task_type = State()
    target_value = State()
    period = State()
    reward_type = State()
    reward_amount = State()
    premium_days = State()
    max_completions = State()
    max_completions_per_user = State()
    repeatable = State()
    only_premium = State()
    only_new_users = State()
    starts_at = State()
    expires_at = State()


# =========================================================
# ACCESS
# =========================================================

async def get_admin(
    telegram_id: int,
):
    async with get_session() as session:

        user = await session.scalar(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        if not user:
            return None

        if user.role not in {
            "owner",
            "admin",
        }:
            return None

        return user


# =========================================================
# ADMIN TASK MENU
# =========================================================

@router.callback_query(
    F.data == "admin_tasks"
)
async def admin_tasks_menu(
    callback: CallbackQuery,
):

    user = await get_admin(
        callback.from_user.id
    )

    if not user:
        await callback.answer(
            "Нет доступа.",
            show_alert=True,
        )
        return

    builder = InlineKeyboardBuilder()

    builder.button(
        text="➕ Создать задание",
        callback_data="admin_task_create",
    )

    builder.button(
        text="📋 Все задания",
        callback_data="admin_tasks_list",
    )

    builder.button(
        text="📊 Статистика",
        callback_data="admin_tasks_stats",
    )

    builder.adjust(1)

    await callback.message.edit_text(
        "🎯 <b>Управление заданиями</b>\n\n"
        "Здесь можно создавать и "
        "управлять заданиями TEYZUS.",
        reply_markup=builder.as_markup(),
    )

    await callback.answer()


# =========================================================
# CREATE
# =========================================================

@router.callback_query(
    F.data == "admin_task_create"
)
async def create_task_start(
    callback: CallbackQuery,
    state: FSMContext,
):

    user = await get_admin(
        callback.from_user.id
    )

    if not user:
        await callback.answer(
            "Нет доступа.",
            show_alert=True,
        )
        return

    await state.clear()

    await state.set_state(
        CreateTaskState.title
    )

    await callback.message.edit_text(
        "➕ <b>Создание задания</b>\n\n"
        "Шаг 1/15\n\n"
        "Введите название задания:"
    )

    await callback.answer()


# =========================================================
# TITLE
# =========================================================

@router.message(
    CreateTaskState.title
)
async def create_title(
    message: Message,
    state: FSMContext,
):

    title = message.text.strip()

    if not title:
        await message.answer(
            "Название не может быть пустым."
        )
        return

    await state.update_data(
        title=title
    )

    await state.set_state(
        CreateTaskState.description
    )

    await message.answer(
        "Шаг 2/15\n\n"
        "Введите описание задания.\n\n"
        "Если описание не нужно, "
        "напишите: <code>-</code>"
    )


# =========================================================
# DESCRIPTION
# =========================================================

@router.message(
    CreateTaskState.description
)
async def create_description(
    message: Message,
    state: FSMContext,
):

    description = message.text.strip()

    if description == "-":
        description = None

    await state.update_data(
        description=description
    )

    builder = InlineKeyboardBuilder()

    task_types = [
        ("📢 Подписка", "subscribe_channel"),
        ("🔎 Поиск", "search"),
        ("👥 Реферал", "referral"),
        ("🎟 Промокод", "promo"),
        ("📱 Mini App", "open_miniapp"),
        ("💎 Premium", "premium"),
        ("⚙️ Свободное", "custom"),
    ]

    for title, value in task_types:
        builder.button(
            text=title,
            callback_data=f"tasktype:{value}",
        )

    builder.adjust(2)

    await state.set_state(
        CreateTaskState.task_type
    )

    await message.answer(
        "Шаг 3/15\n\n"
        "Выберите тип задания:",
        reply_markup=builder.as_markup(),
    )


# =========================================================
# TASK TYPE
# =========================================================

@router.callback_query(
    CreateTaskState.task_type,
    F.data.startswith("tasktype:")
)
async def create_task_type(
    callback: CallbackQuery,
    state: FSMContext,
):

    task_type = callback.data.split(
        ":",
        1,
    )[1]

    await state.update_data(
        task_type=task_type
    )

    await state.set_state(
        CreateTaskState.target_value
    )

    examples = {
        "subscribe_channel":
            "@channel",
        "search":
            "например: 5",
        "referral":
            "например: 3",
        "promo":
            "например: PROMO2026",
        "open_miniapp":
            "-",
        "premium":
            "-",
        "custom":
            "любое значение",
    }

    example = examples.get(
        task_type,
        "-",
    )

    await callback.message.edit_text(
        "Шаг 4/15\n\n"
        "Введите цель задания.\n\n"
        f"Пример:\n"
        f"<code>{example}</code>\n\n"
        "Если цель не нужна — <code>-</code>"
    )

    await callback.answer()


# =========================================================
# TARGET
# =========================================================

@router.message(
    CreateTaskState.target_value
)
async def create_target(
    message: Message,
    state: FSMContext,
):

    target = message.text.strip()

    if target == "-":
        target = None

    await state.update_data(
        target_value=target
    )

    builder = InlineKeyboardBuilder()

    builder.button(
        text="📅 Ежедневное",
        callback_data="period:daily",
    )

    builder.button(
        text="🗓 Еженедельное",
        callback_data="period:weekly",
    )

    builder.button(
        text="📆 Ежемесячное",
        callback_data="period:monthly",
    )

    builder.button(
        text="♾ Постоянное",
        callback_data="period:permanent",
    )

    builder.adjust(2)

    await state.set_state(
        CreateTaskState.period
    )

    await message.answer(
        "Шаг 5/15\n\n"
        "Выберите период задания:",
        reply_markup=builder.as_markup(),
    )


# =========================================================
# PERIOD
# =========================================================

@router.callback_query(
    CreateTaskState.period,
    F.data.startswith("period:")
)
async def create_period(
    callback: CallbackQuery,
    state: FSMContext,
):

    period = callback.data.split(
        ":",
        1,
    )[1]

    await state.update_data(
        period=period
    )

    builder = InlineKeyboardBuilder()

    rewards = [
        ("💰 Баланс ₽", "balance"),
        ("⭐ Stars", "stars"),
        ("🔎 Поиски", "searches"),
        ("🎯 Ловушки", "traps"),
        ("🏷 Скидка", "discount"),
        ("💎 Premium", "premium"),
    ]

    for title, value in rewards:
        builder.button(
            text=title,
            callback_data=f"reward:{value}",
        )

    builder.adjust(2)

    await state.set_state(
        CreateTaskState.reward_type
    )

    await callback.message.edit_text(
        "Шаг 6/15\n\n"
        "Выберите награду:",
        reply_markup=builder.as_markup(),
    )

    await callback.answer()


# =========================================================
# REWARD TYPE
# =========================================================

@router.callback_query(
    CreateTaskState.reward_type,
    F.data.startswith("reward:")
)
async def create_reward_type(
    callback: CallbackQuery,
    state: FSMContext,
):

    reward_type = callback.data.split(
        ":",
        1,
    )[1]

    await state.update_data(
        reward_type=reward_type
    )

    if reward_type == "premium":

        await state.set_state(
            CreateTaskState.premium_days
        )

        await callback.message.edit_text(
            "Шаг 7/15\n\n"
            "Введите количество дней Premium:"
        )

    else:

        await state.set_state(
            CreateTaskState.reward_amount
        )

        await callback.message.edit_text(
            "Шаг 7/15\n\n"
            "Введите количество награды:"
        )

    await callback.answer()


# =========================================================
# REWARD AMOUNT
# =========================================================

@router.message(
    CreateTaskState.reward_amount
)
async def create_reward_amount(
    message: Message,
    state: FSMContext,
):

    try:
        amount = int(
            message.text.strip()
        )

        if amount < 0:
            raise ValueError

    except ValueError:
        await message.answer(
            "Введите целое число."
        )
        return

    await state.update_data(
        reward_amount=amount,
        premium_days=0,
    )

    await state.set_state(
        CreateTaskState.max_completions
    )

    await message.answer(
        "Шаг 8/15\n\n"
        "Максимальное количество "
        "выполнений всеми пользователями.\n\n"
        "Введите число или <code>0</code> "
        "для безлимита."
    )


# =========================================================
# PREMIUM DAYS
# =========================================================

@router.message(
    CreateTaskState.premium_days
)
async def create_premium_days(
    message: Message,
    state: FSMContext,
):

    try:
        days = int(
            message.text.strip()
        )

        if days <= 0:
            raise ValueError

    except ValueError:
        await message.answer(
            "Введите положительное число дней."
        )
        return

    await state.update_data(
        reward_amount=0,
        premium_days=days,
    )

    await state.set_state(
        CreateTaskState.max_completions
    )

    await message.answer(
        "Шаг 8/15\n\n"
        "Максимальное количество "
        "выполнений всеми пользователями.\n\n"
        "Введите число или <code>0</code> "
        "для безлимита."
    )


# =========================================================
# MAX COMPLETIONS
# =========================================================

@router.message(
    CreateTaskState.max_completions
)
async def create_max_completions(
    message: Message,
    state: FSMContext,
):

    try:
        value = int(
            message.text.strip()
        )

        if value < 0:
            raise ValueError

    except ValueError:
        await message.answer(
            "Введите число 0 или больше."
        )
        return

    await state.update_data(
        max_completions=(
            None
            if value == 0
            else value
        )
    )

    await state.set_state(
        CreateTaskState.max_completions_per_user
    )

    await message.answer(
        "Шаг 9/15\n\n"
        "Сколько раз один пользователь "
        "может выполнить задание?\n\n"
        "Например: <code>1</code>"
    )


# =========================================================
# PER USER LIMIT
# =========================================================

@router.message(
    CreateTaskState.max_completions_per_user
)
async def create_per_user_limit(
    message: Message,
    state: FSMContext,
):

    try:
        value = int(
            message.text.strip()
        )

        if value < 0:
            raise ValueError

    except ValueError:
        await message.answer(
            "Введите число 0 или больше."
        )
        return

    await state.update_data(
        max_completions_per_user=(
            None
            if value == 0
            else value
        )
    )

    builder = InlineKeyboardBuilder()

    builder.button(
        text="🔄 Да",
        callback_data="repeat:yes",
    )

    builder.button(
        text="❌ Нет",
        callback_data="repeat:no",
    )

    await state.set_state(
        CreateTaskState.repeatable
    )

    await message.answer(
        "Шаг 10/15\n\n"
        "Можно ли выполнять задание повторно?",
        reply_markup=builder.as_markup(),
    )


# =========================================================
# REPEATABLE
# =========================================================

@router.callback_query(
    CreateTaskState.repeatable,
    F.data.startswith("repeat:")
)
async def create_repeatable(
    callback: CallbackQuery,
    state: FSMContext,
):

    value = callback.data.endswith(
        ":yes"
    )

    await state.update_data(
        repeatable=value
    )

    builder = InlineKeyboardBuilder()

    builder.button(
        text="💎 Только Premium",
        callback_data="onlypremium:yes",
    )

    builder.button(
        text="👥 Все пользователи",
        callback_data="onlypremium:no",
    )

    builder.adjust(1)

    await state.set_state(
        CreateTaskState.only_premium
    )

    await callback.message.edit_text(
        "Шаг 11/15\n\n"
        "Для кого доступно задание?",
        reply_markup=builder.as_markup(),
    )

    await callback.answer()


# =========================================================
# ONLY PREMIUM
# =========================================================

@router.callback_query(
    CreateTaskState.only_premium,
    F.data.startswith("onlypremium:")
)
async def create_only_premium(
    callback: CallbackQuery,
    state: FSMContext,
):

    value = callback.data.endswith(
        ":yes"
    )

    await state.update_data(
        only_premium=value
    )

    builder = InlineKeyboardBuilder()

    builder.button(
        text="👶 Только новые",
        callback_data="onlynew:yes",
    )

    builder.button(
        text="👥 Все",
        callback_data="onlynew:no",
    )

    await state.set_state(
        CreateTaskState.only_new_users
    )

    await callback.message.edit_text(
        "Шаг 12/15\n\n"
        "Ограничить задание только "
        "новыми пользователями?",
        reply_markup=builder.as_markup(),
    )

    await callback.answer()


# =========================================================
# ONLY NEW
# =========================================================

@router.callback_query(
    CreateTaskState.only_new_users,
    F.data.startswith("onlynew:")
)
async def create_only_new(
    callback: CallbackQuery,
    state: FSMContext,
):

    value = callback.data.endswith(
        ":yes"
    )

    await state.update_data(
        only_new_users=value
    )

    await state.set_state(
        CreateTaskState.starts_at
    )

    await callback.message.edit_text(
        "Шаг 13/15\n\n"
        "Введите дату начала.\n\n"
        "Формат:\n"
        "<code>2026-08-10 12:00</code>\n\n"
        "Или <code>-</code> для запуска сразу."
    )

    await callback.answer()


# =========================================================
# START DATE
# =========================================================

@router.message(
    CreateTaskState.starts_at
)
async def create_start_date(
    message: Message,
    state: FSMContext,
):

    value = message.text.strip()

    if value == "-":
        starts_at = None
    else:
        try:
            starts_at = datetime.strptime(
                value,
                "%Y-%m-%d %H:%M",
            ).replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            await message.answer(
                "Неверный формат.\n\n"
                "Используйте:\n"
                "<code>2026-08-10 12:00</code>"
            )
            return

    await state.update_data(
        starts_at=starts_at
    )

    await state.set_state(
        CreateTaskState.expires_at
    )

    await message.answer(
        "Шаг 14/15\n\n"
        "Введите дату окончания.\n\n"
        "Формат:\n"
        "<code>2026-08-31 23:59</code>\n\n"
        "Или <code>-</code> для бессрочного задания."
    )


# =========================================================
# EXPIRES
# =========================================================

@router.message(
    CreateTaskState.expires_at
)
async def create_expires(
    message: Message,
    state: FSMContext,
):

    value = message.text.strip()

    if value == "-":
        expires_at = None
    else:
        try:
            expires_at = datetime.strptime(
                value,
                "%Y-%m-%d %H:%M",
            ).replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            await message.answer(
                "Неверный формат."
            )
            return

    await state.update_data(
        expires_at=expires_at
    )

    data = await state.get_data()

    async with get_session() as session:

        task = Task(
            title=data["title"],
            description=data[
                "description"
            ],
            task_type=data[
                "task_type"
            ],
            target_value=data[
                "target_value"
            ],
            period=data[
                "period"
            ],
            reward_type=data[
                "reward_type"
            ],
            reward_amount=data[
                "reward_amount"
            ],
            premium_days=data[
                "premium_days"
            ],
            max_completions=data[
                "max_completions"
            ],
            max_completions_per_user=data[
                "max_completions_per_user"
            ],
            repeatable=data[
                "repeatable"
            ],
            only_premium=data[
                "only_premium"
            ],
            only_new_users=data[
                "only_new_users"
            ],
            starts_at=data[
                "starts_at"
            ],
            expires_at=expires_at,
            is_active=True,
            sort_order=0,
            created_by=(
                callback_user_id
                if False
                else message.from_user.id
            ),
        )

        session.add(task)

        await session.commit()

        await session.refresh(task)

        task_id = task.id

    await state.clear()

    await message.answer(
        "✅ <b>Задание создано!</b>\n\n"
        f"🆔 ID: <code>{task_id}</code>\n"
        f"🎯 {data['title']}\n"
        f"📅 {data['period']}\n"
        f"⚙️ {data['task_type']}\n"
        f"🎁 {data['reward_type']}\n\n"
        "Задание уже активно."
    )


# =========================================================
# TASK LIST
# =========================================================

@router.callback_query(
    F.data == "admin_tasks_list"
)
async def admin_tasks_list(
    callback: CallbackQuery,
):

    user = await get_admin(
        callback.from_user.id
    )

    if not user:
        await callback.answer(
            "Нет доступа.",
            show_alert=True,
        )
        return

    async with get_session() as session:

        result = await session.execute(
            select(Task)
            .order_by(
                Task.id.desc()
            )
            .limit(50)
        )

        tasks = result.scalars().all()

    if not tasks:

        await callback.message.edit_text(
            "📋 Заданий пока нет.",
        )

        await callback.answer()
        return

    builder = InlineKeyboardBuilder()

    text = (
        "📋 <b>Задания</b>\n\n"
    )

    for task in tasks:

        status = (
            "🟢"
            if task.is_active
            else "🔴"
        )

        premium = (
            "💎"
            if task.only_premium
            else ""
        )

        text += (
            f"{status} "
            f"{premium} "
            f"<b>{task.title}</b>\n"
            f"ID: <code>{task.id}</code>\n"
            f"Выполнений: "
            f"{task.completions_count}\n\n"
        )

        builder.button(
            text=(
                f"{status} "
                f"{task.title[:25]}"
            ),
            callback_data=(
                f"admin_task:{task.id}"
            ),
        )

    builder.adjust(1)

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
    )

    await callback.answer()


# =========================================================
# TASK VIEW
# =========================================================

@router.callback_query(
    F.data.startswith("admin_task:")
)
async def admin_task_view(
    callback: CallbackQuery,
):

    user = await get_admin(
        callback.from_user.id
    )

    if not user:
        await callback.answer(
            "Нет доступа.",
            show_alert=True,
        )
        return

    task_id = int(
        callback.data.split(":")[1]
    )

    async with get_session() as session:

        task = await session.scalar(
            select(Task).where(
                Task.id == task_id
            )
        )

    if not task:

        await callback.answer(
            "Задание не найдено.",
            show_alert=True,
        )
        return

    status = (
        "🟢 Активно"
        if task.is_active
        else "🔴 Выключено"
    )

    premium = (
        "💎 Только Premium"
        if task.only_premium
        else "👥 Все пользователи"
    )

    text = (
        f"🎯 <b>{task.title}</b>\n\n"
        f"🆔 ID: <code>{task.id}</code>\n"
        f"📌 Тип: <code>{task.task_type}</code>\n"
        f"📅 Период: <code>{task.period}</code>\n"
        f"👤 Доступ: {premium}\n"
        f"🔄 Повторяемое: "
        f"{'Да' if task.repeatable else 'Нет'}\n"
        f"🎁 Награда: "
        f"<code>{task.reward_type}</code>\n"
        f"💰 Количество: "
        f"<code>{task.reward_amount}</code>\n"
        f"💎 Premium дней: "
        f"<code>{task.premium_days}</code>\n"
        f"📊 Выполнено: "
        f"<code>{task.completions_count}</code>\n"
        f"📌 Статус: {status}"
    )

    builder = InlineKeyboardBuilder()

    if task.is_active:

        builder.button(
            text="🔴 Выключить",
            callback_data=(
                f"task_disable:{task.id}"
            ),
        )

    else:

        builder.button(
            text="🟢 Включить",
            callback_data=(
                f"task_enable:{task.id}"
            ),
        )

    builder.button(
        text="🗑 Удалить",
        callback_data=(
            f"task_delete:{task.id}"
        ),
    )

    builder.button(
        text="⬅️ Назад",
        callback_data="admin_tasks_list",
    )

    builder.adjust(1)

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
    )

    await callback.answer()


# =========================================================
# ENABLE
# =========================================================

@router.callback_query(
    F.data.startswith("task_enable:")
)
async def enable_task(
    callback: CallbackQuery,
):

    user = await get_admin(
        callback.from_user.id
    )

    if not user:
        await callback.answer(
            "Нет доступа.",
            show_alert=True,
        )
        return

    task_id = int(
        callback.data.split(":")[1]
    )

    async with get_session() as session:

        task = await session.scalar(
            select(Task).where(
                Task.id == task_id
            )
        )

        if not task:
            await callback.answer(
                "Задание не найдено.",
                show_alert=True,
            )
            return

        task.is_active = True

        await session.commit()

    await callback.answer(
        "Задание включено."
    )

    await admin_task_view(
        callback
    )


# =========================================================
# DISABLE
# =========================================================

@router.callback_query(
    F.data.startswith("task_disable:")
)
async def disable_task(
    callback: CallbackQuery,
):

    user = await get_admin(
        callback.from_user.id
    )

    if not user:
        await callback.answer(
            "Нет доступа.",
            show_alert=True,
        )
        return

    task_id = int(
        callback.data.split(":")[1]
    )

    async with get_session() as session:

        task = await session.scalar(
            select(Task).where(
                Task.id == task_id
            )
        )

        if not task:
            await callback.answer(
                "Задание не найдено.",
                show_alert=True,
            )
            return

        task.is_active = False

        await session.commit()

    await callback.answer(
        "Задание выключено."
    )

    await admin_task_view(
        callback
    )


# =========================================================
# DELETE
# =========================================================

@router.callback_query(
    F.data.startswith("task_delete:")
)
async def delete_task(
    callback: CallbackQuery,
):

    user = await get_admin(
        callback.from_user.id
    )

    if not user:
        await callback.answer(
            "Нет доступа.",
            show_alert=True,
        )
        return

    # Удаление специально
    # разрешаем только OWNER.

    if user.role != "owner":

        await callback.answer(
            "Удалять задания может только Owner.",
            show_alert=True,
        )
        return

    task_id = int(
        callback.data.split(":")[1]
    )

    async with get_session() as session:

        task = await session.scalar(
            select(Task).where(
                Task.id == task_id
            )
        )

        if not task:
            await callback.answer(
                "Задание не найдено.",
                show_alert=True,
            )
            return

        await session.delete(task)

        await session.commit()

    await callback.message.edit_text(
        "🗑 <b>Задание удалено.</b>",
    )

    await callback.answer(
        "Удалено."
    )


# =========================================================
# STATISTICS
# =========================================================

@router.callback_query(
    F.data == "admin_tasks_stats"
)
async def admin_tasks_stats(
    callback: CallbackQuery,
):

    user = await get_admin(
        callback.from_user.id
    )

    if not user:
        await callback.answer(
            "Нет доступа.",
            show_alert=True,
        )
        return

    async with get_session() as session:

        result = await session.execute(
            select(Task)
        )

        tasks = result.scalars().all()

    total = len(tasks)

    active = sum(
        1
        for task in tasks
        if task.is_active
    )

    completed = sum(
        task.completions_count
        for task in tasks
    )

    premium_tasks = sum(
        1
        for task in tasks
        if task.only_premium
    )

    await callback.message.edit_text(
        "📊 <b>Статистика заданий</b>\n\n"
        f"🎯 Всего заданий: <b>{total}</b>\n"
        f"🟢 Активных: <b>{active}</b>\n"
        f"💎 Premium: <b>{premium_tasks}</b>\n"
        f"✅ Всего выполнений: <b>{completed}</b>",
    )

    await callback.answer()
