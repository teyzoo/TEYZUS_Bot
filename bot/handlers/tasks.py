from __future__ import annotations

from aiogram import Router, F
from aiogram.types import CallbackQuery

from database.session import get_session
from database.repositories.tasks import (
    get_active_tasks,
    get_task_by_id,
)
from services.tasks import complete_task

router = Router()


@router.callback_query(F.data == "tasks")
async def tasks_button(
    callback: CallbackQuery,
) -> None:
    await callback.answer()

    if callback.message is None:
        return

    await callback.message.answer(
        "📋 <b>Задания TEYZUS</b>\n\n"
        "Все задания доступны в Mini App.\n"
        "Нажмите кнопку «Задания» в меню Mini App.",
    )


@router.callback_query(
    F.data.startswith("task_complete:")
)
async def complete_task_callback(
    callback: CallbackQuery,
) -> None:
    if callback.message is None:
        return

    try:
        task_id = int(
            callback.data.split(":", 1)[1]
        )
    except (ValueError, AttributeError):
        await callback.answer(
            "Некорректное задание.",
            show_alert=True,
        )
        return

    async with get_session() as session:
        from sqlalchemy import select
        from database.models import User

        result = await session.execute(
            select(User).where(
                User.telegram_id == callback.from_user.id
            )
        )

        user = result.scalar_one_or_none()

        if user is None:
            await callback.answer(
                "Сначала зарегистрируйтесь.",
                show_alert=True,
            )
            return

        task = await get_task_by_id(
            session,
            task_id,
        )

        if task is None:
            await callback.answer(
                "Задание не найдено.",
                show_alert=True,
            )
            return

        success, message = await complete_task(
            session,
            task,
            user,
        )

    await callback.answer(
        message,
        show_alert=not success,
    )
