from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from app.bot.keyboards import main_menu_keyboard
from app.bot.widgets.service import widget_service
from app.services.navigation import navigation_service

router = Router(name="common")


@router.message(CommandStart())
@router.message(Command("dashboard"))
@router.message(F.text == "📊 Панель CRM")
async def cmd_start(message: Message, state: FSMContext):
    """Привітання та відкриття інтерактивної панелі управління."""
    await state.clear()
    
    # Спроба надіслати нативний інтерактивний HTML Widget
    sent_widget = False
    if message.bot:
        sent_widget = await widget_service.send_dashboard(
            bot=message.bot,
            chat_id=message.chat.id,
            initial_tab="orders",
        )

    # Fallback або інформаційне повідомлення
    wh = navigation_service.warehouse_info
    text = (
        f"👋 **Вітаємо в Peat CRM!**\n"
        f"Інтерактивна система управління клієнтами, замовленнями та доставками торфу.\n\n"
        f"📍 **Базовий склад відвантаження:**\n"
        f"• {wh['name']}\n"
        f"• {wh['address']}\n\n"
        f"📋 **Швидкі команди:**\n"
        f"• `/new_order` — оформити замовлення\n"
        f"• `/orders` — список замовлень\n"
        f"• `/order_ID` — картка замовлення (напр. `/order_1`)\n"
        f"• `/customers` — база клієнтів\n"
        f"• `/dashboard` — оновити інтерактивну панель CRM\n"
        f"• `/help` — довідка"
    )
    if not sent_widget:
        await message.answer(text, reply_markup=main_menu_keyboard(), parse_mode="Markdown")



@router.message(Command("help"))
@router.message(F.text == "ℹ️ Допомога")
async def cmd_help(message: Message, state: FSMContext):
    """Довідка з використання бота."""
    text = (
        f"ℹ️ **Довідка Peat CRM**\n\n"
        f"**Робота з замовленнями:**\n"
        f"• `/orders` — переглянути 10 останніх замовлень\n"
        f"• `/orders in_delivery` — замовлення, які зараз у дорозі\n"
        f"• `/orders new` — нові замовлення\n"
        f"• `/order_123` — картка замовлення з кнопками навігації Waze та зміною статусу\n"
        f"• `/new_order` — покроковий майстер створення замовлення\n\n"
        f"**Робота з клієнтами:**\n"
        f"• `/customers` — переглянути список клієнтів\n"
        f"• `/customers Ковальчук` або `/customers 067` — швидкий пошук за ПІБ чи номером телефону\n"
        f"• `/new_customer` — покроковий майстер додавання клієнта\n\n"
        f"**Локації та навігація:**\n"
        f"При створенні клієнта або замовлення можна надіслати координати (`51.2981, 25.5532`) "
        f"або посилання на геолокацію з Viber / Google Maps. Бот автоматично сформує кнопку відкриття навігатора Waze."
    )
    await message.answer(text, parse_mode="Markdown")


@router.message(F.text == "❌ Скасувати введення")
async def cmd_cancel_fsm(message: Message, state: FSMContext):
    """Скасування поточного стану вводу."""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Немає активного процесу для скасування.", reply_markup=main_menu_keyboard())
        return

    await state.clear()
    await message.answer("❌ Дія скасована.", reply_markup=main_menu_keyboard())
