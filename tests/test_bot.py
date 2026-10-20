from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.bot.bot import AccessControlMiddleware
from app.bot.handlers.orders import (
    cb_call_customer,
    cb_order_details,
    normalize_phone_number,
    render_order_card,
    render_order_list_text,
    render_order_summary,
)
from app.bot.keyboards import (
    cancel_or_skip_keyboard,
    delivery_price_keyboard,
    main_menu_keyboard,
    order_actions_keyboard,
    order_categories_keyboard,
    order_confirm_keyboard,
    order_list_keyboard,
)
from app.models.customer import Customer
from app.models.order import DEFAULT_PRODUCT_NAME, Order, OrderStatus


def test_order_actions_keyboard():
    # 1. New order with Waze link
    waze = "https://waze.com/ul?ll=51.298100,25.553200&navigate=yes"
    kb_new = order_actions_keyboard(
        order_id=1,
        order_status=OrderStatus.NEW.value,
        waze_url=waze,
    )
    all_buttons = [btn for row in kb_new.inline_keyboard for btn in row]
    btn_texts = [b.text for b in all_buttons]
    btn_callbacks = [b.callback_data for b in all_buttons if b.callback_data]

    assert "🧭 Waze" in btn_texts
    assert "🚚 Почати доставку" in btn_texts
    assert "start_del:1" in btn_callbacks
    assert "cancel_del:1" in btn_callbacks

    # 2. Delivered order: no start or complete buttons
    kb_del = order_actions_keyboard(
        order_id=2,
        order_status=OrderStatus.DELIVERED.value,
        waze_url=None,
    )
    del_texts = [btn.text for row in kb_del.inline_keyboard for btn in row]
    assert "🚚 Почати доставку" not in del_texts
    assert "✅ Доставлено" not in del_texts
    assert "❌ Скасувати замовлення" not in del_texts


def test_cancel_or_skip_keyboard():
    kb_with_skip = cancel_or_skip_keyboard(allow_skip=True)
    buttons_skip = [btn.text for row in kb_with_skip.keyboard for btn in row]
    assert "⏭ Пропустити" in buttons_skip
    assert "❌ Скасувати введення" in buttons_skip

    kb_no_skip = cancel_or_skip_keyboard(allow_skip=False)
    buttons_no_skip = [btn.text for row in kb_no_skip.keyboard for btn in row]
    assert "⏭ Пропустити" not in buttons_no_skip
    assert "❌ Скасувати введення" in buttons_no_skip


def test_delivery_and_confirm_keyboards():
    deliv_kb = delivery_price_keyboard()
    deliv_callbacks = [b.callback_data for row in deliv_kb.inline_keyboard for b in row]
    assert "deliv:free" in deliv_callbacks

    confirm_kb = order_confirm_keyboard()
    confirm_callbacks = [b.callback_data for row in confirm_kb.inline_keyboard for b in row]
    assert "order_confirm:yes" in confirm_callbacks
    assert "order_confirm:no" in confirm_callbacks


def test_render_order_card():
    customer = Customer(
        id=5,
        name="Тарас Григорович",
        phone="+380501112233",
        address="м. Луцьк",
    )
    order = Order(
        id=42,
        customer_id=5,
        customer=customer,
        product_name=DEFAULT_PRODUCT_NAME,
        quantity=Decimal("10.00"),
        unit_price=Decimal("200.00"),
        delivery_price=Decimal("350.00"),
        total_amount=Decimal("2350.00"),
        delivery_address="м. Луцьк, вул. Шкільна 2",
        delivery_latitude=Decimal("51.298100"),
        delivery_longitude=Decimal("25.553200"),
        status=OrderStatus.NEW.value,
        notes="Вивантажити за будинком",
    )

    card = render_order_card(order)
    assert "Замовлення #42" in card
    assert "Тарас Григорович" in card
    assert "+380501112233" in card
    assert DEFAULT_PRODUCT_NAME in card
    assert "2000.00" in card  # Product total
    assert "350.00" in card   # Delivery price
    assert "2350.00" in card  # Total amount
    assert "51.298100, 25.553200" in card
    assert "Вивантажити за будинком" in card


def test_render_order_summary():
    data = {
        "customer_name": "Іван Іванович",
        "quantity": "10.00",
        "unit_price": "200.00",
        "delivery_price": "350.00",
        "delivery_address": "м. Луцьк, вул. Польова 10",
        "notes": "Дзвонити водію",
    }
    summary = render_order_summary(data)
    assert "Нове замовлення" in summary
    assert "Іван Іванович" in summary
    assert DEFAULT_PRODUCT_NAME in summary
    assert "2000.00 грн" in summary
    assert "350.00 грн" in summary
    assert "2350.00 грн" in summary
    assert "м. Луцьк, вул. Польова 10" in summary
    assert "Дзвонити водію" in summary


