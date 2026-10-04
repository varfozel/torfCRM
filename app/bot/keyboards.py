from typing import Optional
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from app.models.order import OrderStatus


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Головне меню команд."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Замовлення"), KeyboardButton(text="👥 Клієнти")],
            [KeyboardButton(text="➕ Нове замовлення"), KeyboardButton(text="➕ Новий клієнт")],
            [KeyboardButton(text="ℹ️ Допомога")],
        ],
        resize_keyboard=True,
    )


def cancel_or_skip_keyboard(allow_skip: bool = True) -> ReplyKeyboardMarkup:
    """Клавіатура для кроків FSM (з можливістю пропустити або скасувати)."""
    buttons = []
    if allow_skip:
        buttons.append(KeyboardButton(text="⏭ Пропустити"))
    buttons.append(KeyboardButton(text="❌ Скасувати введення"))
    return ReplyKeyboardMarkup(
        keyboard=[buttons],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def order_actions_keyboard(
    order_id: int,
    order_status: str,
    waze_url: Optional[str] = None,
    google_maps_url: Optional[str] = None,
) -> InlineKeyboardMarkup:
    """Інлайн-кнопки дій над замовленням (навігація, зміна статусів)."""
    rows = []

    # Рядок навігації
    nav_buttons = []
    if waze_url:
        nav_buttons.append(InlineKeyboardButton(text="🧭 Waze", url=waze_url))
    if google_maps_url:
        nav_buttons.append(InlineKeyboardButton(text="📍 Google Maps", url=google_maps_url))
    if nav_buttons:
        rows.append(nav_buttons)

    # Рядок дій доставки
    action_buttons = []
    if order_status in [OrderStatus.NEW.value, OrderStatus.PLANNED.value]:
        action_buttons.append(
            InlineKeyboardButton(text="🚚 Почати доставку", callback_data=f"start_del:{order_id}")
        )
    if order_status in [OrderStatus.NEW.value, OrderStatus.PLANNED.value, OrderStatus.IN_DELIVERY.value]:
        action_buttons.append(
            InlineKeyboardButton(text="✅ Доставлено", callback_data=f"complete_del:{order_id}")
        )
    if action_buttons:
        rows.append(action_buttons)

    # Скасування
    if order_status not in [OrderStatus.DELIVERED.value, OrderStatus.CANCELLED.value]:
        rows.append([
            InlineKeyboardButton(text="❌ Скасувати замовлення", callback_data=f"cancel_del:{order_id}")
        ])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def customer_actions_keyboard(customer_id: int) -> InlineKeyboardMarkup:
    """Інлайн-кнопки для швидких дій над клієнтом."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Створити замовлення",
                    callback_data=f"cust_new_ord:{customer_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Замовлення клієнта",
                    callback_data=f"cust_orders:{customer_id}",
                )
            ],
        ]
    )


def quick_products_keyboard() -> InlineKeyboardMarkup:
    """Швидкий вибір найпопулярніших позицій торфу."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Торф фрезерний кислий (pH 3.5-4.5)",
                    callback_data="prod:Торф фрезерний кислий (pH 3.5-4.5)",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Торф верховий нейтралізований",
                    callback_data="prod:Торф верховий нейтралізований",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Торф низинний",
                    callback_data="prod:Торф низинний",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Торф'яний паливний брикет",
                    callback_data="prod:Торф'яний паливний брикет",
                )
            ],
        ]
    )
