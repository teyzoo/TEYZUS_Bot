from __future__ import annotations

from datetime import datetime, timedelta, timezone

from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
)
from aiogram.fsm.context import FSMContext

from config import settings

from database.session import get_session
from database.repositories.tasks import TaskRepository

from bot.states.tasks import (
    CreateTaskState,
)

from bot.keyboards.tasks import (
    task_admin_menu_keyboard,
    task_type_keyboard,
    reward_type_keyboard,
    task_period_keyboard,
    yes_no_keyboard,
)


router = Router()


# =========================================================
# ADMIN CHECK
# =========================================================

def is_admin(
    telegram_id: int,
) -> bool:

    owner_id = getattr(
        settings,
        "owner_id",
        0,
    )

    admin_ids = getattr(
        settings,
        "admin_ids",
        [],
    )

    if telegram_id == owner_id:
        return True

    if telegram_id in admin_ids:
        return True

    return False


# =========================================================
# TASK MENU
# =========================================================

@router.callback_query(
    F.data == "admin:tasks"
)
async def admin_tasks_menu(
    callback: CallbackQuery,
):

    if not is_admin(
        callback.from_user.id
    ):

        await callback.answer(
            "⛔ Нет доступа.",
            show_alert=True,
        )

        return

    await callback.message.edit_text(
        "📋 <b>Управление заданиями</b>\n\n"
        "Здесь можно создавать и "
        "управлять заданиями.",
        reply_markup=(
            task_admin_menu_keyboard()
        ),
    )

    await callback.answer()


# =========================================================
# CREATE
# =========================================================

@router.callback_query(
    F.data == "task:create"
)
async def task_create(
    callback: CallbackQuery,
    state: FSMContext,
):

    if not is_admin(
        callback.from_user.id
    ):

        await callback.answer(
            "⛔ Нет доступа.",
            show_alert=True,
        )

        return

    await state.clear()

    await state.set_state(
        CreateTaskState.title
    )

    await callback.message.edit_text(
        "➕ <b>Создание задания</b>\n\n"
        "Введите название задания:"
    )

    await callback.answer()


# =========================================================
# TITLE
# =========================================================

@router.message(
    CreateTaskState.title
)
async def task_title(
    message: Message,
    state: FSMContext,
):

    title = (
        message.text or ""
    ).strip()

    if not title:

        await message.answer(
            "❌ Название не может быть пустым."
        )

        return

    await state.update_data(
        title=title
    )

    await state.set_state(
        CreateTaskState.description
    )

    await message.answer(
        "Введите описание задания.\n\n"
        "Если описание не нужно — отправьте <code>-</code>."
    )


# =========================================================
# DESCRIPTION
# =========================================================

@router.message(
    CreateTaskState.description
)
async def task_description(
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
        CreateTaskState.task_type
    )

    await message.answer(
        "Выберите тип задания:",
        reply_markup=(
            task_type_keyboard()
        ),
    )


# =========================================================
# TASK TYPE
# =========================================================

@router.callback_query(
    CreateTaskState.task_type,
    F.data.startswith(
        "task_type:"
    ),
)
async def task_type(
    callback: CallbackQuery,
    state: FSMContext,
):

    task_type_value = (
        callback.data
        .split(":", 1)[1]
    )

    await state.update_data(
        task_type=task_type_value
    )

    await state.set_state(
        CreateTaskState.target_value
    )

    await callback.message.edit_text(
        "🎯 <b>Целевое значение</b>\n\n"
        "Например:\n"
        "<code>@channel</code>\n"
        "<code>5</code>\n"
        "<code>username</code>\n"
        "<code>https://t.me/...</code>\n\n"
        "Если target не нужен — отправьте <code>-</code>."
    )

    await callback.answer()


# =========================================================
# TARGET
# =========================================================

@router.message(
    CreateTaskState.target_value
)
async def task_target(
    message: Message,
    state: FSMContext,
):

    value = (
        message.text or ""
    ).strip()

    if value == "-":
        value = None

    await state.update_data(
        target_value=value
    )

    await state.set_state(
        CreateTaskState.reward_type
    )

    await message.answer(
        "🎁 Выберите награду:",
        reply_markup=(
            reward_type_keyboard()
        ),
    )


# =========================================================
# REWARD TYPE
# =========================================================

@router.callback_query(
    CreateTaskState.reward_type,
    F.data.startswith(
        "reward_type:"
    ),
)
async def task_reward_type(
    callback: CallbackQuery,
    state: FSMContext,
):

    reward_type = (
        callback.data
        .split(":", 1)[1]
    )

    await state.update_data(
        reward_type=reward_type
    )

    await state.set_state(
        CreateTaskState.reward_amount
    )

    await callback.message.edit_text(
        "Введите количество награды:\n\n"
        "Например:\n"
        "<code>100</code>"
    )

    await callback.answer()


