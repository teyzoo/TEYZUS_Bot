from aiogram.fsm.state import State, StatesGroup
class OwnerPromoState(StatesGroup):
    code = State()
    reward_type = State()
    reward_amount = State()
    premium_days = State()
    max_activations = State()
    max_activations_per_user = State()
    starts_at = State()
    expires_at = State()
    only_new_users = State()
    only_premium = State()
    allowed_user_ids = State()
    confirmation = State()
