from decimal import Decimal
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import (
    cancel_or_skip_keyboard,
    customer_actions_keyboard,
    main_menu_keyboard,
)
from app.bot.states import CustomerCreateStates, OrderCreateStates
from app.database import AsyncSessionLocal
from app.schemas.customer import CustomerCreate
from app.services.customer_service import customer_service
from app.services.navigation import navigation_service
from app.services.order_service import order_service

router = Router(name="customers")


@router.message(Command("customers"))
@router.message(F.text == "👥 Клієнти")
async def cmd_list_customers(message: Message):
    """Пошук або список останніх клієнтів."""
    # Перевіримо чи вказано пошуковий запит після команди (напр. /customers Ковальчук)
    query_text = ""
    if message.text and message.text.startswith("/customers"):
        parts = message.text.split(maxsplit=1)
        if len(parts) > 1:
            query_text = parts[1].strip()

    async with AsyncSessionLocal() as session:
        customers = await customer_service.search_customers(session, query_text, limit=10)

    if not customers:
        msg = "🔍 Клієнтів не знайдено."
        if query_text:
            msg += f" За запитом: '{query_text}'"
        else:
            msg += " База клієнтів порожня. Додайте першого за допомогою /new_customer"
        await message.answer(msg, reply_markup=main_menu_keyboard())
        return

    title = f"👥 **Знайдено клієнтів** ({len(customers)}):" if query_text else "👥 **Останні клієнти**:"
    await message.answer(title, parse_mode="Markdown")

    for c in customers:
        coords_str = f"📍 {c.latitude:.4f}, {c.longitude:.4f}" if c.latitude and c.longitude else "📍 Координати не вказано"
        notes_str = f"\n📝 _{c.notes}_" if c.notes else ""
        card = (
            f"👤 **{c.name}** (ID: `{c.id}`)\n"
            f"📞 `{c.phone}`\n"
            f"🏠 {c.address}\n"
            f"{coords_str}{notes_str}"
        )
        await message.answer(
            card,
            reply_markup=customer_actions_keyboard(c.id),
            parse_mode="Markdown",
        )


@router.message(Command("new_customer"))
@router.message(F.text == "➕ Новий клієнт")
async def cmd_new_customer(message: Message, state: FSMContext):
    """Початок створення клієнта."""
    await state.clear()
    await state.set_state(CustomerCreateStates.name)
    await message.answer(
        "📝 **Створення нового клієнта** (Крок 1/5)\n\n"
        "Введіть повне ім'я клієнта або назву компанії:",
        reply_markup=cancel_or_skip_keyboard(allow_skip=False),
        parse_mode="Markdown",
    )


@router.message(CustomerCreateStates.name)
async def process_customer_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("⚠️ Ім'я занадто коротке. Введіть щонайменше 2 символи:")
        return

    await state.update_data(name=name)
    await state.set_state(CustomerCreateStates.phone)
    await message.answer(
        f"👍 Ім'я: **{name}**\n\n"
        "📞 (Крок 2/5) Введіть номер телефону (напр. `+380501234567`):",
        reply_markup=cancel_or_skip_keyboard(allow_skip=False),
        parse_mode="Markdown",
    )


@router.message(CustomerCreateStates.phone)
async def process_customer_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    if len(phone) < 6:
        await message.answer("⚠️ Номер телефону занадто короткий. Спробуйте ще раз:")
        return

    await state.update_data(phone=phone)
    await state.set_state(CustomerCreateStates.address)
    await message.answer(
        f"👍 Телефон: `{phone}`\n\n"
        "🏠 (Крок 3/5) Введіть адресу клієнта (населений пункт, вулиця, будинок):",
        reply_markup=cancel_or_skip_keyboard(allow_skip=False),
        parse_mode="Markdown",
    )


@router.message(CustomerCreateStates.address)
async def process_customer_address(message: Message, state: FSMContext):
    address = message.text.strip()
    if len(address) < 2:
        await message.answer("⚠️ Адреса занадто коротка. Введіть детальну адресу:")
        return

    await state.update_data(address=address)
    await state.set_state(CustomerCreateStates.coordinates)
    await message.answer(
        f"👍 Адреса: {address}\n\n"
        "📍 (Крок 4/5) Введіть координати або посилання з Viber/Google Maps (необов'язково):\n"
        "Наприклад: `51.2981, 25.5532` або надішліть посилання на точку.\n"
        "Якщо координат немає, натисніть '⏭ Пропустити'.",
        reply_markup=cancel_or_skip_keyboard(allow_skip=True),
        parse_mode="Markdown",
    )


@router.message(CustomerCreateStates.coordinates)
async def process_customer_coordinates(message: Message, state: FSMContext):
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

    await state.update_data(latitude=lat, longitude=lon)
    await state.set_state(CustomerCreateStates.notes)
    await message.answer(
        "📝 (Крок 5/5) Введіть додаткові примітки про клієнта (необов'язково):\n"
        "Або натисніть '⏭ Пропустити'.",
        reply_markup=cancel_or_skip_keyboard(allow_skip=True),
        parse_mode="Markdown",
    )


@router.message(CustomerCreateStates.notes)
async def process_customer_notes(message: Message, state: FSMContext):
    text = message.text.strip()
    notes = None if text == "⏭ Пропустити" else text

    data = await state.get_data()
    await state.clear()

    cust_create = CustomerCreate(
        name=data["name"],
        phone=data["phone"],
        address=data["address"],
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        notes=notes,
    )

    async with AsyncSessionLocal() as session:
        customer = await customer_service.create_customer(session, cust_create)

    coords_msg = (
        f"📍 `{customer.latitude:.6f}, {customer.longitude:.6f}`"
        if customer.latitude and customer.longitude
        else "не вказано"
    )

    await message.answer(
        f"🎉 **Клієнта успішно створено!**\n\n"
        f"👤 **{customer.name}** (ID: `{customer.id}`)\n"
        f"📞 `{customer.phone}`\n"
        f"🏠 {customer.address}\n"
        f"📍 Координати: {coords_msg}\n"
        f"📝 Примітки: {customer.notes or 'немає'}",
        reply_markup=customer_actions_keyboard(customer.id),
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith("cust_orders:"))
async def cb_customer_orders(call: CallbackQuery):
    """Показати замовлення конкретного клієнта."""
    customer_id = int(call.data.split(":")[1])
    async with AsyncSessionLocal() as session:
        orders = await order_service.list_orders(session, customer_id=customer_id, limit=5)

    if not orders:
        await call.answer("У цього клієнта ще немає замовлень.", show_alert=True)
        return

    await call.answer()
    await call.message.answer(f"📋 **Замовлення клієнта ID `{customer_id}`** ({len(orders)}):", parse_mode="Markdown")
    for o in orders:
        await call.message.answer(
            f"📦 **Замовлення #{o.id}** — {o.product_name}\n"
            f"Об'єм: {o.quantity} | Сума: {o.total_amount} грн\n"
            f"Статус: `{o.status}`\n"
            f"Деталі: `/order_{o.id}`",
            parse_mode="Markdown",
        )
