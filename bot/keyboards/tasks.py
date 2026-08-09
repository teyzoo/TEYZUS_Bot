from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def task_admin_menu_keyboard() -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()

    builder.button(
        text="➕ Создать задание",
        callback_data="task:create",
    )

    builder.button(
        text="📋 Все задания",
        callback_data="task:list",
    )

    builder.button(
        text="📊 Статистика",
        callback_data="task:stats",
    )

    builder.adjust(1)

    return builder.as_markup()


def task_type_keyboard() -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()

    builder.button(
        text="📢 Подписка",
        callback_data="task_type:subscribe_channel",
    )

    builder.button(
        text="🔎 Поиск",
        callback_data="task_type:search",
    )

    builder.button(
        text="👥 Рефералы",
        callback_data="task_type:referral",
    )

    builder.button(
        text="🎟 Промокод",
        callback_data="task_type:promo",
    )

    builder.button(
        text="💎 Premium",
        callback_data="task_type:premium",
    )

    builder.button(
        text="📱 Открыть Mini App",
        callback_data="task_type:open_miniapp",
    )

    builder.button(
        text="🛠 Другое",
        callback_data="task_type:custom",
    )

    builder.adjust(2)

    return builder.as_markup()


def reward_type_keyboard() -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()

    builder.button(
        text="💰 Баланс ₽",
        callback_data="reward_type:balance",
    )

    builder.button(
        text="⭐ Stars",
        callback_data="reward_type:stars",
    )

    builder.button(
        text="🔎 Поиски",
        callback_data="reward_type:searches",
    )

    builder.button(
        text="🎯 Ловушки",
        callback_data="reward_type:traps",
    )

    builder.button(
        text="🏷 Скидка %",
        callback_data="reward_type:discount",
    )

    builder.button(
        text="💎 Premium",
        callback_data="reward_type:premium",
    )

    builder.adjust(2)

    return builder.as_markup()


def task_period_keyboard() -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()

    builder.button(
        text="📅 Ежедневное",
        callback_data="task_period:daily",
    )

    builder.button(
        text="📆 Еженедельное",
        callback_data="task_period:weekly",
    )

    builder.button(
        text="🗓 Ежемесячное",
        callback_data="task_period:monthly",
    )

    builder.button(
        text="♾ Без периода",
        callback_data="task_period:permanent",
    )

    builder.adjust(2)

    return builder.as_markup()


def yes_no_keyboard(
    yes_callback: str,
    no_callback: str,
) -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()

    builder.button(
        text="✅ Да",
        callback_data=yes_callback,
    )

    builder.button(
        text="❌ Нет",
        callback_data=no_callback,
    )

    builder.adjust(2)

    return builder.as_markup()
