from decimal import Decimal
import math
import re
from typing import Optional, Sequence
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

from app.bot.keyboards import (
    cancel_or_skip_keyboard,
    delivery_price_keyboard,
    main_menu_keyboard,
    order_actions_keyboard,
    order_categories_keyboard,
    order_confirm_keyboard,
    order_list_keyboard,
)
from app.bot.states import OrderCreateStates
from app.database import AsyncSessionLocal
from app.models.order import DEFAULT_PRODUCT_NAME, Order, OrderStatus
from app.schemas.order import OrderCreate
from app.services.customer_service import customer_service
from app.services.navigation import navigation_service
from app.services.order_service import order_service

router = Router(name="orders")

STATUS_ICONS = {
    OrderStatus.NEW.value: "🆕 Нове",
    OrderStatus.PLANNED.value: "🗓 Заплановано",
    OrderStatus.IN_DELIVERY.value: "🚚 В дорозі",
    OrderStatus.DELIVERED.value: "✅ Доставлено",
    OrderStatus.CANCELLED.value: "❌ Скасовано",
}

ORDER_CATEGORIES = {
    "active": {
        "title": "🟢 Активні",
        "filter": [OrderStatus.NEW.value, OrderStatus.PLANNED.value, OrderStatus.IN_DELIVERY.value],
    },
    "delivered": {
        "title": "✅ Виконані",
        "filter": OrderStatus.DELIVERED.value,
    },
    "cancelled": {
        "title": "❌ Скасовані",
        "filter": OrderStatus.CANCELLED.value,
    },
    "all": {
        "title": "📋 Всі замовлення",
        "filter": None,
    },
}

ORDERS_PAGE_SIZE = 5


def normalize_phone_number(phone: Optional[str]) -> str:
    """Нормалізація номера телефону для Telegram/дзвінка."""
    if not phone:
        return ""
    cleaned = re.sub(r"[^\d+]", "", str(phone).strip())
    if cleaned.startswith("0") and len(cleaned) == 10:
        cleaned = "+38" + cleaned
    elif cleaned.startswith("380") and not cleaned.startswith("+"):
        cleaned = "+" + cleaned
    elif not cleaned.startswith("+") and cleaned.isdigit():
        cleaned = "+" + cleaned
    return cleaned


def render_order_card(order) -> str:
    """Форматування тексту картки замовлення з усіма обов'язковими показниками."""
    status_label = STATUS_ICONS.get(order.status, order.status)
    cust_name = order.customer.name if order.customer else f"ID {order.customer_id}"
    cust_phone = order.customer.phone if order.customer else "—"

    # Дата замовлення
    if getattr(order, "order_date", None):
        order_date_str = order.order_date.strftime("%d.%m.%Y")
    elif getattr(order, "created_at", None):
        order_date_str = order.created_at.strftime("%d.%m.%Y")
    else:
        order_date_str = "—"

    # Розрахункові показники
    product_total = getattr(order, "product_total", (order.quantity * order.unit_price).quantize(Decimal("0.01")))
    delivery_price = getattr(order, "delivery_price", Decimal("0.00"))

    # Кілометраж та тариф за км
    dist_val = getattr(order, "distance_km", None)
    dist_str = f"{dist_val} км" if dist_val is not None else "Не вказано"

    tariff_val = getattr(order, "delivery_price_per_km", None)
    tariff_str = f"{tariff_val} грн/км" if tariff_val is not None else "Не вказано"

    # Ознака встановлення суми вручну
    is_manual = getattr(order, "is_total_manual", False)
    if is_manual:
        calc_total = getattr(order, "calculated_total_amount", None)
        calc_note = f", розрахункова: {calc_total} грн" if calc_total is not None else ""
        total_line = f"💰 **Загальна/фінальна сума:** `{order.total_amount}` грн ⚠️ *(Встановлено вручну{calc_note})*"
    else:
        total_line = f"💰 **Загальна/фінальна сума:** `{order.total_amount}` грн"

    coords_line = ""
    if order.delivery_latitude and order.delivery_longitude:
        coords_line = f"📍 Точка вивантаження: `{order.delivery_latitude:.6f}, {order.delivery_longitude:.6f}`\n"

    delivery_times = ""
    if getattr(order, "delivery_started_at", None):
        delivery_times += f"⏱ Виїзд: `{order.delivery_started_at.strftime('%Y-%m-%d %H:%M')}`\n"
    if getattr(order, "delivery_completed_at", None):
        delivery_times += f"🏁 Доставлено: `{order.delivery_completed_at.strftime('%Y-%m-%d %H:%M')}`\n"

    notes_line = f"📝 Примітки: _{order.notes}_\n" if getattr(order, "notes", None) else ""

    return (
        f"📦 **Замовлення #{order.id}** — {status_label}\n\n"
        f"👤 **Клієнт:** {cust_name}\n"
        f"📞 **Телефон:** `{cust_phone}`\n"
        f"🏠 **Адреса доставки:** {order.delivery_address}\n"
        f"📅 **Дата замовлення:** {order_date_str}\n"
        f"🧱 **Товар:** {order.product_name}\n"
        f"⚖️ **Кількість:** {order.quantity} | **Ціна за од.:** {order.unit_price} грн\n"
        f"🛣 **Кілометраж:** {dist_str}\n"
        f"🚚 **Ціна доставки за км:** {tariff_str}\n"
        f"🚚 **Вартість доставки:** `{delivery_price}` грн\n"
        f"💵 **Сума товару:** `{product_total}` грн\n"
        f"{total_line}\n\n"
        f"{coords_line}"
        f"{delivery_times}"
        f"{notes_line}"
    )


