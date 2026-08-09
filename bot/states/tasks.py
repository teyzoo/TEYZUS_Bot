from aiogram.fsm.state import State, StatesGroup


class CreateTaskState(StatesGroup):
    title = State()
    description = State()
    task_type = State()
    target_value = State()
    reward_type = State()
    reward_amount = State()
    premium_days = State()
    period = State()
    duration = State()
    max_completions = State()
    max_completions_per_user = State()
    only_premium = State()
    repeatable = State()
    sort_order = State()
    image_file_id = State()
