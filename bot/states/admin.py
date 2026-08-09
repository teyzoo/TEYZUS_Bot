from aiogram.fsm.state import (
    State,
    StatesGroup,
)
# =========================================================
# 👑 OWNER PROMO CREATION
# =========================================================
class OwnerPromoState(StatesGroup):
    # Код промокода
    code = State()
    # Тип награды
    reward_type = State()
    # Количество награды
    reward_amount = State()
    # Premium дни
    premium_days = State()
    # Общий лимит
    max_activations = State()
    # Лимит одного пользователя
    max_activations_per_user = State()
    # Дата начала
    starts_at = State()
    # Дата окончания
    expires_at = State()
    # Только новые пользователи
    only_new_users = State()
    # Только Premium
    only_premium = State()
    # Список Telegram ID
    allowed_user_ids = State()
    # Подтверждение
    confirmation = State()
