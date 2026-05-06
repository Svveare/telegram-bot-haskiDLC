from aiogram.fsm.state import StatesGroup, State


class SupportRequest(StatesGroup):
    text = State()