def render_order_list_text(
    orders: Sequence[Order],
    category_title: str,
    page: int,
    total_pages: int,
    total_count: int,
) -> str:
    """Текстовий список замовлень для поточної сторінки пагінації."""
    if not orders:
        return (
            f"📦 **Замовлення: {category_title}**\n\n"
            f"Замовлень у цій категорії наразі немає."
        )

    lines = [
        f"📦 **Замовлення: {category_title}**",
        f"📄 Сторінка {page} з {total_pages} (Всього: {total_count})\n",
    ]

    for o in orders:
        status_label = STATUS_ICONS.get(o.status, o.status)
        cust_name = o.customer.name if o.customer else f"ID {o.customer_id}"
        if getattr(o, "order_date", None):
            date_str = o.order_date.strftime("%d.%m.%Y")
        elif getattr(o, "created_at", None):
            date_str = o.created_at.strftime("%d.%m.%Y")
        else:
            date_str = "—"

        lines.append(
            f"📦 **Замовлення #{o.id}** | {status_label}\n"
            f"👤 **Клієнт:** {cust_name}\n"
            f"⚖️ **Кількість тонн:** {o.quantity} т | 💰 **Сума:** {o.total_amount} грн\n"
            f"🏠 **Адреса:** {o.delivery_address}\n"
            f"📅 **Дата:** {date_str}\n"
        )

    lines.append("Натисніть кнопку замовлення нижче для перегляду деталей:")
    return "\n".join(lines)


def render_order_summary(data: dict) -> str:
    """Форматування підсумку перед підтвердженням замовлення."""
    cust_name = data.get("customer_name", "Клієнт")
    qty = Decimal(data["quantity"])
    price = Decimal(data["unit_price"])
    deliv = Decimal(data.get("delivery_price", "0.00"))
    prod_total = (qty * price).quantize(Decimal("0.01"))
    total = (prod_total + deliv).quantize(Decimal("0.01"))
    addr = data.get("delivery_address", "")
    coords = ""
    if data.get("delivery_lat") and data.get("delivery_lon"):
        coords = f"📍 Координати: `{data['delivery_lat']}, {data['delivery_lon']}`\n"
    notes = f"📝 Примітки: _{data['notes']}_\n" if data.get("notes") else ""

    return (
        f"📋 **Нове замовлення**\n\n"
        f"👤 **Клієнт:** {cust_name}\n"
        f"• **Товар:** {DEFAULT_PRODUCT_NAME}\n"
        f"• **Кількість:** {qty}\n"
        f"• **Ціна за одиницю:** {price} грн\n"
        f"• **Сума товару:** {prod_total} грн\n"
        f"• **Доставка:** {deliv} грн\n"
        f"• **Разом до сплати: {total} грн**\n\n"
        f"🏠 **Адреса:** {addr}\n"
        f"{coords}"
        f"{notes}\n"
        f"Підтвердіть створення замовлення:"
    )


