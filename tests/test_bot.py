from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
import pytest

from app.bot.bot import AccessControlMiddleware
from app.bot.handlers.orders import render_order_card
from app.bot.keyboards import (
    cancel_or_skip_keyboard,
    customer_actions_keyboard,
    order_actions_keyboard,
)
from app.models.customer import Customer
from app.models.order import Order, OrderStatus


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
    del_texts = [b.text for row in kb_del.inline_keyboard for btn in row]
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


def test_render_order_card():
    customer = Customer(
        id=5,
        name="Тарас Григорович",
        phone="+380501112233",
        address="смт Маневичі",
    )
    order = Order(
        id=42,
        customer_id=5,
        customer=customer,
        product_name="Торф верховий",
        quantity=Decimal("15.00"),
        unit_price=Decimal("900.00"),
        total_amount=Decimal("13500.00"),
        delivery_address="смт Маневичі, вул. Шкільна 2",
        delivery_latitude=Decimal("51.298100"),
        delivery_longitude=Decimal("25.553200"),
        status=OrderStatus.NEW.value,
        notes="Вивантажити за будинком",
    )

    card = render_order_card(order)
    assert "Замовлення #42" in card
    assert "Тарас Григорович" in card
    assert "+380501112233" in card
    assert "13500.00" in card
    assert "51.298100, 25.553200" in card
    assert "Вивантажити за будинком" in card


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
