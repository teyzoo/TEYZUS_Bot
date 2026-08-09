from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
)

from sqlalchemy import select

from database.models import (
    Case,
    CaseReward,
)
from database.session import (
    get_session,
)
from bot.keyboards.cases import (
    cases_keyboard,
    case_open_keyboard,
)
from services.cases import (
    get_case,
    get_case_rewards,
    open_case,
)


router = Router()


# =========================================================
# CASES MENU
# =========================================================

@router.message(
    F.text == "🎁 Кейсы"
)
async def cases_command(
    message: Message,
):

    async with get_session() as session:

        result = await session.execute(
            select(Case)
            .where(
                Case.is_active.is_(True)
            )
            .order_by(
                Case.sort_order.asc(),
                Case.id.asc(),
            )
        )

        cases = list(
            result.scalars().all()
        )

    if not cases:

        await message.answer(
            "🎁 <b>Кейсы</b>\n\n"
            "Сейчас доступных кейсов нет."
        )

        return

    text = (
        "🎁 <b>TEYZUS CASES</b>\n\n"
        "Открывай кейсы и получай "
        "случайные награды.\n\n"
        "Выбери кейс:"
    )

    await message.answer(
        text,
        reply_markup=cases_keyboard(
            cases
        ),
    )


# =========================================================
# CASE CALLBACK
# =========================================================

@router.callback_query(
    F.data.startswith("case:")
)
async def case_details(
    callback: CallbackQuery,
):

    case_id = int(
        callback.data.split(":")[1]
    )

    async with get_session() as session:

        case = await get_case(
            session,
            case_id,
        )

        if case is None:

            await callback.answer(
                "Кейс недоступен.",
                show_alert=True,
            )

            return

        rewards = await get_case_rewards(
            session,
            case.id,
        )

    lines = [
        f"🎁 <b>{case.title}</b>",
        "",
    ]

    if case.description:

        lines.extend(
            [
                case.description,
                "",
            ]
        )

    lines.append(
        f"💰 Цена: "
        f"<b>⭐ {case.price_stars}</b>"
    )

    lines.extend(
        [
            "",
            "🎯 <b>Возможные награды:</b>",
            "",
        ]
    )

    for reward in rewards:

        if reward.reward_type == "premium":

            reward_text = (
                f"{reward.emoji} "
                f"{reward.title} "
                f"— {reward.premium_days} д."
            )

        else:

            reward_text = (
                f"{reward.emoji} "
                f"{reward.title}"
            )

        lines.append(
            f"{reward_text} "
            f"— {reward.chance:g}%"
        )

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=case_open_keyboard(
            case.id
        ),
    )

    await callback.answer()


# =========================================================
# OPEN CASE
# =========================================================

@router.callback_query(
    F.data.startswith("case_open:")
)
async def case_open_callback(
    callback: CallbackQuery,
):

    case_id = int(
        callback.data.split(":")[1]
    )

    async with get_session() as session:

        result = await session.execute(
            select(Case)
            .where(
                Case.id == case_id,
                Case.is_active.is_(True),
            )
        )

        case = (
            result.scalar_one_or_none()
        )

        if case is None:

            await callback.answer(
                "Кейс недоступен.",
                show_alert=True,
            )

            return

        user_result = await session.execute(
            select(__import__(
                "database.models",
                fromlist=["User"]
            ).User).where(
                __import__(
                    "database.models",
                    fromlist=["User"]
                ).User.telegram_id
                == callback.from_user.id
            )
        )

        user = (
            user_result.scalar_one_or_none()
        )

        if user is None:

            await callback.answer(
                "Сначала зарегистрируйтесь.",
                show_alert=True,
            )

            return

        try:

            opened = await open_case(
                session,
                user,
                case_id,
            )

        except ValueError as error:

            await callback.answer(
                str(error),
                show_alert=True,
            )

            return

    if opened.reward_type == "premium":

        reward_text = (
            f"{opened.reward_title}\n"
            f"💎 Premium на "
            f"{opened.premium_days} дней"
        )

    elif opened.reward_type in (
        "stars",
        "balance",
        "searches",
        "traps",
        "discount",
    ):

        reward_text = (
            f"{opened.reward_title}\n"
            f"🎁 Количество: "
            f"{opened.reward_amount}"
        )

    else:

        reward_text = (
            opened.reward_title
        )

    await callback.message.edit_text(
        "🎉 <b>ПОЗДРАВЛЯЕМ!</b>\n\n"
        "Ты открыл кейс:\n"
        f"🎁 {case.title}\n\n"
        "Твоя награда:\n"
        f"<b>{reward_text}</b>\n\n"
        "Награда автоматически зачислена "
        "на твой аккаунт."
    )

    await callback.answer(
        "🎉 Награда получена!"
    )