# =========================================================
# REWARD AMOUNT
# =========================================================

@router.message(
    CreateTaskState.reward_amount
)
async def task_reward_amount(
    message: Message,
    state: FSMContext,
):

    try:

        amount = int(
            (
                message.text or ""
            ).strip()
        )

    except ValueError:

        await message.answer(
            "❌ Введите целое число."
        )

        return

    if amount < 0:

        await message.answer(
            "❌ Значение не может быть отрицательным."
        )

        return

    await state.update_data(
        reward_amount=amount
    )

    data = await state.get_data()

    if data.get(
        "reward_type"
    ) == "premium":

        await state.set_state(
            CreateTaskState.premium_days
        )

        await message.answer(
            "💎 На сколько дней Premium?\n\n"
            "Введите количество дней."
        )

        return

    await state.update_data(
        premium_days=0
    )

    await state.set_state(
        CreateTaskState.period
    )

    await message.answer(
        "Выберите период задания:",
        reply_markup=(
            task_period_keyboard()
        ),
    )


# =========================================================
# PREMIUM DAYS
# =========================================================

@router.message(
    CreateTaskState.premium_days
)
async def task_premium_days(
    message: Message,
    state: FSMContext,
):

    try:

        days = int(
            (
                message.text or ""
            ).strip()
        )

    except ValueError:

        await message.answer(
            "❌ Введите количество дней."
        )

        return

    if days <= 0:

        await message.answer(
            "❌ Количество дней должно быть больше нуля."
        )

        return

    await state.update_data(
        premium_days=days
    )

    await state.set_state(
        CreateTaskState.period
    )

    await message.answer(
        "Выберите период задания:",
        reply_markup=(
            task_period_keyboard()
        ),
    )


# =========================================================
# PERIOD
# =========================================================

@router.callback_query(
    CreateTaskState.period,
    F.data.startswith(
        "task_period:"
    ),
)
async def task_period(
    callback: CallbackQuery,
    state: FSMContext,
):

    period = (
        callback.data
        .split(":", 1)[1]
    )

    await state.update_data(
        period=period
    )

    if period == "permanent":

        await state.update_data(
            duration=0
        )

        await state.set_state(
            CreateTaskState.max_completions
        )

        await callback.message.edit_text(
            "Введите максимальное количество "
            "выполнений задания.\n\n"
            "Например: <code>1000</code>\n"
            "Или <code>0</code> — без лимита."
        )

    else:

        await state.set_state(
            CreateTaskState.duration
        )

        await callback.message.edit_text(
            "⏱ На сколько дней создать задание?\n\n"
            "Например: <code>7</code>"
        )

    await callback.answer()


# =========================================================
# DURATION
# =========================================================

@router.message(
    CreateTaskState.duration
)
async def task_duration(
    message: Message,
    state: FSMContext,
):

    try:

        duration = int(
            (
                message.text or ""
            ).strip()
        )

    except ValueError:

        await message.answer(
            "❌ Введите количество дней."
        )

        return

    if duration <= 0:

        await message.answer(
            "❌ Количество дней должно быть больше нуля."
        )

        return

    await state.update_data(
        duration=duration
    )

    await state.set_state(
        CreateTaskState.max_completions
    )

    await message.answer(
        "Введите максимальное количество "
        "выполнений задания.\n\n"
        "Например: <code>1000</code>\n"
        "Или <code>0</code> — без лимита."
    )


# =========================================================
# MAX COMPLETIONS
# =========================================================

@router.message(
    CreateTaskState.max_completions
)
async def task_max_completions(
    message: Message,
    state: FSMContext,
):

    try:

        value = int(
            (
                message.text or ""
            ).strip()
        )

    except ValueError:

        await message.answer(
            "❌ Введите число."
        )

        return

    if value < 0:

        await message.answer(
            "❌ Значение не может быть отрицательным."
        )

        return

    if value == 0:
        value = None

    await state.update_data(
        max_completions=value
    )

    await state.set_state(
        CreateTaskState.max_completions_per_user
    )

    await message.answer(
        "👤 Сколько раз один пользователь "
        "может выполнить задание?\n\n"
        "Например: <code>1</code>\n"
        "Для многократного выполнения "
        "можно указать больше."
    )


# =========================================================
# MAX PER USER
# =========================================================

@router.message(
    CreateTaskState.max_completions_per_user
)
async def task_max_per_user(
    message: Message,
    state: FSMContext,
):

    try:

        value = int(
            (
                message.text or ""
            ).strip()
        )

    except ValueError:

        await message.answer(
            "❌ Введите число."
        )

        return

    if value <= 0:

        await message.answer(
            "❌ Значение должно быть больше нуля."
        )

        return

    await state.update_data(
        max_completions_per_user=value
    )

    await state.set_state(
        CreateTaskState.only_premium
    )

    await message.answer(
        "💎 Сделать задание только для Premium?",
        reply_markup=yes_no_keyboard(
            "task_premium:yes",
            "task_premium:no",
        ),
    )


