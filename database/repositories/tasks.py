from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    Task,
    TaskCompletion,
    User,
)


# =========================================================
# TIME
# =========================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# =========================================================
# GET TASK
# =========================================================

async def get_task(
    session: AsyncSession,
    task_id: int,
) -> Task | None:

    result = await session.execute(
        select(Task).where(
            Task.id == task_id
        )
    )

    return result.scalar_one_or_none()


# =========================================================
# GET ACTIVE TASKS
# =========================================================

async def list_active_tasks(
    session: AsyncSession,
) -> list[Task]:

    now = utc_now()

    result = await session.execute(
        select(Task)
        .where(
            Task.is_active.is_(True),
        )
        .where(
            (
                Task.starts_at.is_(None)
                | (Task.starts_at <= now)
            )
        )
        .where(
            (
                Task.expires_at.is_(None)
                | (Task.expires_at >= now)
            )
        )
        .order_by(
            Task.sort_order.asc(),
            Task.id.asc(),
        )
    )

    return list(
        result.scalars().all()
    )


# =========================================================
# GET ALL TASKS
# =========================================================

async def list_tasks(
    session: AsyncSession,
) -> list[Task]:

    result = await session.execute(
        select(Task)
        .order_by(
            Task.sort_order.asc(),
            Task.id.asc(),
        )
    )

    return list(
        result.scalars().all()
    )


# =========================================================
# CREATE TASK
# =========================================================

async def create_task(
    session: AsyncSession,
    *,
    title: str,
    description: str | None,
    task_type: str,
    target_value: str | None,
    reward_type: str,
    reward_amount: int = 0,
    premium_days: int = 0,
    max_completions: int | None = None,
    only_new_users: bool = False,
    only_premium: bool = False,
    starts_at: datetime | None = None,
    expires_at: datetime | None = None,
    repeatable: bool = False,
    max_completions_per_user: int | None = 1,
    sort_order: int = 0,
    image_file_id: str | None = None,
    created_by: int = 0,
) -> Task:

    title = title.strip()

    if not title:
        raise ValueError(
            "Название задания не может быть пустым."
        )

    if not task_type:
        raise ValueError(
            "Тип задания не указан."
        )

    if not reward_type:
        raise ValueError(
            "Тип награды не указан."
        )

    if reward_amount < 0:
        raise ValueError(
            "Количество награды не может быть отрицательным."
        )

    if premium_days < 0:
        raise ValueError(
            "Количество дней Premium не может быть отрицательным."
        )

    if max_completions is not None:
        if max_completions <= 0:
            raise ValueError(
                "Лимит выполнений должен быть больше 0."
            )

    if (
        max_completions_per_user is not None
        and max_completions_per_user <= 0
    ):
        raise ValueError(
            "Лимит на пользователя должен быть больше 0."
        )

    if (
        starts_at is not None
        and expires_at is not None
        and expires_at <= starts_at
    ):
        raise ValueError(
            "Дата окончания должна быть позже даты начала."
        )

    # -----------------------------------------------------
    # VALIDATE REWARD
    # -----------------------------------------------------

    if reward_type == "premium":

        if premium_days <= 0:
            raise ValueError(
                "Для Premium необходимо указать количество дней."
            )

    elif reward_type in {
        "searches",
        "traps",
        "balance_rub",
        "stars",
        "discount",
    }:

        if reward_amount <= 0:
            raise ValueError(
                "Количество награды должно быть больше 0."
            )

    else:

        raise ValueError(
            f"Неизвестный тип награды: {reward_type}"
        )

    task = Task(
        title=title,
        description=description,
        task_type=task_type,
        target_value=target_value,
        reward_type=reward_type,
        reward_amount=reward_amount,
        premium_days=premium_days,
        max_completions=max_completions,
        completions_count=0,
        only_new_users=only_new_users,
        only_premium=only_premium,
        starts_at=starts_at,
        expires_at=expires_at,
        repeatable=repeatable,
        max_completions_per_user=(
            max_completions_per_user
        ),
        is_active=True,
        sort_order=sort_order,
        image_file_id=image_file_id,
        created_by=created_by,
    )

    session.add(task)

    await session.commit()

    await session.refresh(task)

    return task


