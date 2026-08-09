from __future__ import annotations

from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from database.session import get_session
from database.models import User

from services.tasks import (
    get_user_tasks,
    complete_task,
    format_reward,
)


router = Router(
    name="tasks"
)


# =========================================================
# HELPERS
# =========================================================

async def get_user_by_telegram_id(
    telegram_id: int,
) -> User | None:

    from sqlalchemy import select

    async with get_session() as session:

        result = await session.execute(
            select(User).where(
                User.telegram_id
                == telegram_id
            )
        )

        return (
            result.scalar_one_or_none()
        )


# =========================================================
# TASK BUTTON
# =========================================================

def tasks_keyboard(
    tasks: list[dict],
) -> InlineKeyboardMarkup:

    buttons = []

    for task in tasks:

        if task["completed"]:
            text = (
                f"✅ {task['title']}"
            )
        elif task["only_premium"]:
            text = (
                f"💎 {task['title']}"
            )
        else:
            text = (
                f"📋 {task['title']}"
            )

        buttons.append(
            [
                InlineKeyboardButton(
                    text=text,
                    callback_data=(
                        f"task:{task['id']}"
                    ),
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="🔄 Обновить",
                callback_data="tasks:refresh",
            )
        ]
    )

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


# =========================================================
# TASKS MENU
# =========================================================

@router.callback_query(
    F.data == "tasks"
)
async def tasks_callback(
    callback: CallbackQuery,
):

    user = await get_user_by_telegram_id(
        callback.from_user.id
    )

    if user is None:

        await callback.answer(
            "Сначала зарегистрируйся.",
            show_alert=True,
        )

        return

    async with get_session() as session:

        tasks = await get_user_tasks(
            session,
            user,
        )

    if not tasks:

        await callback.message.edit_text(
            "📋 <b>Задания</b>\n\n"
            "Сейчас доступных заданий нет.",
        )

        await callback.answer()

        return

    text = (
        "📋 <b>Задания TEYZUS</b>\n\n"
        "Выбери задание ниже.\n\n"
        "🎁 Выполняй задания и получай "
        "награды."
    )

    await callback.message.edit_text(
        text,
        reply_markup=tasks_keyboard(
            tasks
        ),
    )

    await callback.answer()


# =========================================================
# REFRESH
# =========================================================

@router.callback_query(
    F.data == "tasks:refresh"
)
async def tasks_refresh(
    callback: CallbackQuery,
):

    user = await get_user_by_telegram_id(
        callback.from_user.id
    )

    if user is None:

        await callback.answer(
            "Пользователь не найден.",
            show_alert=True,
        )

        return

    async with get_session() as session:

        tasks = await get_user_tasks(
            session,
            user,
        )

    if not tasks:

        await callback.message.edit_text(
            "📋 <b>Задания</b>\n\n"
            "Сейчас доступных заданий нет."
        )

    else:

        await callback.message.edit_text(
            "📋 <b>Задания TEYZUS</b>\n\n"
            "Выбери задание:",
            reply_markup=tasks_keyboard(
                tasks
            ),
        )

    await callback.answer(
        "Обновлено"
    )


# =========================================================
# TASK DETAILS
# =========================================================

@router.callback_query(
    F.data.startswith("task:")
)
async def task_details(
    callback: CallbackQuery,
):

    try:
        task_id = int(
            callback.data.split(
                ":"
            )[1]
        )
    except (
        ValueError,
        IndexError,
    ):

        await callback.answer(
            "Некорректное задание.",
            show_alert=True,
        )

        return

    user = await get_user_by_telegram_id(
        callback.from_user.id
    )

    if user is None:

        await callback.answer(
            "Пользователь не найден.",
            show_alert=True,
        )

        return

    async with get_session() as session:

        from database.repositories.tasks import (
            get_task,
        )

        task = await get_task(
            session,
            task_id,
        )

    if task is None:

        await callback.answer(
            "Задание не найдено.",
            show_alert=True,
        )

        return

    reward = format_reward(
        task.reward_type,
        task.reward_amount,
        task.premium_days,
    )

    period_map = {
        "daily": "📅 Ежедневное",
        "weekly": "📆 Еженедельное",
        "monthly": "🗓 Ежемесячное",
        "permanent": "♾ Постоянное",
    }

    from services.tasks import (
        get_period,
    )

    period = period_map.get(
        get_period(task),
        "📋 Задание",
    )

    text = (
        f"📋 <b>{task.title}</b>\n\n"
    )

    if task.description:
        text += (
            f"{task.description}\n\n"
        )

    text += (
        f"{period}\n"
        f"🎁 Награда: <b>{reward}</b>\n"
    )

    if task.only_premium:
        text += (
            "\n💎 Доступно только "
            "Premium пользователям.\n"
        )

    keyboard = []

    keyboard.append(
        [
            InlineKeyboardButton(
                text="✅ Выполнить",
                callback_data=(
                    f"task_complete:{task.id}"
                ),
            )
        ]
    )

    keyboard.append(
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="tasks",
            )
        ]
    )

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        ),
    )

    await callback.answer()


# =========================================================
# COMPLETE
# =========================================================

@router.callback_query(
    F.data.startswith(
        "task_complete:"
    )
)
async def task_complete(
    callback: CallbackQuery,
):

    try:

        task_id = int(
            callback.data.split(
                ":"
            )[1]
        )

    except (
        ValueError,
        IndexError,
    ):

        await callback.answer(
            "Ошибка задания.",
            show_alert=True,
        )

        return

    async with get_session() as session:

        from sqlalchemy import select

        result = await session.execute(
            select(User).where(
                User.telegram_id
                == callback.from_user.id
            )
        )

        user = (
            result.scalar_one_or_none()
        )

        if user is None:

            await callback.answer(
                "Пользователь не найден.",
                show_alert=True,
            )

            return

        result = await session.execute(
            select(
                __import__(
                    "database.models",
                    fromlist=["Task"]
                ).Task
            ).where(
                __import__(
                    "database.models",
                    fromlist=["Task"]
                ).Task.id
                == task_id
            )
        )

        task = (
            result.scalar_one_or_none()
        )

        if task is None:

            await callback.answer(
                "Задание не найдено.",
                show_alert=True,
            )

            return

        # -------------------------------------------------
        # Здесь позже будет реальная проверка задания.
        #
        # Например:
        #
        # subscribe_channel
        # search
        # referral
        # promo
        # open_miniapp
        #
        # Сейчас кнопка используется
        # для выполнения задач,
        # которые уже подтверждены.
        # -------------------------------------------------

        result = await complete_task(
            session=session,
            user=user,
            task_id=task_id,
        )

    if result.success:

        await callback.message.edit_text(
            "🎉 <b>Задание выполнено!</b>\n\n"
            f"{result.message}\n\n"
            "Награда уже начислена "
            "на твой аккаунт."
        )

        await callback.answer(
            "Награда получена! 🎉"
        )

    else:

        await callback.answer(
            result.message,
            show_alert=True,
        )