async def show_orders_page(
    event: Message | CallbackQuery,
    category: str = "active",
    page: int = 1,
):
    """Відображення списку замовлень обраної категорії з пагінацією."""
    cat_info = ORDER_CATEGORIES.get(category, ORDER_CATEGORIES["all"])
    status_filter = cat_info["filter"]

    async with AsyncSessionLocal() as session:
        total_count = await order_service.count_orders(session, status=status_filter)
        total_pages = max(1, math.ceil(total_count / ORDERS_PAGE_SIZE))
        page = min(max(1, page), total_pages)
        skip = (page - 1) * ORDERS_PAGE_SIZE
        orders = await order_service.list_orders(
            session,
            status=status_filter,
            skip=skip,
            limit=ORDERS_PAGE_SIZE,
        )

    text = render_order_list_text(
        orders=orders,
        category_title=cat_info["title"],
        page=page,
        total_pages=total_pages,
        total_count=total_count,
    )
    kb = order_list_keyboard(
        orders=orders,
        category=category,
        page=page,
        total_pages=total_pages,
    )

    if isinstance(event, CallbackQuery):
        await event.answer()
        try:
            await event.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
        except Exception:
            await event.message.answer(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await event.answer(text, reply_markup=kb, parse_mode="Markdown")


@router.message(Command("orders"))
@router.message(F.text.in_(["📦 Замовлення", "📋 Замовлення"]))
async def cmd_list_orders(message: Message):
    """Меню вибору категорії замовлень або фільтр зі статусом."""
    if message.text and message.text.startswith("/orders"):
        parts = message.text.split(maxsplit=1)
        if len(parts) > 1:
            raw_arg = parts[1].strip().lower()
            if raw_arg in ORDER_CATEGORIES:
                await show_orders_page(message, category=raw_arg, page=1)
                return
            valid_statuses = [s.value for s in OrderStatus]
            if raw_arg in valid_statuses:
                cat = "delivered" if raw_arg == "delivered" else ("cancelled" if raw_arg == "cancelled" else "active")
                await show_orders_page(message, category=cat, page=1)
                return

    # Показуємо меню вибору категорій з лічильниками
    async with AsyncSessionLocal() as session:
        counts = await order_service.get_orders_category_counts(session)

    text = (
        "📦 **Управління замовленнями**\n\n"
        "Оберіть категорію замовлень для перегляду:"
    )
    await message.answer(
        text,
        reply_markup=order_categories_keyboard(counts),
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith("ord_cat:"))
async def cb_category_select(call: CallbackQuery):
    """Обробник вибору категорії замовлень."""
    parts = call.data.split(":")
    category = parts[1]
    page = int(parts[2]) if len(parts) > 2 else 1
    await show_orders_page(call, category=category, page=page)


@router.callback_query(F.data.startswith("ord_pg:"))
async def cb_page_switch(call: CallbackQuery):
    """Обробник перемикання сторінок пагінації."""
    parts = call.data.split(":")
    category = parts[1]
    page = int(parts[2])
    await show_orders_page(call, category=category, page=page)


@router.callback_query(F.data == "ord_cat_refresh")
async def cb_category_refresh(call: CallbackQuery):
    """Оновлення лічильників у меню категорій."""
    async with AsyncSessionLocal() as session:
        counts = await order_service.get_orders_category_counts(session)
    await call.answer("Оновлено 🔄")
    text = (
        "📦 **Управління замовленнями**\n\n"
        "Оберіть категорію замовлень для перегляду:"
    )
    try:
        await call.message.edit_text(
            text,
            reply_markup=order_categories_keyboard(counts),
            parse_mode="Markdown",
        )
    except Exception:
        pass


@router.callback_query(F.data == "ord_nav:categories")
async def cb_nav_categories(call: CallbackQuery):
    """Повернення до меню вибору категорій."""
    async with AsyncSessionLocal() as session:
        counts = await order_service.get_orders_category_counts(session)
    await call.answer()
    text = (
        "📦 **Управління замовленнями**\n\n"
        "Оберіть категорію замовлень для перегляду:"
    )
    try:
        await call.message.edit_text(
            text,
            reply_markup=order_categories_keyboard(counts),
            parse_mode="Markdown",
        )
    except Exception:
        pass


@router.callback_query(F.data == "ord_nav:home")
async def cb_nav_home(call: CallbackQuery, state: FSMContext):
    """Повернення до головного меню бота."""
    await state.clear()
    await call.answer()
    wh = navigation_service.warehouse_info
    async with AsyncSessionLocal() as session:
        counts = await order_service.get_orders_category_counts(session)
    text = (
        f"👋 **Головне меню Peat CRM**\n\n"
        f"📍 **Базовий склад:** {wh['name']} ({wh['address']})\n\n"
        f"Оберіть категорію замовлень нижче або скористайтесь кнопками меню:"
    )
    try:
        await call.message.edit_text(
            text,
            reply_markup=order_categories_keyboard(counts),
            parse_mode="Markdown",
        )
    except Exception:
        pass


@router.callback_query(F.data == "noop")
async def cb_noop(call: CallbackQuery):
    """Клік на неактивну кнопку індикатора сторінки."""
    await call.answer()


@router.callback_query(F.data.startswith("ord_det:"))
async def cb_order_details(call: CallbackQuery):
    """Відкриття деталей конкретного замовлення з клавіатури списку."""
    parts = call.data.split(":")
    order_id = int(parts[1])
    category = parts[2] if len(parts) > 2 else "active"
    page = int(parts[3]) if len(parts) > 3 else 1

    async with AsyncSessionLocal() as session:
        order = await order_service.get_order(session, order_id)

    if not order:
        await call.answer(f"❌ Замовлення #{order_id} не знайдено.", show_alert=True)
        return

    await call.answer()
    waze_url = navigation_service.generate_waze_url(
        latitude=order.delivery_latitude,
        longitude=order.delivery_longitude,
        address=order.delivery_address,
    )
    gmaps_url = navigation_service.generate_google_maps_url(
        latitude=order.delivery_latitude,
        longitude=order.delivery_longitude,
        address=order.delivery_address,
    )

    cust_phone = order.customer.phone if order.customer else None
    card = render_order_card(order)
    kb = order_actions_keyboard(
        order_id=order.id,
        order_status=order.status,
        customer_phone=cust_phone,
        waze_url=waze_url,
        google_maps_url=gmaps_url,
        back_category=category,
        back_page=page,
    )
    await call.message.edit_text(card, reply_markup=kb, parse_mode="Markdown")


@router.callback_query(F.data.startswith("ord_call:"))
async def cb_call_customer(call: CallbackQuery):
    """Відправка картки контакту клієнта для швидкого виклику."""
    order_id = int(call.data.split(":")[1])
    async with AsyncSessionLocal() as session:
        order = await order_service.get_order(session, order_id)

    if not order or not order.customer or not order.customer.phone:
        await call.answer("⚠️ Номер телефону клієнта не знайдено в CRM.", show_alert=True)
        return

    phone = normalize_phone_number(order.customer.phone)
    cust_name = order.customer.name or "Клієнт"

    await call.answer(f"📞 Телефон: {phone}", show_alert=False)
    await call.message.answer_contact(
        phone_number=phone,
        first_name=cust_name,
    )


@router.message(F.text.regexp(r"^/order_(\d+)$"))
@router.message(F.text.regexp(r"^/order\s+(\d+)$"))
async def cmd_order_details(message: Message):
    """Перегляд деталей замовлення за ID."""
    match = re.search(r"\d+", message.text)
    if not match:
        await message.answer("⚠️ Вкажіть номер замовлення, наприклад: `/order_1`")
        return

    order_id = int(match.group(0))
    async with AsyncSessionLocal() as session:
        order = await order_service.get_order(session, order_id)

    if not order:
        await message.answer(f"❌ Замовлення #{order_id} не знайдено.", reply_markup=main_menu_keyboard())
        return

    waze_url = navigation_service.generate_waze_url(
        latitude=order.delivery_latitude,
        longitude=order.delivery_longitude,
        address=order.delivery_address,
    )
    gmaps_url = navigation_service.generate_google_maps_url(
        latitude=order.delivery_latitude,
        longitude=order.delivery_longitude,
        address=order.delivery_address,
    )

    cust_phone = order.customer.phone if order.customer else None
    card = render_order_card(order)
    kb = order_actions_keyboard(
        order_id=order.id,
        order_status=order.status,
        customer_phone=cust_phone,
        waze_url=waze_url,
        google_maps_url=gmaps_url,
        back_category=None,
    )
    await message.answer(card, reply_markup=kb, parse_mode="Markdown")


# Callbacks for Delivery Actions
@router.callback_query(F.data.startswith("start_del:"))
async def cb_start_delivery(call: CallbackQuery):
    parts = call.data.split(":")
    order_id = int(parts[1])
    back_cat = parts[2] if len(parts) > 2 else None
    back_pg = int(parts[3]) if len(parts) > 3 else 1
    try:
        async with AsyncSessionLocal() as session:
            order = await order_service.start_delivery(session, order_id)
            order = await order_service.get_order(session, order_id)

        await call.answer("🚚 Доставку розпочато!", show_alert=False)
        waze_url = navigation_service.generate_waze_url(
            order.delivery_latitude, order.delivery_longitude, order.delivery_address
        )
        gmaps_url = navigation_service.generate_google_maps_url(
            order.delivery_latitude, order.delivery_longitude, order.delivery_address
        )
        cust_phone = order.customer.phone if order.customer else None
        await call.message.edit_text(
            render_order_card(order),
            reply_markup=order_actions_keyboard(
                order.id,
                order.status,
                customer_phone=cust_phone,
                waze_url=waze_url,
                google_maps_url=gmaps_url,
                back_category=back_cat,
                back_page=back_pg,
            ),
            parse_mode="Markdown",
        )
    except Exception as e:
        await call.answer(f"Помилка: {e}", show_alert=True)


@router.callback_query(F.data.startswith("complete_del:"))
async def cb_complete_delivery(call: CallbackQuery):
    parts = call.data.split(":")
    order_id = int(parts[1])
    back_cat = parts[2] if len(parts) > 2 else None
    back_pg = int(parts[3]) if len(parts) > 3 else 1
    try:
        async with AsyncSessionLocal() as session:
            order = await order_service.complete_delivery(session, order_id)
            order = await order_service.get_order(session, order_id)

        await call.answer("✅ Доставку успішно завершено!", show_alert=True)
        waze_url = navigation_service.generate_waze_url(
            order.delivery_latitude, order.delivery_longitude, order.delivery_address
        )
        gmaps_url = navigation_service.generate_google_maps_url(
            order.delivery_latitude, order.delivery_longitude, order.delivery_address
        )
        cust_phone = order.customer.phone if order.customer else None
        await call.message.edit_text(
            render_order_card(order),
            reply_markup=order_actions_keyboard(
                order.id,
                order.status,
                customer_phone=cust_phone,
                waze_url=waze_url,
                google_maps_url=gmaps_url,
                back_category=back_cat,
                back_page=back_pg,
            ),
            parse_mode="Markdown",
        )
    except Exception as e:
        await call.answer(f"Помилка: {e}", show_alert=True)


@router.callback_query(F.data.startswith("cancel_del:"))
async def cb_cancel_delivery(call: CallbackQuery):
    parts = call.data.split(":")
    order_id = int(parts[1])
    back_cat = parts[2] if len(parts) > 2 else None
    back_pg = int(parts[3]) if len(parts) > 3 else 1
    try:
        async with AsyncSessionLocal() as session:
            order = await order_service.cancel_order(session, order_id, notes="Скасовано через Telegram бот")
            order = await order_service.get_order(session, order_id)

        await call.answer("❌ Замовлення скасовано", show_alert=True)
        cust_phone = order.customer.phone if order.customer else None
        await call.message.edit_text(
            render_order_card(order),
            reply_markup=order_actions_keyboard(
                order.id,
                order.status,
                customer_phone=cust_phone,
                back_category=back_cat,
                back_page=back_pg,
            ),
            parse_mode="Markdown",
        )
    except Exception as e:
        await call.answer(f"Помилка: {e}", show_alert=True)


# FSM Wizard for Creating an Order
@router.message(Command("new_order"))
@router.message(F.text.in_(["➕ Створити замовлення", "➕ Нове замовлення"]))
async def cmd_new_order(message: Message, state: FSMContext):
    """Початок оформлення замовлення."""
    await state.clear()
    await state.set_state(OrderCreateStates.select_customer)
    await message.answer(
        "📦 **Оформлення нового замовлення** (Крок 1/5)\n"
        "Товар: **Торф'яний брикет**\n\n"
        "Введіть **ID клієнта** (напр. `1`) або номер телефону / прізвище для пошуку:",
        reply_markup=cancel_or_skip_keyboard(allow_skip=False),
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith("cust_new_ord:"))
async def cb_start_order_for_customer(call: CallbackQuery, state: FSMContext):
    """Швидкий старт замовлення прямо з картки клієнта."""
    customer_id = int(call.data.split(":")[1])
    async with AsyncSessionLocal() as session:
        customer = await customer_service.get_customer(session, customer_id)

    if not customer:
        await call.answer("Клієнта не знайдено!", show_alert=True)
        return

    await call.answer()
    await state.clear()
    await state.update_data(
        customer_id=customer.id,
        customer_name=customer.name,
        customer_address=customer.address,
        customer_lat=str(customer.latitude) if customer.latitude else None,
        customer_lon=str(customer.longitude) if customer.longitude else None,
    )
    await state.set_state(OrderCreateStates.quantity)
    await call.message.answer(
        f"👤 Клієнт: **{customer.name}** (`{customer.phone}`)\n"
        f"🧱 Товар: **{DEFAULT_PRODUCT_NAME}**\n\n"
        "⚖️ (Крок 2/5) Введіть кількість торф'яного брикету (напр. `10` або `15.5`):",
        reply_markup=cancel_or_skip_keyboard(allow_skip=False),
        parse_mode="Markdown",
    )


@router.message(OrderCreateStates.select_customer)
async def process_select_customer(message: Message, state: FSMContext):
    input_text = message.text.strip()

    async with AsyncSessionLocal() as session:
        if input_text.isdigit():
            customer = await customer_service.get_customer(session, int(input_text))
            if customer:
                await state.update_data(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    customer_address=customer.address,
                    customer_lat=str(customer.latitude) if customer.latitude else None,
                    customer_lon=str(customer.longitude) if customer.longitude else None,
                )
                await state.set_state(OrderCreateStates.quantity)
                await message.answer(
                    f"✅ Обрано клієнта: **{customer.name}**\n"
                    f"🧱 Товар: **{DEFAULT_PRODUCT_NAME}**\n\n"
                    "⚖️ (Крок 2/5) Введіть кількість торф'яного брикету (напр. `10` або `15.5`):",
                    reply_markup=cancel_or_skip_keyboard(allow_skip=False),
                    parse_mode="Markdown",
                )
                return

        customers = await customer_service.search_customers(session, input_text, limit=5)

    if not customers:
        await message.answer(
            f"🔍 Клієнта за запитом '{input_text}' не знайдено.\n"
            "Введіть інший номер/прізвище або створіть клієнта командою /new_customer:"
        )
        return

    if len(customers) == 1:
        c = customers[0]
        await state.update_data(
            customer_id=c.id,
            customer_name=c.name,
            customer_address=c.address,
            customer_lat=str(c.latitude) if c.latitude else None,
            customer_lon=str(c.longitude) if c.longitude else None,
        )
        await state.set_state(OrderCreateStates.quantity)
        await message.answer(
            f"✅ Знайдено клієнта: **{c.name}** (ID: `{c.id}`)\n"
            f"🧱 Товар: **{DEFAULT_PRODUCT_NAME}**\n\n"
            "⚖️ (Крок 2/5) Введіть кількість торф'яного брикету (напр. `10` або `15.5`):",
            reply_markup=cancel_or_skip_keyboard(allow_skip=False),
            parse_mode="Markdown",
        )
    else:
        text = "🔍 Знайдено кілька клієнтів. Введіть точний ID зі списку:\n\n"
        for c in customers:
            text += f"• ID `{c.id}`: **{c.name}** (📞 `{c.phone}`, {c.address})\n"
        await message.answer(text, parse_mode="Markdown")


@router.message(OrderCreateStates.quantity)
async def process_quantity(message: Message, state: FSMContext):
    text = message.text.strip().replace(",", ".")
    try:
        qty = Decimal(text)
        if qty <= 0:
            raise ValueError
    except Exception:
        await message.answer("⚠️ Введіть коректне додатне число (наприклад `10` або `12.5`):")
        return

    await state.update_data(quantity=str(qty))
    await state.set_state(OrderCreateStates.unit_price)
    await message.answer(
        f"⚖️ Кількість: **{qty}**\n\n"
        "💵 (Крок 3/5) Введіть ціну за одиницю брикету в грн (наприклад `200` або `850`):",
        reply_markup=cancel_or_skip_keyboard(allow_skip=False),
        parse_mode="Markdown",
    )


@router.message(OrderCreateStates.unit_price)
async def process_unit_price(message: Message, state: FSMContext):
    text = message.text.strip().replace(",", ".")
    try:
        price = Decimal(text)
        if price < 0:
            raise ValueError
    except Exception:
        await message.answer("⚠️ Введіть коректну ціну (наприклад `200` або `850`):")
        return

    await state.update_data(unit_price=str(price))
    await state.set_state(OrderCreateStates.delivery_price)
    await message.answer(
        f"💵 Ціна за одиницю: **{price} грн**\n\n"
        "🚚 (Крок 4/5) Введіть вартість доставки в грн (наприклад `350` або `0`):\n"
        "Або натисніть кнопку нижче, якщо доставка безкоштовна:",
        reply_markup=delivery_price_keyboard(),
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "deliv:free", OrderCreateStates.delivery_price)
async def cb_free_delivery(call: CallbackQuery, state: FSMContext):
    await state.update_data(delivery_price="0.00")
    await state.set_state(OrderCreateStates.delivery_address)
    await call.answer()

    data = await state.get_data()
    customer_addr = data.get("customer_address", "")
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Адреса клієнта", callback_data="addr:use_customer")]
        ]
    )
    await call.message.answer(
        "🚚 Доставка: **Безкоштовно (0.00 грн)**\n\n"
        f"🏠 (Крок 5/5) Введіть адресу доставки або натисніть '🏠 Адреса клієнта' ({customer_addr}):",
        reply_markup=kb,
        parse_mode="Markdown",
    )