# =========================================================
# UPDATE TASK
# =========================================================

async def update_task(
    session: AsyncSession,
    task_id: int,
    **values,
) -> Task | None:

    task = await get_task(
        session=session,
        task_id=task_id,
    )

    if task is None:
        return None

    allowed_fields = {
        "title",
        "description",
        "task_type",
        "target_value",
        "reward_type",
        "reward_amount",
        "premium_days",
        "max_completions",
        "only_new_users",
        "only_premium",
        "starts_at",
        "expires_at",
        "repeatable",
        "max_completions_per_user",
        "is_active",
        "sort_order",
        "image_file_id",
    }

    for key, value in values.items():

        if key not in allowed_fields:
            continue

        if key == "title" and value is not None:
            value = str(value).strip()

            if not value:
                raise ValueError(
                    "Название задания не может быть пустым."
                )

        setattr(
            task,
            key,
            value,
        )

    # -----------------------------------------------------
    # DATE VALIDATION
    # -----------------------------------------------------

    if (
        task.starts_at is not None
        and task.expires_at is not None
        and task.expires_at <= task.starts_at
    ):
        raise ValueError(
            "Дата окончания должна быть позже даты начала."
        )

    # -----------------------------------------------------
    # REWARD VALIDATION
    # -----------------------------------------------------

    if task.reward_type == "premium":

        if task.premium_days <= 0:
            raise ValueError(
                "Количество дней Premium должно быть больше 0."
            )

    elif task.reward_type in {
        "searches",
        "traps",
        "balance_rub",
        "stars",
        "discount",
    }:

        if task.reward_amount <= 0:
            raise ValueError(
                "Количество награды должно быть больше 0."
            )

    else:

        raise ValueError(
            f"Неизвестный тип награды: {task.reward_type}"
        )

    await session.commit()

    await session.refresh(task)

    return task


# =========================================================
# ACTIVATE TASK
# =========================================================

async def activate_task(
    session: AsyncSession,
    task_id: int,
) -> bool:

    task = await get_task(
        session=session,
        task_id=task_id,
    )

    if task is None:
        return False

    task.is_active = True

    await session.commit()

    return True


# =========================================================
# DEACTIVATE TASK
# =========================================================

async def deactivate_task(
    session: AsyncSession,
    task_id: int,
) -> bool:

    task = await get_task(
        session=session,
        task_id=task_id,
    )

    if task is None:
        return False

    task.is_active = False

    await session.commit()

    return True


# =========================================================
# DELETE TASK
# =========================================================

async def delete_task(
    session: AsyncSession,
    task_id: int,
) -> bool:

    task = await get_task(
        session=session,
        task_id=task_id,
    )

    if task is None:
        return False

    await session.delete(task)

    await session.commit()

    return True


# =========================================================
# GET USER COMPLETIONS
# =========================================================

async def get_user_task_completions(
    session: AsyncSession,
    *,
    task_id: int,
    user_id: int,
) -> list[TaskCompletion]:

    result = await session.execute(
        select(TaskCompletion)
        .where(
            TaskCompletion.task_id == task_id
        )
        .where(
            TaskCompletion.user_id == user_id
        )
        .order_by(
            TaskCompletion.completed_at.desc()
        )
    )

    return list(
        result.scalars().all()
    )


# =========================================================
# USER COMPLETION COUNT
# =========================================================

async def get_user_task_completion_count(
    session: AsyncSession,
    *,
    task_id: int,
    user_id: int,
) -> int:

    result = await session.execute(
        select(
            func.count(
                TaskCompletion.id
            )
        )
        .where(
            TaskCompletion.task_id == task_id
        )
        .where(
            TaskCompletion.user_id == user_id
        )
    )

    return int(
        result.scalar_one() or 0
    )