@pytest.mark.asyncio
async def test_access_control_middleware(monkeypatch):
    from app.config import get_settings

    middleware = AccessControlMiddleware()
    handler = AsyncMock(return_value="success")

    # 1. When allowed_telegram_ids is empty -> allow all
    mock_settings = get_settings()
    monkeypatch.setattr(mock_settings, "TELEGRAM_ALLOWED_USER_IDS", "")

    event = MagicMock()
    event.from_user.id = 999
    event.from_user.username = "stranger"

    res = await middleware(handler, event, {})
    assert res == "success"

    # 2. When allowed_telegram_ids is set to {12345} and user is 999 -> reject
    monkeypatch.setattr(mock_settings, "TELEGRAM_ALLOWED_USER_IDS", "12345")
    handler.reset_mock()
    res_blocked = await middleware(handler, event, {})
    assert res_blocked is None
    handler.assert_not_called()

    # 3. When allowed_telegram_ids is set to {12345} and user is 12345 -> allow
    event.from_user.id = 12345
    handler.reset_mock()
    res_allowed = await middleware(handler, event, {})
    assert res_allowed == "success"
    handler.assert_called_once()


def test_normalize_phone_number():
    assert normalize_phone_number("+380501234567") == "+380501234567"
    assert normalize_phone_number("0501234567") == "+380501234567"
    assert normalize_phone_number("050 123 45 67") == "+380501234567"
    assert normalize_phone_number("+38 (067) 987-65-43") == "+380679876543"
    assert normalize_phone_number("380501234567") == "+380501234567"
    assert normalize_phone_number("") == ""
    assert normalize_phone_number(None) == ""


def test_main_menu_keyboard():
    kb = main_menu_keyboard()
    all_texts = [btn.text for row in kb.keyboard for btn in row]
    assert "📦 Замовлення" in all_texts
    assert "➕ Створити замовлення" in all_texts
    assert "👥 Клієнти" in all_texts
    assert "🔄 Оновити / Назад" in all_texts


def test_order_categories_keyboard():
    counts = {"active": 4, "delivered": 15, "cancelled": 2, "all": 21}
    kb = order_categories_keyboard(counts)
    all_buttons = [btn for row in kb.inline_keyboard for btn in row]
    btn_texts = [b.text for b in all_buttons]
    callbacks = [b.callback_data for b in all_buttons if b.callback_data]

    assert "🟢 Активні (4)" in btn_texts
    assert "✅ Виконані (15)" in btn_texts
    assert "❌ Скасовані (2)" in btn_texts
    assert "📋 Всі замовлення (21)" in btn_texts
    assert "🏠 Головне меню" in btn_texts
    assert "🔄 Оновити" in btn_texts

    assert "ord_cat:active:1" in callbacks
    assert "ord_cat:delivered:1" in callbacks
    assert "ord_cat:cancelled:1" in callbacks
    assert "ord_cat:all:1" in callbacks
    assert "ord_nav:home" in callbacks


def test_order_list_keyboard_pagination():
    customer = Customer(id=1, name="Олена Петренко", phone="+380501234567", address="м. Луцьк")
    order1 = Order(id=10, customer=customer, customer_id=1, quantity=Decimal("5.00"), unit_price=Decimal("200.00"), delivery_price=Decimal("100.00"), total_amount=Decimal("1100.00"), delivery_address="вул. Миру 1", status="new")
    order2 = Order(id=11, customer=customer, customer_id=1, quantity=Decimal("10.00"), unit_price=Decimal("200.00"), delivery_price=Decimal("100.00"), total_amount=Decimal("2100.00"), delivery_address="вул. Миру 2", status="planned")

    # Middle page of 3
    kb = order_list_keyboard(orders=[order1, order2], category="active", page=2, total_pages=3)
    all_buttons = [btn for row in kb.inline_keyboard for btn in row]
    callbacks = [b.callback_data for b in all_buttons if b.callback_data]

    assert "ord_det:10:active:2" in callbacks
    assert "ord_det:11:active:2" in callbacks
    assert "ord_pg:active:1" in callbacks  # Prev page
    assert "ord_pg:active:3" in callbacks  # Next page
    assert "ord_nav:categories" in callbacks
    assert "ord_nav:home" in callbacks


