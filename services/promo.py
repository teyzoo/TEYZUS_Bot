from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    PromoActivation,
    PromoCode,
    User,
)

from database.repositories import (
    activate_promo,
    get_promo_by_code,
)


# =========================================================
# RESULT
# =========================================================

@dataclass(frozen=True)
class PromoResult:

    success: bool

    message: str

    activation: PromoActivation | None = None

    reward_type: str | None = None

    reward_amount: int = 0

    premium_days: int = 0


# =========================================================
# TIME
# =========================================================

def utc_now() -> datetime:

    return datetime.now(
        timezone.utc
    )


# =========================================================
# SERVICE
# =========================================================

class PromoService:

    # =====================================================
    # ACTIVATE
    # =====================================================

    async def activate(
        self,
        session: AsyncSession,
        user: User,
        code: str,
    ) -> PromoResult:

        code = code.strip().upper()

        if not code:

            return PromoResult(
                success=False,
                message=(
                    "❌ <b>Промокод не введён.</b>\n\n"
                    "Введите промокод ещё раз."
                ),
            )

        # -------------------------------------------------
        # FIND
        # -------------------------------------------------

        promo = await get_promo_by_code(
            session=session,
            code=code,
        )

        if promo is None:

            return PromoResult(
                success=False,
                message=(
                    "❌ <b>Промокод не найден.</b>\n\n"
                    "Проверь правильность написания "
                    "и попробуй ещё раз."
                ),
            )

        # -------------------------------------------------
        # VALIDATE
        # -------------------------------------------------

        error = self.validate_promo(
            promo=promo,
            user=user,
        )

        if error is not None:

            return PromoResult(
                success=False,
                message=error,
            )

        # -------------------------------------------------
        # ACTIVATE
        # -------------------------------------------------

        try:

            activation = await activate_promo(
                session=session,
                promo=promo,
                user=user,
            )

        except ValueError as error:

            return PromoResult(
                success=False,
                message=(
                    f"❌ <b>{error}</b>"
                ),
            )

        # -------------------------------------------------
        # SUCCESS
        # -------------------------------------------------

        return PromoResult(
            success=True,
            message=self.build_success_message(
                promo=promo,
                activation=activation,
            ),
            activation=activation,
            reward_type=promo.reward_type,
            reward_amount=promo.reward_amount,
            premium_days=promo.premium_days,
        )

    # =====================================================
    # VALIDATE
    # =====================================================

    def validate_promo(
        self,
        promo: PromoCode,
        user: User,
    ) -> str | None:

        now = utc_now()

        # -------------------------------------------------
        # ACTIVE
        # -------------------------------------------------

        if not promo.is_active:

            return (
                "❌ <b>Промокод отключён.</b>"
            )

        # -------------------------------------------------
        # START
        # -------------------------------------------------

        if promo.starts_at is not None:

            starts_at = promo.starts_at

            if starts_at.tzinfo is None:

                starts_at = starts_at.replace(
                    tzinfo=timezone.utc
                )

            if now < starts_at:

                return (
                    "⏳ <b>Промокод ещё не активен.</b>\n\n"
                    "Попробуй использовать его позже."
                )

        # -------------------------------------------------
        # EXPIRES
        # -------------------------------------------------

        if promo.expires_at is not None:

            expires_at = promo.expires_at

            if expires_at.tzinfo is None:

                expires_at = expires_at.replace(
                    tzinfo=timezone.utc
                )

            if now > expires_at:

                return (
                    "⌛ <b>Срок действия промокода истёк.</b>"
                )

        # -------------------------------------------------
        # GLOBAL LIMIT
        # -------------------------------------------------

        if promo.max_activations is not None:

            if (
                promo.activations_count
                >= promo.max_activations
            ):

                return (
                    "🚫 <b>Лимит активаций исчерпан.</b>"
                )

        # -------------------------------------------------
        # PREMIUM
        # -------------------------------------------------

        if promo.only_premium:

            if not self.user_has_active_premium(
                user
            ):

                return (
                    "💎 <b>Промокод только для Premium.</b>\n\n"
                    "Активируй TEYZUS Premium."
                )

        # -------------------------------------------------
        # NEW USERS
        # -------------------------------------------------

        if promo.only_new_users:

            if user.created_at is None:

                return (
                    "❌ Не удалось определить "
                    "дату регистрации."
                )

        # -------------------------------------------------
        # ALLOWED USERS
        # -------------------------------------------------

        if promo.allowed_user_ids:

            allowed_ids = self.parse_user_ids(
                promo.allowed_user_ids
            )

            if user.telegram_id not in allowed_ids:

                return (
                    "🔒 <b>Этот промокод недоступен тебе.</b>"
                )

        # -------------------------------------------------
        # REWARD
        # -------------------------------------------------

        if promo.reward_type == "premium":

            if promo.premium_days <= 0:

                return (
                    "❌ Промокод настроен некорректно."
                )

        elif promo.reward_type in {
            "stars",
            "balance_rub",
            "searches",
            "traps",
        }:

            if promo.reward_amount <= 0:

                return (
                    "❌ Промокод настроен некорректно."
                )

        else:

            return (
                "❌ Неизвестный тип награды."
            )

        return None

    # =====================================================
    # PREMIUM CHECK
    # =====================================================

    @staticmethod
    def user_has_active_premium(
        user: User,
    ) -> bool:

        if not user.premium_active:

            return False

        if user.premium_until is None:

            return True

        premium_until = (
            user.premium_until
        )

        if premium_until.tzinfo is None:

            premium_until = (
                premium_until.replace(
                    tzinfo=timezone.utc
                )
            )

        return premium_until > utc_now()

    # =====================================================
    # IDS
    # =====================================================

    @staticmethod
    def parse_user_ids(
        value: str,
    ) -> set[int]:

        result: set[int] = set()

        for item in value.split(","):

            item = item.strip()

            if not item:
                continue

            try:

                result.add(
                    int(item)
                )

            except ValueError:

                continue

        return result

    # =====================================================
    # SUCCESS MESSAGE
    # =====================================================

    @staticmethod
    def build_success_message(
        promo: PromoCode,
        activation: PromoActivation,
    ) -> str:

        reward_type = promo.reward_type

        if reward_type == "premium":

            return (
                "🎉 <b>Промокод активирован!</b>\n\n"
                f"🎟 Код: <code>{promo.code}</code>\n"
                "💎 Награда: "
                "<b>TEYZUS Premium</b>\n"
                f"⏳ Срок: "
                f"<b>{promo.premium_days} дн.</b>\n\n"
                "✨ Premium добавлен "
                "на твой аккаунт."
            )

        if reward_type == "stars":

            return (
                "🎉 <b>Промокод активирован!</b>\n\n"
                f"🎟 Код: <code>{promo.code}</code>\n"
                f"⭐ Награда: "
                f"<b>+{promo.reward_amount} Stars</b>\n\n"
                "Баланс Stars пополнен."
            )

        if reward_type == "balance_rub":

            return (
                "🎉 <b>Промокод активирован!</b>\n\n"
                f"🎟 Код: <code>{promo.code}</code>\n"
                f"💰 Награда: "
                f"<b>+{promo.reward_amount} ₽</b>\n\n"
                "Баланс пополнен."
            )

        if reward_type == "searches":

            return (
                "🎉 <b>Промокод активирован!</b>\n\n"
                f"🎟 Код: <code>{promo.code}</code>\n"
                f"🔎 Награда: "
                f"<b>+{promo.reward_amount} поисков</b>\n\n"
                "Дополнительные поиски добавлены."
            )

        if reward_type == "traps":

            return (
                "🎉 <b>Промокод активирован!</b>\n\n"
                f"🎟 Код: <code>{promo.code}</code>\n"
                f"🚨 Награда: "
                f"<b>+{promo.reward_amount} ловушек</b>\n\n"
                "Ловушки добавлены."
            )

        return (
            "🎉 <b>Промокод успешно активирован!</b>"
        )


# =========================================================
# SINGLETON
# =========================================================

promo_service = PromoService()