# =========================================================
# HAS USER COMPLETED TASK
# =========================================================

async def has_user_completed_task(
    session: AsyncSession,
    *,
    task_id: int,
    user_id: int,
) -> bool:

    result = await session.execute(
        select(TaskCompletion.id)
        .where(
            TaskCompletion.task_id == task_id
        )
        .where(
            TaskCompletion.user_id == user_id
        )
        .limit(1)
    )

    return result.scalar_one_or_none() is not None


# =========================================================
# CAN USER COMPLETE
# =========================================================

async def can_user_complete_task(
    session: AsyncSession,
    *,
    task: Task,
    user: User,
) -> tuple[bool, str | None]:

    now = utc_now()

    # -----------------------------------------------------
    # ACTIVE
    # -----------------------------------------------------

    if not task.is_active:

        return (
            False,
            "❌ Это задание отключено.",
        )

    # -----------------------------------------------------
    # START DATE
    # -----------------------------------------------------

    if task.starts_at is not None:

        starts_at = task.starts_at

        if starts_at.tzinfo is None:
            starts_at = starts_at.replace(
                tzinfo=timezone.utc
            )

        if now < starts_at:

            return (
                False,
                "⏳ Это задание ещё не началось.",
            )

    # -----------------------------------------------------
    # EXPIRE DATE
    # -----------------------------------------------------

    if task.expires_at is not None:

        expires_at = task.expires_at

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(
                tzinfo=timezone.utc
            )

        if now > expires_at:

            return (
                False,
                "⌛ Срок выполнения задания истёк.",
            )

    # -----------------------------------------------------
    # GLOBAL LIMIT
    # -----------------------------------------------------

    if task.max_completions is not None:

        if (
            task.completions_count
            >= task.max_completions
        ):

            return (
                False,
                "🚫 Лимит выполнений этого задания исчерпан.",
            )

    # -----------------------------------------------------
    # NEW USERS
    # -----------------------------------------------------

    if task.only_new_users:

        if user.created_at is None:

            return (
                False,
                "❌ Не удалось определить дату регистрации.",
            )

    # -----------------------------------------------------
    # PREMIUM
    # -----------------------------------------------------

    if task.only_premium:

        if not user.premium_active:

            return (
                False,
                "💎 Это задание доступно только Premium пользователям.",
            )

        if user.premium_until is not None:

            premium_until = user.premium_until

            if premium_until.tzinfo is None:

                premium_until = premium_until.replace(
                    tzinfo=timezone.utc
                )

            if premium_until <= now:

                return (
                    False,
                    "💎 Это задание доступно только активным Premium пользователям.",
                )

    # -----------------------------------------------------
    # USER LIMIT
    # -----------------------------------------------------

    count = await get_user_task_completion_count(
        session=session,
        task_id=task.id,
        user_id=user.id,
    )

    if task.max_completions_per_user is not None:

        if (
            count
            >= task.max_completions_per_user
        ):

            return (
                False,
                "✅ Ты уже выполнил это задание максимальное количество раз.",
            )

    # -----------------------------------------------------
    # REPEATABLE
    # -----------------------------------------------------

    if not task.repeatable and count > 0:

        return (
            False,
            "✅ Ты уже выполнил это задание.",
        )

    return (
        True,
        None,
    )


# =========================================================
# COMPLETE TASK
# =========================================================

