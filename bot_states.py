from aiogram.fsm.state import StatesGroup, State


class RegisterStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_email = State()
    waiting_for_password = State()


class LoginStates(StatesGroup):
    waiting_for_email = State()
    waiting_for_password = State()