from aiogram.fsm.state import State, StatesGroup


class CustomerCreateStates(StatesGroup):
    name = State()
    phone = State()
    address = State()
    coordinates = State()
    notes = State()


class OrderCreateStates(StatesGroup):
    select_customer = State()
    product_name = State()
    quantity = State()
    unit_price = State()
    delivery_address = State()
    delivery_coordinates = State()
    notes = State()
