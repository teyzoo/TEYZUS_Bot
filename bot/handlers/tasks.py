from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
)
from aiogram.utils.keyboard import (
    InlineKeyboardBuilder,
)
from sqlalchemy import select

from database.models import (
    Task,
    User,
)
from database.session import (
    get_session,
)
from bot.services.tasks import (
    task_is_active,
    user_can_see_task,
    complete_task,
)

router = Router()


# =========================================================
# TASK LIST
# =========================================================

def task_keyboard(
    tasks: list[Task],
):
    builder = InlineKeyboardBuilder()

    for task in tasks:

        if task.only_premium:
            prefix = "💎"
        else:
            prefix = "🎯"

        builder.button(
            text=(
                f"{prefix} {task.title}"
            ),
            callback_data=(
                f"task:{task.id}"
            ),
        )

    builder.adjust(1)

    return builder.as_markup()


# =========================================================
# TASKS BUTTON
# =========================================================

@router.callback_query(
    F.data == "tasks"
)
async def open_tasks(
    callback: CallbackQuery,
):

    async with get_session() as session:

        user = (
            await session.scalar(
                select(User).where(
                    User.telegram_id
                    == callback.from_user.id
                )
            )
        )

        if not user:
            await callback.answer(
                "Пользователь не найден.",
                show_alert=True,
            )
            return

        result = await session.execute(
            select(Task)
            .where(
                Task.is_active.is_(True)
            )
            .order_by(
                Task.sort_order.asc(),
                Task.id.asc(),
            )
        )

        all_tasks = result.scalars().all()

        tasks = []

        for task in all_tasks:

            if not task_is_active(task):
                continue

            if not user_can_see_task(
                user,
                task,
            ):
                continue

            tasks.append(task)

    if not tasks:

        await callback.message.edit_text(
            "🎯 <b>Задания</b>\n\n"
            "Сейчас доступных заданий нет.",
        )

        await callback.answer()
        return

    text = (
        "🎯 <b>Задания</b>\n\n"
        "Выбери задание:"
    )

    await callback.message.edit_text(
        text,
        reply_markup=task_keyboard(
            tasks
        ),
    )

    await callback.answer()


# =========================================================
# TASK DETAILS
# =========================================================

@router.callback_query(
    F.data.startswith("task:")
)
async def task_details(
    callback: CallbackQuery,
):

    task_id = int(
        callback.data.split(":")[1]
    )

    async with get_session() as session:

        user = (
            await session.scalar(
                select(User).where(
                    User.telegram_id
                    == callback.from_user.id
                )
            )
        )

        task = await session.scalar(
            select(Task).where(
                Task.id == task_id
            )
        )

        if not user or not task:

            await callback.answer(
                "Задание не найдено.",
                show_alert=True,
            )
            return

        if not task_is_active(task):

            await callback.answer(
                "Задание недоступно.",
                show_alert=True,
            )
            return

        if not user_can_see_task(
            user,
            task,
        ):

            await callback.answer(
                "Задание доступно только Premium.",
                show_alert=True,
            )
            return

        reward = ""

        if task.reward_type == "premium":

            reward = (
                f"💎 Premium "
                f"{task.premium_days} дн."
            )

        elif task.reward_type == "balance":

            reward = (
                f"💰 "
                f"{task.reward_amount:,} ₽"
                .replace(",", " ")
            )

        elif task.reward_type == "stars":

            reward = (
                f"⭐ "
                f"{task.reward_amount} Stars"
            )

        elif task.reward_type == "searches":

            reward = (
                f"🔎 "
                f"{task.reward_amount} поисков"
            )

        elif task.reward_type == "traps":

            reward = (
                f"🎯 "
                f"{task.reward_amount} ловушек"
            )

        elif task.reward_type == "discount":

            reward = (
                f"🏷 "
                f"+{task.reward_amount}%"
            )

        else:

            reward = "🎁 Награда"

        period_names = {
            "daily": "Ежедневное",
            "weekly": "Еженедельное",
            "monthly": "Ежемесячное",
            "permanent": "Постоянное",
        }

        period = period_names.get(
            task.period,
            "Задание",
        )

        text = (
            f"🎯 <b>{task.title}</b>\n\n"
            f"{task.description or ''}\n\n"
            f"📅 Тип: {period}\n"
            f"🎁 Награда: {reward}\n"
        )

        if task.repeatable:
            text += (
                "\n🔄 Можно выполнять повторно."
            )

        builder = InlineKeyboardBuilder()

        builder.button(
            text="✅ Выполнить",
            callback_data=(
                f"task_complete:{task.id}"
            ),
        )

        builder.button(
            text="⬅️ Назад",
            callback_data="tasks",
        )

        builder.adjust(1)

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
    )

    await callback.answer()


# =========================================================
# COMPLETE
# =========================================================

@router.callback_query(
    F.data.startswith("task_complete:")
)
async def complete_task_handler(
    callback: CallbackQuery,
):

    task_id = int(
        callback.data.split(":")[1]
    )

    async with get_session() as session:

        user = (
            await session.scalar(
                select(User).where(
                    User.telegram_id
                    == callback.from_user.id
                )
            )
        )

        task = await session.scalar(
            select(Task).where(
                Task.id == task_id
            )
        )

        if not user or not task:

            await callback.answer(
                "Задание не найдено.",
                show_alert=True,
            )
            return

        # Пока базовое выполнение.
        #
        # Для subscribe_channel,
        # search, referral и других
        # типов ниже подключим
        # отдельные проверки.

        if task.task_type == "search":

            await callback.answer(
                "Для этого задания сначала нужно выполнить поиск.",
                show_alert=True,
            )
            return

        success, message = (
            await complete_task(
                session=session,
                user=user,
                task=task,
            )
        )

    if not success:

        await callback.answer(
            message,
            show_alert=True,
        )
        return

    await callback.message.edit_text(
        "🎉 <b>Задание выполнено!</b>\n\n"
        f"🎁 Твоя награда:\n"
        f"<b>{message}</b>",
    )

    await callback.answer(
        "Награда выдана!",
    )
