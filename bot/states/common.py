from aiogram.fsm.state import (
    State,
    StatesGroup,
)


class PromoState(StatesGroup):

    code = State()


class HunterSearchState(StatesGroup):

    length_5 = State()
    length_6 = State()
    expensive = State()
    dictionary = State()


class HunterMaskState(StatesGroup):

    mask = State()