def test_order_card_manual_amount_and_all_fields():
    customer = Customer(
        id=7,
        name="Марія Сидоренко",
        phone="+380998887766",
        address="м. Ковель, вул. Незалежності 15",
    )
    order = Order(
        id=99,
        customer_id=7,
        customer=customer,
        product_name=DEFAULT_PRODUCT_NAME,
        quantity=Decimal("12.50"),
        unit_price=Decimal("180.00"),
        delivery_price_per_km=Decimal("25.00"),
        delivery_price=Decimal("500.00"),
        calculated_total_amount=Decimal("2750.00"),
        total_amount=Decimal("2600.00"),
        is_total_manual=True,
        distance_km=Decimal("20.00"),
        delivery_address="м. Ковель, вул. Незалежності 15",
        status=OrderStatus.PLANNED.value,
        notes="Термінова доставка",
    )

    card = render_order_card(order)
    assert "Замовлення #99" in card
    assert "Марія Сидоренко" in card
    assert "+380998887766" in card
    assert "м. Ковель, вул. Незалежності 15" in card
    assert "12.5" in card  # Quantity
    assert "180.00" in card  # Unit price
    assert "20.00 км" in card  # Distance
    assert "25.00 грн/км" in card  # Price per km
    assert "500.00" in card  # Delivery price
    assert "2600.00" in card  # Final total amount
    assert "Встановлено вручну" in card  # Manual indication!
    assert "Заплановано" in card  # Status label


def test_order_actions_keyboard_with_call_button():
    kb = order_actions_keyboard(
        order_id=55,
        order_status=OrderStatus.NEW.value,
        customer_phone="+380991112233",
        back_category="active",
        back_page=2,
    )
    all_buttons = [btn for row in kb.inline_keyboard for btn in row]
    btn_texts = [b.text for b in all_buttons]
    callbacks = [b.callback_data for b in all_buttons if b.callback_data]

    assert "📞 Зателефонувати клієнту" in btn_texts
    assert "ord_call:55" in callbacks
    assert "⬅️ Назад" in btn_texts
    assert "ord_pg:active:2" in callbacks
    assert "🏠 Головне меню" in btn_texts
    assert "ord_nav:home" in callbacks


def test_render_order_list_text():
    customer = Customer(id=1, name="Сергій", phone="+380501112233", address="м. Луцьк, вул. Дружби 5")
    order = Order(
        id=15,
        customer=customer,
        customer_id=1,
        quantity=Decimal("8.00"),
        unit_price=Decimal("200.00"),
        delivery_price=Decimal("200.00"),
        total_amount=Decimal("1800.00"),
        delivery_address="м. Луцьк, вул. Дружби 5",
        status=OrderStatus.IN_DELIVERY.value,
    )
    text = render_order_list_text([order], "🟢 Активні", page=1, total_pages=1, total_count=1)
    assert "🟢 Активні" in text
    assert "#15" in text
    assert "Сергій" in text
    assert "8.00 т" in text
    assert "м. Луцьк, вул. Дружби 5" in text
    assert "1800.00 грн" in text
    assert "В дорозі" in text


@pytest.mark.asyncio
async def test_cb_call_customer():
    customer = Customer(id=1, name="Василь", phone="050 123-45-67")
    order = Order(id=77, customer=customer, customer_id=1)

    call = MagicMock()
    call.data = "ord_call:77"
    call.answer = AsyncMock()
    call.message = MagicMock()
    call.message.answer_contact = AsyncMock()

    with patch("app.bot.handlers.orders.order_service.get_order", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = order
        await cb_call_customer(call)

    call.answer.assert_called_once()
    call.message.answer_contact.assert_called_once_with(
        phone_number="+380501234567",
        first_name="Василь",
    )


@pytest.mark.asyncio
async def test_cb_order_details():
    customer = Customer(id=2, name="Наталія", phone="+380998889900", address="вул. Садова 3")
    order = Order(
        id=88,
        customer=customer,
        customer_id=2,
        product_name=DEFAULT_PRODUCT_NAME,
        quantity=Decimal("5.00"),
        unit_price=Decimal("200.00"),
        delivery_price=Decimal("100.00"),
        total_amount=Decimal("1100.00"),
        delivery_address="вул. Садова 3",
        status=OrderStatus.NEW.value,
    )

    call = MagicMock()
    call.data = "ord_det:88:active:1"
    call.answer = AsyncMock()
    call.message = MagicMock()
    call.message.edit_text = AsyncMock()

    with patch("app.bot.handlers.orders.order_service.get_order", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = order
        await cb_order_details(call)

    call.answer.assert_called_once()
    call.message.edit_text.assert_called_once()
    edit_args = call.message.edit_text.call_args[0]
    assert "Замовлення #88" in edit_args[0]
    assert "Наталія" in edit_args[0]
    kb = call.message.edit_text.call_args[1]["reply_markup"]
    btn_callbacks = [b.callback_data for row in kb.inline_keyboard for b in row if b.callback_data]
    assert "ord_call:88" in btn_callbacks
    assert "ord_pg:active:1" in btn_callbacks

