from typing import Dict, Optional, Sequence
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from app.models.order import Order, OrderStatus


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Головне меню команд."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 Замовлення"), KeyboardButton(text="➕ Створити замовлення")],
            [KeyboardButton(text="👥 Клієнти"), KeyboardButton(text="➕ Новий клієнт")],
            [KeyboardButton(text="🔄 Оновити / Назад"), KeyboardButton(text="ℹ️ Допомога")],
        ],
        resize_keyboard=True,
    )


def order_categories_keyboard(counts: Optional[Dict[str, int]] = None) -> InlineKeyboardMarkup:
    """Клавіатура вибору категорії замовлень з лічильниками."""
    counts = counts or {}
    c_act = f" ({counts['active']})" if "active" in counts else ""
    c_del = f" ({counts['delivered']})" if "delivered" in counts else ""
    c_can = f" ({counts['cancelled']})" if "cancelled" in counts else ""
    c_all = f" ({counts['all']})" if "all" in counts else ""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"🟢 Активні{c_act}", callback_data="ord_cat:active:1")],
            [InlineKeyboardButton(text=f"✅ Виконані{c_del}", callback_data="ord_cat:delivered:1")],
            [InlineKeyboardButton(text=f"❌ Скасовані{c_can}", callback_data="ord_cat:cancelled:1")],
            [InlineKeyboardButton(text=f"📋 Всі замовлення{c_all}", callback_data="ord_cat:all:1")],
            [
                InlineKeyboardButton(text="🏠 Головне меню", callback_data="ord_nav:home"),
                InlineKeyboardButton(text="🔄 Оновити", callback_data="ord_cat_refresh"),
            ],
        ]
    )


def order_list_keyboard(
    orders: Sequence[Order],
    category: str,
    page: int,
    total_pages: int,
) -> InlineKeyboardMarkup:
    """Інлайн-клавіатура списку замовлень з пагінацією та переходом до деталей."""
    rows = []

    # Кнопки кожного замовлення
    for o in orders:
        cust_name = o.customer.name if o.customer else f"ID {o.customer_id}"
        if len(cust_name) > 16:
            cust_name = cust_name[:15] + "…"
        btn_text = f"📦 #{o.id} · {cust_name} · {o.quantity}т"
        rows.append([
            InlineKeyboardButton(
                text=btn_text,
                callback_data=f"ord_det:{o.id}:{category}:{page}",
            )
        ])

    # Рядок пагінації (⬅️ / ➡️)
    if total_pages > 1:
        pag_buttons = []
        if page > 1:
            pag_buttons.append(
                InlineKeyboardButton(text="⬅️", callback_data=f"ord_pg:{category}:{page - 1}")
            )
        pag_buttons.append(
            InlineKeyboardButton(text=f"📄 {page}/{total_pages}", callback_data="noop")
        )
        if page < total_pages:
            pag_buttons.append(
                InlineKeyboardButton(text="➡️", callback_data=f"ord_pg:{category}:{page + 1}")
            )
        rows.append(pag_buttons)

    # Кнопки навігації
    rows.append([
        InlineKeyboardButton(text="⬅️ Назад", callback_data="ord_nav:categories"),
        InlineKeyboardButton(text="🏠 Головне меню", callback_data="ord_nav:home"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)


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
    customer_phone: Optional[str] = None,
    waze_url: Optional[str] = None,
    google_maps_url: Optional[str] = None,
    back_category: Optional[str] = None,
    back_page: int = 1,
) -> InlineKeyboardMarkup:
    """Інлайн-кнопки дій над замовленням (дзвінок, навігація, зміна статусів, повернення)."""
    rows = []

    # Кнопка для дзвінка клієнту
    if customer_phone:
        rows.append([
            InlineKeyboardButton(
                text="📞 Зателефонувати клієнту",
                callback_data=f"ord_call:{order_id}",
            )
        ])

    # Рядок навігації
    nav_buttons = []
    if waze_url:
        nav_buttons.append(InlineKeyboardButton(text="🧭 Waze", url=waze_url))
    if google_maps_url:
        nav_buttons.append(InlineKeyboardButton(text="📍 Google Maps", url=google_maps_url))
    if nav_buttons:
        rows.append(nav_buttons)

    # Рядок дій доставки
    # Для зворотної сумісності з тестами зберігаємо start_del:{order_id} якщо back_category None
    suffix = f":{back_category}:{back_page}" if back_category is not None else ""
    action_buttons = []
    if order_status in [OrderStatus.NEW.value, OrderStatus.PLANNED.value]:
        action_buttons.append(
            InlineKeyboardButton(
                text="🚚 Почати доставку",
                callback_data=f"start_del:{order_id}{suffix}",
            )
        )
    if order_status in [OrderStatus.NEW.value, OrderStatus.PLANNED.value, OrderStatus.IN_DELIVERY.value]:
        action_buttons.append(
            InlineKeyboardButton(
                text="✅ Доставлено",
                callback_data=f"complete_del:{order_id}{suffix}",
            )
        )
    if action_buttons:
        rows.append(action_buttons)

    # Скасування
    if order_status not in [OrderStatus.DELIVERED.value, OrderStatus.CANCELLED.value]:
        rows.append([
            InlineKeyboardButton(
                text="❌ Скасувати замовлення",
                callback_data=f"cancel_del:{order_id}{suffix}",
            )
        ])

    # Кнопки повернення
    back_cb = f"ord_pg:{back_category}:{back_page}" if back_category else "ord_nav:categories"
    rows.append([
        InlineKeyboardButton(text="⬅️ Назад", callback_data=back_cb),
        InlineKeyboardButton(text="🏠 Головне меню", callback_data="ord_nav:home"),
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


def delivery_price_keyboard() -> InlineKeyboardMarkup:
    """Швидкий вибір безкоштовної доставки."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎁 Безкоштовна доставка (0 грн)",
                    callback_data="deliv:free",
                )
            ]
        ]
    )


def order_confirm_keyboard() -> InlineKeyboardMarkup:
    """Кнопки підтвердження створення замовлення."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Підтвердити створення",
                    callback_data="order_confirm:yes",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Скасувати",
                    callback_data="order_confirm:no",
                )
            ],
        ]
    )
