from __future__ import annotations

from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    Message,
)
from aiogram.utils.keyboard import (
    InlineKeyboardBuilder,
)

from database.session import get_session
from database.models import User

from database.repositories.tasks import (
    get_active_tasks,
    get_user_task_completion_count,
)

from services.tasks import (
    complete_task,
    is_premium_active,
)


router = Router(
    name="tasks"
)


# =========================================================
# TASK TYPE NAMES
# =========================================================

TASK_TYPE_NAMES = {
    "subscribe_channel": "📢 Подписка",
    "referral": "👥 Рефералы",
    "search": "🔎 Поиск",
    "promo": "🎟 Промокод",
    "premium": "💎 Premium",
    "open_miniapp": "📱 Mini App",
    "custom": "⭐ Другое",
}


# =========================================================
# REWARD NAMES
# =========================================================

REWARD_NAMES = {
    "stars": "⭐ Stars",
    "rub": "💰 Баланс",
    "balance": "💰 Баланс",
    "searches": "🔎 Поиски",
    "bonus_searches": "🔎 Поиски",
    "traps": "🎯 Ловушки",
    "bonus_traps": "🎯 Ловушки",
    "discount": "🏷 Скидка",
    "premium": "💎 Premium",
}


# =========================================================
# MAIN TASKS BUTTON
# =========================================================

def tasks_button():
    builder = InlineKeyboardBuilder()

    builder.button(
        text="📋 Задания",
        callback_data="tasks:list",
    )

    builder.adjust(1)

    return builder.as_markup()


# =========================================================
# PERIOD
# =========================================================

def get_period_text(
    task,
) -> str:

    if not task.starts_at or not task.expires_at:
        return "♾ Постоянное"

    seconds = (
        task.expires_at
        - task.starts_at
    ).total_seconds()

    if seconds <= 86400:
        return "📅 Ежедневное"

    if seconds <= 86400 * 7:
        return "📆 Недельное"

    if seconds <= 86400 * 31:
        return "🗓 Месячное"

    return "⏳ Ограниченное"


# =========================================================
# REWARD
# =========================================================

def get_reward_text(
    task,
) -> str:

    reward = task.reward_type.lower()

    name = REWARD_NAMES.get(
        reward,
        "🎁 Награда",
    )

    if reward == "premium":
        amount = (
            task.premium_days
            or task.reward_amount
        )

        return (
            f"{name}: "
            f"{amount} дн."
        )

    return (
        f"{name}: "
        f"+{task.reward_amount}"
    )


# =========================================================
# TASK CARD
# =========================================================

def task_text(
    task,
    completed: int,
) -> str:

    type_name = TASK_TYPE_NAMES.get(
        task.task_type,
        "⭐ Задание",
    )

    period = get_period_text(
        task
    )

    reward = get_reward_text(
        task
    )

    premium_text = ""

    if task.only_premium:
        premium_text = (
            "\n💎 <b>Только Premium</b>"
        )

    description = (
        task.description
        or "Выполни это задание."
    )

    limit_text = ""

    if task.max_completions_per_user:
        limit_text = (
            "\n🔢 Лимит: "
            f"{task.max_completions_per_user}"
        )

    return (
        f"{task.image_file_id or ''}\n"
        f"<b>{task.title}</b>\n\n"
        f"{description}\n\n"
        f"{type_name}\n"
        f"{period}\n"
        f"🎁 {reward}"
        f"{premium_text}"
        f"{limit_text}\n\n"
        f"Выполнено тобой: "
        f"{completed}"
    )


# =========================================================
# TASK LIST
# =========================================================

@router.callback_query(
    F.data == "tasks:list"
)
async def tasks_list(
    callback: CallbackQuery,
):

    await callback.answer()

    user_tg_id = (
        callback.from_user.id
    )

    async with get_session() as session:

        from sqlalchemy import select

        result = await session.execute(
            select(User).where(
                User.telegram_id
                == user_tg_id
            )
        )

        user = (
            result.scalar_one_or_none()
        )

        if user is None:
            await callback.message.answer(
                "❌ Сначала используй /start."
            )
            return

        premium = is_premium_active(
            user
        )

        tasks = await get_active_tasks(
            session,
            premium=premium,
        )

        if not tasks:
            await callback.message.answer(
                "📋 <b>Задания</b>\n\n"
                "Сейчас доступных заданий нет.\n\n"
                "Загляни позже 👀"
            )
            return

        builder = (
            InlineKeyboardBuilder()
        )

        text = (
            "📋 <b>ЗАДАНИЯ TEYZUS</b>\n\n"
        )

        for task in tasks:

            completed = (
                await get_user_task_completion_count(
                    session,
                    user_id=user.id,
                    task_id=task.id,
                )
            )

            text += (
                f"{task.title}\n"
                f"🎁 {get_reward_text(task)}\n"
            )

            if task.only_premium:
                text += "💎 Premium\n"

            if completed:
                text += (
                    f"✅ Выполнено: "
                    f"{completed}\n"
                )

            text += "\n"

            builder.button(
                text=(
                    "💎 "
                    if task.only_premium
                    else "📋 "
                )
                + task.title[:35],
                callback_data=(
                    f"tasks:view:{task.id}"
                ),
            )

        builder.button(
            text="🔄 Обновить",
            callback_data="tasks:list",
        )

        builder.adjust(1)

        await callback.message.answer(
            text,
            reply_markup=builder.as_markup(),
        )


