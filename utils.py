from aiogram.dispatcher.filters.state import StatesGroup, State


class TransferState(StatesGroup):
    FromUsername = State()
    ToUsername = State()
    Amount = State()


class AddMoneyState(StatesGroup):
    Username = State()
    Amount = State()
