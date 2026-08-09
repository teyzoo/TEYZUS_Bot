from aiogram.fsm.state import State, StatesGroup


# =========================================================
# 🎟 PROMO
# =========================================================

class PromoState(StatesGroup):
    """
    Состояния пользовательской активации промокода.
    """

    code = State()


# =========================================================
# 🔎 HUNTER SEARCH
# =========================================================

class HunterSearchState(StatesGroup):
    """
    Состояния основных режимов Hunter.
    """

    # 🔎 Обычный поиск 6 символов
    length_6 = State()

    # 💎 Поиск дорогих username
    expensive = State()

    # 📖 Dictionary Search
    dictionary = State()

    # 💎 Premium поиск 5 символов
    length_5 = State()


# =========================================================
# 🎯 HUNTER MASK
# =========================================================

class HunterMaskState(StatesGroup):
    """
    Состояния поиска username по маске.
    """

    mask = State()