# =========================================================
# VIEW TASK
# =========================================================

@router.callback_query(
    F.data.startswith("tasks:view:")
)
async def tasks_view(
    callback: CallbackQuery,
):

    await callback.answer()

    try:
        task_id = int(
            callback.data.split(":")[-1]
        )
    except (
        ValueError,
        AttributeError,
    ):
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
            await callback.message.answer(
                "❌ Пользователь не найден."
            )
            return

        from database.repositories.tasks import (
            get_task,
        )

        task = await get_task(
            session,
            task_id,
        )

        if task is None:
            await callback.message.answer(
                "❌ Задание не найдено."
            )
            return

        completed = (
            await get_user_task_completion_count(
                session,
                user_id=user.id,
                task_id=task.id,
            )
        )

        builder = (
            InlineKeyboardBuilder()
        )

        # -------------------------------------------------
        # ACTION
        # -------------------------------------------------

        if task.task_type == "subscribe_channel":
            button_text = (
                "📢 Подписаться"
            )

        elif task.task_type == "open_miniapp":
            button_text = (
                "📱 Открыть Mini App"
            )

        elif task.task_type == "search":
            button_text = (
                "🔎 Выполнить поиск"
            )

        elif task.task_type == "referral":
            button_text = (
                "👥 Пригласить"
            )

        elif task.task_type == "promo":
            button_text = (
                "🎟 Активировать"
            )

        else:
            button_text = (
                "✅ Выполнить"
            )

        builder.button(
            text=button_text,
            callback_data=(
                f"tasks:do:{task.id}"
            ),
        )

        builder.button(
            text="⬅️ Назад",
            callback_data="tasks:list",
        )

        builder.adjust(1)

        await callback.message.answer(
            task_text(
                task,
                completed,
            ),
            reply_markup=(
                builder.as_markup()
            ),
        )


# =========================================================
# DO TASK
# =========================================================

@router.callback_query(
    F.data.startswith("tasks:do:")
)
async def tasks_do(
    callback: CallbackQuery,
):

    await callback.answer()

    try:
        task_id = int(
            callback.data.split(":")[-1]
        )
    except (
        ValueError,
        AttributeError,
    ):
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
            await callback.message.answer(
                "❌ Пользователь не найден."
            )
            return

        from database.repositories.tasks import (
            get_task,
        )

        task = await get_task(
            session,
            task_id,
        )

        if task is None:
            await callback.message.answer(
                "❌ Задание не найдено."
            )
            return

        # -------------------------------------------------
        # SEARCH
        # -------------------------------------------------

        if task.task_type == "search":

            await callback.message.answer(
                "🔎 <b>Задание на поиск</b>\n\n"
                "Выполни поиск username через "
                "кнопку «Поиск».\n\n"
                "После успешного поиска задание "
                "можно будет подтвердить."
            )

            return

        # -------------------------------------------------
        # SUBSCRIBE
        # -------------------------------------------------

        if task.task_type == "subscribe_channel":

            await callback.message.answer(
                "📢 Сначала подпишись на канал:\n\n"
                f"{task.target_value or 'Канал не указан'}\n\n"
                "После подписки нажми кнопку "
                "проверки ещё раз."
            )

            return

        # -------------------------------------------------
        # REFERRAL
        # -------------------------------------------------

        if task.task_type == "referral":

            await callback.message.answer(
                "👥 Для выполнения задания "
                "пригласи нужное количество "
                "пользователей по своей "
                "реферальной ссылке."
            )

            return

        # -------------------------------------------------
        # MINI APP
        # -------------------------------------------------

        if task.task_type == "open_miniapp":

            result = await complete_task(
                session,
                task_id=task.id,
                user=user,
            )

            await callback.message.answer(
                result.message
            )

            return

        # -------------------------------------------------
        # CUSTOM
        # -------------------------------------------------

        result = await complete_task(
            session,
            task_id=task.id,
            user=user,
        )

        await callback.message.answer(
            result.message
        )