# =========================================================
# ONLY PREMIUM
# =========================================================

@router.callback_query(
    CreateTaskState.only_premium,
    F.data.startswith(
        "task_premium:"
    ),
)
async def task_only_premium(
    callback: CallbackQuery,
    state: FSMContext,
):

    value = (
        callback.data
        .split(":", 1)[1]
        == "yes"
    )

    await state.update_data(
        only_premium=value
    )

    await state.set_state(
        CreateTaskState.repeatable
    )

    await callback.message.edit_text(
        "🔁 Сделать задание повторяемым?",
        reply_markup=yes_no_keyboard(
            "task_repeat:yes",
            "task_repeat:no",
        ),
    )

    await callback.answer()


# =========================================================
# REPEATABLE
# =========================================================

@router.callback_query(
    CreateTaskState.repeatable,
    F.data.startswith(
        "task_repeat:"
    ),
)
async def task_repeatable(
    callback: CallbackQuery,
    state: FSMContext,
):

    value = (
        callback.data
        .split(":", 1)[1]
        == "yes"
    )

    await state.update_data(
        repeatable=value
    )

    await state.set_state(
        CreateTaskState.sort_order
    )

    await callback.message.edit_text(
        "🔢 Введите порядок отображения.\n\n"
        "Например: <code>0</code>"
    )

    await callback.answer()


# =========================================================
# SORT
# =========================================================

@router.message(
    CreateTaskState.sort_order
)
async def task_sort(
    message: Message,
    state: FSMContext,
):

    try:

        value = int(
            (
                message.text or ""
            ).strip()
        )

    except ValueError:

        value = 0

    await state.update_data(
        sort_order=value
    )

    await state.set_state(
        CreateTaskState.image_file_id
    )

    await message.answer(
        "🖼 Отправьте изображение задания "
        "или напишите <code>-</code>."
    )


# =========================================================
# IMAGE
# =========================================================

@router.message(
    CreateTaskState.image_file_id
)
async def task_image(
    message: Message,
    state: FSMContext,
):

    file_id = None

    if message.photo:

        file_id = (
            message.photo[-1]
            .file_id
        )

    elif (
        message.text
        and message.text.strip()
        != "-"
    ):

        await message.answer(
            "❌ Отправьте изображение "
            "или <code>-</code>."
        )

        return

    await state.update_data(
        image_file_id=file_id
    )

    data = await state.get_data()

    # =====================================================
    # DATES
    # =====================================================

    now = datetime.now(
        timezone.utc
    )

    starts_at = now

    period = data.get(
        "period"
    )

    duration = int(
        data.get(
            "duration",
            0,
        )
        or 0
    )

    expires_at = None

    if duration > 0:

        expires_at = (
            now
            + timedelta(
                days=duration
            )
        )

    # =====================================================
    # CREATE
    # =====================================================

    async with get_session() as session:

        repository = TaskRepository(
            session
        )

        task = await repository.create_task(
            title=data["title"],
            description=data.get(
                "description"
            ),
            task_type=data[
                "task_type"
            ],
            target_value=data.get(
                "target_value"
            ),
            reward_type=data[
                "reward_type"
            ],
            reward_amount=int(
                data.get(
                    "reward_amount",
                    0,
                )
            ),
            premium_days=int(
                data.get(
                    "premium_days",
                    0,
                )
            ),
            max_completions=data.get(
                "max_completions"
            ),
            max_completions_per_user=data.get(
                "max_completions_per_user",
                1,
            ),
            repeatable=data.get(
                "repeatable",
                False,
            ),
            only_premium=data.get(
                "only_premium",
                False,
            ),
            starts_at=starts_at,
            expires_at=expires_at,
            sort_order=int(
                data.get(
                    "sort_order",
                    0,
                )
            ),
            image_file_id=data.get(
                "image_file_id"
            ),
            created_by=(
                message.from_user.id
                if message.from_user
                else 0
            ),
        )

        await session.commit()

    await state.clear()

    await message.answer(
        "✅ <b>Задание создано!</b>\n\n"
        f"🆔 ID: <code>{task.id}</code>\n"
        f"📌 {task.title}\n"
        f"🛠 Тип: <code>{task.task_type}</code>\n"
        f"🎁 Награда: <code>{task.reward_type}</code>\n"
        f"💎 Premium-only: "
        f"{'Да' if task.only_premium else 'Нет'}",
        reply_markup=(
            task_admin_menu_keyboard()
        ),
    )
