from aiogram.fsm.state import StatesGroup, State


class AddProduct(StatesGroup):
    name = State()
    price = State()
    description = State()


class EditProduct(StatesGroup):
    product_id = State()
    new_price = State()


class BroadcastMessage(StatesGroup):
    text = State()


class SupportReply(StatesGroup):
    ticket_id = State()
    text = State()
