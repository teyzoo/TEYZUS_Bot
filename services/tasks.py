from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Task, TaskCompletion, User
from database.repositories.tasks import complete_task


# =========================================================
# CONSTANTS
# =========================================================

REWARD_NAMES = {
    "premium": "💎 Premium",
    "stars": "⭐ Stars",
    "balance_rub": "💰 Рубли",
    "searches": "🔎 Дополнительные поиски",
    "traps": "🚨 Дополнительные ловушки",
    "discount": "🏷 Скидка",
}


TASK_TYPE_NAMES = {
    "subscribe_channel": "📢 Подписаться на канал",
    "subscribe_channels": "📢 Подписаться на каналы",
    "referral": "👥 Пригласить пользователя",
    "search": "🔎 Выполнить поиск",
    "username_search": "🔎 Найти username",
    "promo": "🎟 Активировать промокод",
    "premium": "💎 Оформить Premium",
    "open_miniapp": "📱 Открыть Mini App",
    "daily": "📅 Ежедневное задание",
    "custom": "🎯 Задание",
}


# =========================================================
# TIME
# =========================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# =========================================================
# RESULT
# =========================================================

@dataclass(frozen=True)
class TaskResult:

    success: bool

    message: str

    completion: TaskCompletion | None = None

    reward_type: str | None = None

    reward_amount: int = 0

    premium_days: int = 0


# =========================================================
# TASK SERVICE
# =========================================================

