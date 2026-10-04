from decimal import Decimal
import re
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

from app.bot.keyboards import (
    cancel_or_skip_keyboard,
    delivery_price_keyboard,
    main_menu_keyboard,
    order_actions_keyboard,
    order_confirm_keyboard,
)
from app.bot.states import OrderCreateStates
from app.database import AsyncSessionLocal
from app.models.order import DEFAULT_PRODUCT_NAME, OrderStatus
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


def render_order_card(order) -> str:
    """Форматування тексту картки замовлення."""
    status_label = STATUS_ICONS.get(order.status, order.status)
    cust_name = order.customer.name if order.customer else f"ID {order.customer_id}"
    cust_phone = order.customer.phone if order.customer else "—"

    coords_line = ""
    if order.delivery_latitude and order.delivery_longitude:
        coords_line = f"📍 Точка вивантаження: `{order.delivery_latitude:.6f}, {order.delivery_longitude:.6f}`\n"

    delivery_times = ""
    if order.delivery_started_at:
        delivery_times += f"⏱ Виїзд: `{order.delivery_started_at.strftime('%Y-%m-%d %H:%M')}`\n"
    if order.delivery_completed_at:
        delivery_times += f"🏁 Доставлено: `{order.delivery_completed_at.strftime('%Y-%m-%d %H:%M')}`\n"

    notes_line = f"📝 Примітки: _{order.notes}_\n" if order.notes else ""

    product_total = getattr(order, "product_total", (order.quantity * order.unit_price).quantize(Decimal("0.01")))
    delivery_price = getattr(order, "delivery_price", Decimal("0.00"))

    return (
        f"📦 **Замовлення #{order.id}** — {status_label}\n\n"
        f"👤 **Клієнт:** {cust_name}\n"
        f"📞 **Телефон:** `{cust_phone}`\n"
        f"🧱 **Товар:** {order.product_name}\n"
        f"⚖️ **Кількість:** {order.quantity} | **Ціна за од.:** {order.unit_price} грн\n"
        f"💵 **Сума товару:** `{product_total}` грн\n"
        f"🚚 **Доставка:** `{delivery_price}` грн\n"
        f"💰 **Разом до сплати:** `{order.total_amount}` грн\n\n"
        f"🏠 **Адреса доставки:** {order.delivery_address}\n"
        f"{coords_line}"
        f"{delivery_times}"
        f"{notes_line}"
    )


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


@router.message(Command("orders"))
@router.message(F.text == "📋 Замовлення")
async def cmd_list_orders(message: Message):
    """Список останніх замовлень з можливістю фільтрації за статусом."""
    status_filter = None
    if message.text and message.text.startswith("/orders"):
        parts = message.text.split(maxsplit=1)
        if len(parts) > 1:
            raw_status = parts[1].strip().lower()
            valid_statuses = [s.value for s in OrderStatus]
            if raw_status in valid_statuses:
                status_filter = raw_status

    async with AsyncSessionLocal() as session:
        orders = await order_service.list_orders(session, status=status_filter, limit=10)

    if not orders:
        msg = "📋 Замовлень не знайдено."
        if status_filter:
            msg += f" Зі статусом `{status_filter}`."
        await message.answer(msg, reply_markup=main_menu_keyboard(), parse_mode="Markdown")
        return

    filter_title = f" зі статусом `{status_filter}`" if status_filter else ""
    await message.answer(f"📋 **Останні замовлення**{filter_title} ({len(orders)}):", parse_mode="Markdown")

    for o in orders:
        status_label = STATUS_ICONS.get(o.status, o.status)
        cust_name = o.customer.name if o.customer else "—"
        await message.answer(
            f"📦 **Замовлення #{o.id}** | {status_label}\n"
            f"👤 {cust_name} (📞 `{o.customer.phone if o.customer else ''}`)\n"
            f"🧱 {o.product_name}: {o.quantity} (товар: {o.product_total} грн, доставка: {o.delivery_price} грн)\n"
            f"💰 Разом: **{o.total_amount} грн**\n"
            f"🏠 {o.delivery_address}\n"
            f"👉 Деталі: `/order_{o.id}`",
            parse_mode="Markdown",
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

    card = render_order_card(order)
    kb = order_actions_keyboard(
        order_id=order.id,
        order_status=order.status,
        waze_url=waze_url,
        google_maps_url=gmaps_url,
    )
    await message.answer(card, reply_markup=kb, parse_mode="Markdown")


# Callbacks for Delivery Actions
@router.callback_query(F.data.startswith("start_del:"))
async def cb_start_delivery(call: CallbackQuery):
    order_id = int(call.data.split(":")[1])
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
        await call.message.edit_text(
            render_order_card(order),
            reply_markup=order_actions_keyboard(order.id, order.status, waze_url, gmaps_url),
            parse_mode="Markdown",
        )
    except Exception as e:
        await call.answer(f"Помилка: {e}", show_alert=True)


@router.callback_query(F.data.startswith("complete_del:"))
async def cb_complete_delivery(call: CallbackQuery):
    order_id = int(call.data.split(":")[1])
    try:
        async with AsyncSessionLocal() as session:
            order = await order_service.complete_delivery(session, order_id)
            order = await order_service.get_order(session, order_id)

        await call.answer("✅ Доставку успішно завершено!", show_alert=True)
        waze_url = navigation_service.generate_waze_url(
            order.delivery_latitude, order.delivery_longitude, order.delivery_address
        )
        await call.message.edit_text(
            render_order_card(order),
            reply_markup=order_actions_keyboard(order.id, order.status, waze_url=waze_url),
            parse_mode="Markdown",
        )
    except Exception as e:
        await call.answer(f"Помилка: {e}", show_alert=True)


@router.callback_query(F.data.startswith("cancel_del:"))
async def cb_cancel_delivery(call: CallbackQuery):
    order_id = int(call.data.split(":")[1])
    try:
        async with AsyncSessionLocal() as session:
            order = await order_service.cancel_order(session, order_id, notes="Скасовано через Telegram бот")
            order = await order_service.get_order(session, order_id)

        await call.answer("❌ Замовлення скасовано", show_alert=True)
        await call.message.edit_text(
            render_order_card(order),
            reply_markup=order_actions_keyboard(order.id, order.status),
            parse_mode="Markdown",
        )
    except Exception as e:
        await call.answer(f"Помилка: {e}", show_alert=True)


# FSM Wizard for Creating an Order
@router.message(Command("new_order"))
@router.message(F.text == "➕ Нове замовлення")
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
