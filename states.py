from aiogram.fsm.state import State, StatesGroup


class Form(StatesGroup):
    waiting_expense = State()
    waiting_income = State()

    waiting_debt_name = State()
    waiting_debt_amount = State()
    waiting_debt_date = State()

    waiting_broadcast_message = State()