class TaskService:

    # =====================================================
    # COMPLETE TASK
    # =====================================================

    async def complete(
        self,
        session: AsyncSession,
        user: User,
        task: Task,
    ) -> TaskResult:

        # -------------------------------------------------
        # COMPLETE
        # -------------------------------------------------

        try:

            completion = await complete_task(
                session=session,
                task=task,
                user=user,
            )

        except ValueError as error:

            return TaskResult(
                success=False,
                message=f"❌ <b>{error}</b>",
            )

        # -------------------------------------------------
        # GIVE REWARD
        # -------------------------------------------------

        try:

            self.apply_reward(
                user=user,
                reward_type=task.reward_type,
                reward_amount=task.reward_amount,
                premium_days=task.premium_days,
            )

            await session.commit()

        except Exception:

            await session.rollback()

            return TaskResult(
                success=False,
                message=(
                    "❌ <b>Не удалось выдать награду.</b>\n\n"
                    "Попробуй выполнить задание ещё раз."
                ),
            )

        # -------------------------------------------------
        # SUCCESS MESSAGE
        # -------------------------------------------------

        message = self.build_success_message(
            task=task,
        )

        return TaskResult(
            success=True,
            message=message,
            completion=completion,
            reward_type=task.reward_type,
            reward_amount=task.reward_amount,
            premium_days=task.premium_days,
        )

    # =====================================================
    # APPLY REWARD
    # =====================================================

    @staticmethod
    def apply_reward(
        user: User,
        reward_type: str,
        reward_amount: int,
        premium_days: int,
    ) -> None:

        # -------------------------------------------------
        # PREMIUM
        # -------------------------------------------------

        if reward_type == "premium":

            if premium_days <= 0:

                raise ValueError(
                    "Некорректное количество дней Premium."
                )

            now = utc_now()

            current_until = user.premium_until

            if current_until is not None:

                if current_until.tzinfo is None:

                    current_until = current_until.replace(
                        tzinfo=timezone.utc
                    )

            # Если Premium уже активен,
            # добавляем дни к существующему сроку.
            if (
                user.premium_active
                and current_until is not None
                and current_until > now
            ):

                new_until = (
                    current_until
                    + timedelta(
                        days=premium_days
                    )
                )

            else:

                new_until = (
                    now
                    + timedelta(
                        days=premium_days
                    )
                )

            user.premium_active = True

            user.premium_until = new_until

            return

        # -------------------------------------------------
        # STARS
        # -------------------------------------------------

        if reward_type == "stars":

            if reward_amount <= 0:

                raise ValueError(
                    "Некорректное количество Stars."
                )

            user.stars_balance += reward_amount

            return

        # -------------------------------------------------
        # RUB
        # -------------------------------------------------

        if reward_type == "balance_rub":

            if reward_amount <= 0:

                raise ValueError(
                    "Некорректная сумма."
                )

            user.balance_rub += reward_amount

            return

        # -------------------------------------------------
        # SEARCHES
        # -------------------------------------------------

        if reward_type == "searches":

            if reward_amount <= 0:

                raise ValueError(
                    "Некорректное количество поисков."
                )

            # Дополнительные поиски храним
            # в отдельном поле, если оно есть.
            if hasattr(
                user,
                "bonus_searches",
            ):

                user.bonus_searches += reward_amount

            else:

                raise ValueError(
                    "В модели User отсутствует "
                    "поле bonus_searches."
                )

            return

        # -------------------------------------------------
        # TRAPS
        # -------------------------------------------------

        if reward_type == "traps":

            if reward_amount <= 0:

                raise ValueError(
                    "Некорректное количество ловушек."
                )

            if hasattr(
                user,
                "bonus_traps",
            ):

                user.bonus_traps += reward_amount

            else:

                raise ValueError(
                    "В модели User отсутствует "
                    "поле bonus_traps."
                )

            return

        # -------------------------------------------------
        # DISCOUNT
        # -------------------------------------------------

        if reward_type == "discount":

            if reward_amount <= 0:

                raise ValueError(
                    "Некорректный размер скидки."
                )

            if hasattr(
                user,
                "discount_percent",
            ):

                current = (
                    user.discount_percent
                    or 0
                )

                user.discount_percent = min(
                    100,
                    current + reward_amount,
                )

            else:

                raise ValueError(
                    "В модели User отсутствует "
                    "поле discount_percent."
                )

            return

        # -------------------------------------------------
        # UNKNOWN
        # -------------------------------------------------

        raise ValueError(
            f"Неизвестный тип награды: {reward_type}"
        )

    # =====================================================
    # BUILD SUCCESS MESSAGE
    # =====================================================

    @staticmethod
    def build_success_message(
        task: Task,
    ) -> str:

        reward_type = task.reward_type

        # -------------------------------------------------
        # PREMIUM
        # -------------------------------------------------

        if reward_type == "premium":

            return (
                "🎉 <b>Задание выполнено!</b>\n\n"
                f"🎯 {task.title}\n\n"
                "🎁 Награда:\n"
                f"💎 <b>TEYZUS Premium "
                f"на {task.premium_days} дн.</b>\n\n"
                "✅ Premium автоматически "
                "добавлен к твоему аккаунту."
            )

        # -------------------------------------------------
        # STARS
        # -------------------------------------------------

        if reward_type == "stars":

            return (
                "🎉 <b>Задание выполнено!</b>\n\n"
                f"🎯 {task.title}\n\n"
                "🎁 Награда:\n"
                f"⭐ <b>+{task.reward_amount} Stars</b>\n\n"
                "Баланс Stars пополнен автоматически."
            )

        # -------------------------------------------------
        # RUB
        # -------------------------------------------------

        if reward_type == "balance_rub":

            return (
                "🎉 <b>Задание выполнено!</b>\n\n"
                f"🎯 {task.title}\n\n"
                "🎁 Награда:\n"
                f"💰 <b>+{task.reward_amount} ₽</b>\n\n"
                "Баланс пополнен автоматически."
            )

        # -------------------------------------------------
        # SEARCHES
        # -------------------------------------------------

        if reward_type == "searches":

            return (
                "🎉 <b>Задание выполнено!</b>\n\n"
                f"🎯 {task.title}\n\n"
                "🎁 Награда:\n"
                f"🔎 <b>+{task.reward_amount} поисков</b>\n\n"
                "Дополнительные поиски добавлены."
            )

        # -------------------------------------------------
        # TRAPS
        # -------------------------------------------------

        if reward_type == "traps":

            return (
                "🎉 <b>Задание выполнено!</b>\n\n"
                f"🎯 {task.title}\n\n"
                "🎁 Награда:\n"
                f"🚨 <b>+{task.reward_amount} ловушек</b>\n\n"
                "Дополнительные ловушки добавлены."
            )

        # -------------------------------------------------
        # DISCOUNT
        # -------------------------------------------------

        if reward_type == "discount":

            return (
                "🎉 <b>Задание выполнено!</b>\n\n"
                f"🎯 {task.title}\n\n"
                "🎁 Награда:\n"
                f"🏷 <b>Скидка {task.reward_amount}%</b>\n\n"
                "Скидка добавлена к твоему аккаунту."
            )

        return (
            "🎉 <b>Задание выполнено!</b>\n\n"
            "🎁 Награда успешно выдана."
        )

    # =====================================================
    # TASK INFO
    # =====================================================

    @staticmethod
    def build_task_text(
        task: Task,
        completion_count: int = 0,
    ) -> str:

        task_type = TASK_TYPE_NAMES.get(
            task.task_type,
            task.task_type,
        )

        reward_name = REWARD_NAMES.get(
            task.reward_type,
            task.reward_type,
        )

        # -------------------------------------------------
        # REWARD TEXT
        # -------------------------------------------------

        if task.reward_type == "premium":

            reward_text = (
                f"{reward_name} "
                f"— {task.premium_days} дн."
            )

        elif task.reward_type == "discount":

            reward_text = (
                f"{reward_name} "
                f"— {task.reward_amount}%"
            )

        else:

            reward_text = (
                f"{reward_name} "
                f"— {task.reward_amount}"
            )

        # -------------------------------------------------
        # LIMIT
        # -------------------------------------------------

        if task.max_completions_per_user is None:

            user_limit = "∞"

        else:

            user_limit = str(
                task.max_completions_per_user
            )

        # -------------------------------------------------
        # DESCRIPTION
        # -------------------------------------------------

        description = (
            task.description
            if task.description
            else "Выполни это задание и получи награду."
        )

        return (
            f"🎯 <b>{task.title}</b>\n\n"
            f"{description}\n\n"
            f"📌 Тип: <b>{task_type}</b>\n"
            f"🎁 Награда: <b>{reward_text}</b>\n"
            f"🔄 Выполнено тобой: "
            f"<b>{completion_count}/{user_limit}</b>"
        )


# =========================================================
# SINGLETON
# =========================================================

task_service = TaskService()