@router.message(OrderCreateStates.delivery_price)
async def process_delivery_price(message: Message, state: FSMContext):
    text = message.text.strip().replace(",", ".")
    try:
        deliv = Decimal(text)
        if deliv < 0:
            raise ValueError
    except Exception:
        await message.answer("⚠️ Введіть коректну вартість доставки (наприклад `350` або `0`):")
        return

    await state.update_data(delivery_price=str(deliv.quantize(Decimal("0.01"))))
    await state.set_state(OrderCreateStates.delivery_address)

    data = await state.get_data()
    customer_addr = data.get("customer_address", "")
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Адреса клієнта", callback_data="addr:use_customer")]
        ]
    )
    await message.answer(
        f"🚚 Доставка: **{deliv} грн**\n\n"
        f"🏠 (Крок 5/5) Введіть адресу доставки або натисніть '🏠 Адреса клієнта' ({customer_addr}):",
        reply_markup=kb,
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "addr:use_customer", OrderCreateStates.delivery_address)
async def cb_use_customer_address(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    addr = data.get("customer_address", "")
    await state.update_data(delivery_address=addr)
    await state.set_state(OrderCreateStates.delivery_coordinates)
    await call.answer()
    await call.message.answer(
        f"🏠 Адреса доставки: **{addr}**\n\n"
        "📍 Введіть координати або посилання з Viber (необов'язково):\n"
        "Або натисніть '⏭ Пропустити'.",
        reply_markup=cancel_or_skip_keyboard(allow_skip=True),
        parse_mode="Markdown",
    )


@router.message(OrderCreateStates.delivery_address)
async def process_delivery_address(message: Message, state: FSMContext):
    addr = message.text.strip()
    if len(addr) < 2:
        await message.answer("⚠️ Введіть коректну адресу доставки:")
        return

    await state.update_data(delivery_address=addr)
    await state.set_state(OrderCreateStates.delivery_coordinates)
    await message.answer(
        f"🏠 Адреса доставки: **{addr}**\n\n"
        "📍 Введіть координати або посилання з Viber (необов'язково):\n"
        "Або натисніть '⏭ Пропустити'.",
        reply_markup=cancel_or_skip_keyboard(allow_skip=True),
        parse_mode="Markdown",
    )


@router.message(OrderCreateStates.delivery_coordinates)
async def process_delivery_coordinates(message: Message, state: FSMContext):
    text = message.text.strip()
    lat, lon = None, None

    if text != "⏭ Пропустити":
        lat, lon = navigation_service.parse_coordinates(text)
        if lat is None or lon is None:
            await message.answer(
                "⚠️ Не вдалося розпізнати координати або посилання.\n"
                "Спробуйте надіслати у форматі `51.2981, 25.5532` або натисніть '⏭ Пропустити':"
            )
            return

    await state.update_data(
        delivery_lat=str(lat) if lat is not None else None,
        delivery_lon=str(lon) if lon is not None else None,
    )
    await state.set_state(OrderCreateStates.notes)
    await message.answer(
        "📝 Введіть примітки до замовлення (необов'язково):\nАбо натисніть '⏭ Пропустити'.",
        reply_markup=cancel_or_skip_keyboard(allow_skip=True),
        parse_mode="Markdown",
    )


@router.message(OrderCreateStates.notes)
async def process_notes_and_show_summary(message: Message, state: FSMContext):
    text = message.text.strip()
    notes = None if text == "⏭ Пропустити" else text
    await state.update_data(notes=notes)

    data = await state.get_data()
    summary_text = render_order_summary(data)

    await state.set_state(OrderCreateStates.confirm_order)
    await message.answer(
        summary_text,
        reply_markup=order_confirm_keyboard(),
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "order_confirm:yes", OrderCreateStates.confirm_order)
async def cb_confirm_order(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    deliv_lat = Decimal(data["delivery_lat"]) if data.get("delivery_lat") else None
    deliv_lon = Decimal(data["delivery_lon"]) if data.get("delivery_lon") else None

    order_in = OrderCreate(
        customer_id=data["customer_id"],
        product_name=DEFAULT_PRODUCT_NAME,
        quantity=Decimal(data["quantity"]),
        unit_price=Decimal(data["unit_price"]),
        delivery_price=Decimal(data.get("delivery_price", "0.00")),
        delivery_address=data.get("delivery_address"),
        delivery_latitude=deliv_lat,
        delivery_longitude=deliv_lon,
        notes=data.get("notes"),
    )

    try:
        async with AsyncSessionLocal() as session:
            order = await order_service.create_order(session, order_in)
            order = await order_service.get_order(session, order.id)

        waze_url = navigation_service.generate_waze_url(
            order.delivery_latitude, order.delivery_longitude, order.delivery_address
        )
        gmaps_url = navigation_service.generate_google_maps_url(
            order.delivery_latitude, order.delivery_longitude, order.delivery_address
        )

        await call.answer("🎉 Замовлення створено!")
        await call.message.edit_text(
            f"🎉 **Замовлення #{order.id} успішно створено!**\n\n" + render_order_card(order),
            reply_markup=order_actions_keyboard(order.id, order.status, waze_url, gmaps_url),
            parse_mode="Markdown",
        )
    except Exception as e:
        await call.answer(f"Помилка при збереженні: {e}", show_alert=True)


@router.callback_query(F.data == "order_confirm:no", OrderCreateStates.confirm_order)
async def cb_cancel_order_creation(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer("Створення скасовано.")
    await call.message.edit_text(
        "❌ Створення замовлення скасовано. Жодних даних не збережено.",
        reply_markup=None,
    )
    await call.message.answer("Оберіть дію в меню нижче:", reply_markup=main_menu_keyboard())
