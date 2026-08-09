from aiogram.fsm.state import (
    State,
    StatesGroup,
)
# =========================================================
# COMMON / HUNTER SEARCH
# =========================================================
class HunterSearchState(StatesGroup):
    length_6 = State()
    length_5 = State()
    expensive = State()
    dictionary = State()
class HunterMaskState(StatesGroup):
    mask = State()
# =========================================================
# PROMO
# =========================================================
class PromoState(StatesGroup):
    code = State()