async def complete_task(
    session: AsyncSession,
    *,
    task: Task,
    user: User,
) -> TaskCompletion:

    # -----------------------------------------------------
    # CHECK
    # -----------------------------------------------------

    allowed, error = await can_user_complete_task(
        session=session,
        task=task,
        user=user,
    )

    if not allowed:

        raise ValueError(
            error
            or "Задание нельзя выполнить."
        )

    # -----------------------------------------------------
    # CREATE COMPLETION
    # -----------------------------------------------------

    completion = TaskCompletion(
        task_id=task.id,
        user_id=user.id,
        telegram_id=user.telegram_id,
        reward_type=task.reward_type,
        reward_amount=task.reward_amount,
        premium_days=task.premium_days,
    )

    session.add(completion)

    # -----------------------------------------------------
    # UPDATE COUNTER
    # -----------------------------------------------------

    task.completions_count += 1

    await session.commit()

    await session.refresh(
        completion
    )

    return completion


# =========================================================
# TASK STATISTICS
# =========================================================

async def get_task_statistics(
    session: AsyncSession,
    task_id: int,
) -> dict:

    task = await get_task(
        session=session,
        task_id=task_id,
    )

    if task is None:
        return {}

    total_result = await session.execute(
        select(
            func.count(
                TaskCompletion.id
            )
        )
        .where(
            TaskCompletion.task_id == task_id
        )
    )

    total_completions = int(
        total_result.scalar_one() or 0
    )

    unique_result = await session.execute(
        select(
            func.count(
                func.distinct(
                    TaskCompletion.user_id
                )
            )
        )
        .where(
            TaskCompletion.task_id == task_id
        )
    )

    unique_users = int(
        unique_result.scalar_one() or 0
    )

    return {
        "task_id": task.id,
        "title": task.title,
        "is_active": task.is_active,
        "total_completions": total_completions,
        "unique_users": unique_users,
        "max_completions": task.max_completions,
        "reward_type": task.reward_type,
        "reward_amount": task.reward_amount,
        "premium_days": task.premium_days,
    }


# =========================================================
# GLOBAL TASK STATISTICS
# =========================================================

async def get_tasks_statistics(
    session: AsyncSession,
) -> dict:

    tasks_result = await session.execute(
        select(
            func.count(Task.id)
        )
    )

    total_tasks = int(
        tasks_result.scalar_one() or 0
    )

    active_result = await session.execute(
        select(
            func.count(Task.id)
        )
        .where(
            Task.is_active.is_(True)
        )
    )

    active_tasks = int(
        active_result.scalar_one() or 0
    )

    completions_result = await session.execute(
        select(
            func.count(
                TaskCompletion.id
            )
        )
    )

    total_completions = int(
        completions_result.scalar_one() or 0
    )

    users_result = await session.execute(
        select(
            func.count(
                func.distinct(
                    TaskCompletion.user_id
                )
            )
        )
    )

    unique_users = int(
        users_result.scalar_one() or 0
    )

    return {
        "total_tasks": total_tasks,
        "active_tasks": active_tasks,
        "total_completions": total_completions,
        "unique_users": unique_users,
    }


# =========================================================
# RECENT COMPLETIONS
# =========================================================

async def get_recent_task_completions(
    session: AsyncSession,
    *,
    task_id: int | None = None,
    limit: int = 50,
) -> list[TaskCompletion]:

    limit = max(
        1,
        min(
            limit,
            500,
        ),
    )

    query = (
        select(TaskCompletion)
        .order_by(
            TaskCompletion.completed_at.desc()
        )
        .limit(limit)
    )

    if task_id is not None:

        query = query.where(
            TaskCompletion.task_id == task_id
        )

    result = await session.execute(
        query
    )

    return list(
        result.scalars().all()
    )


# =========================================================
# DELETE USER COMPLETIONS
# =========================================================

async def delete_user_task_completions(
    session: AsyncSession,
    *,
    task_id: int,
    user_id: int,
) -> int:

    result = await session.execute(
        delete(TaskCompletion)
        .where(
            TaskCompletion.task_id == task_id
        )
        .where(
            TaskCompletion.user_id == user_id
        )
    )

    await session.commit()

    return int(
        result.rowcount or 0
    )
