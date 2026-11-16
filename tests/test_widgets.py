import json
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from aiogram.types import Update

from app.bot.bot import create_bot_and_dispatcher
from app.bot.handlers.widgets import extract_widget_query, process_widget_action
from app.bot.widgets.methods import AnswerWidgetQuery, EditMessageWidgetData, SendWidget
from app.bot.widgets.service import widget_service
from app.bot.widgets.templates.dashboard import build_dashboard_html
from app.bot.widgets.templates.order_card import build_order_card_html
from app.bot.widgets.templates.customer_card import build_customer_card_html
from app.bot.widgets.templates.order_create import build_order_create_html


def test_dashboard_html_generation():
    html = build_dashboard_html()
    assert "<!DOCTYPE html>" in html
    assert "Peat CRM" in html
    assert "tab-btn-orders" in html
    assert "tab-btn-customers" in html
    assert "tab-btn-deliveries" in html
    assert "tab-btn-calendar" in html
    assert "tab-btn-stats" in html
    assert "TelegramWidget" in html
    assert "chatDataChanged" in html
    assert "toggleDayBlocked" in html
    assert "crm-progress-bar" in html

    # Size limitation check (Telegram Bot API 10.4 constraint)
    size_bytes = len(html.encode("utf-8"))
    assert size_bytes < 32768, f"HTML Widget exceeds 32KB limit: {size_bytes} bytes"


def test_order_card_html_generation():
    html = build_order_card_html()
    assert "<!DOCTYPE html>" in html
    assert "order-stepper" in html
    assert "step-new" in html
    assert "step-planned" in html
    assert "step-in_delivery" in html
    assert "step-delivered" in html
    assert "confirm-modal" in html
    assert "openWaze" in html
    assert "TelegramWidget" in html
    assert "chatDataChanged" in html

    # Size limitation check (Telegram Bot API 10.4 constraint <= 32KB)
    size_bytes = len(html.encode("utf-8"))
    assert size_bytes < 32768, f"Order Card HTML Widget exceeds 32KB limit: {size_bytes} bytes"


def test_customer_card_html_generation():
    html = build_customer_card_html()
    assert "<!DOCTYPE html>" in html
    assert "cust-name-title" in html
    assert "cust-orders-count" in html
    assert "cust-total-spent" in html
    assert "cust-phone" in html
    assert "cust-address" in html
    assert "history-container" in html
    assert "TelegramWidget" in html
    assert "chatDataChanged" in html

    # Size limitation check (Telegram Bot API 10.4 constraint <= 32KB)
    size_bytes = len(html.encode("utf-8"))
    assert size_bytes < 32768, f"Customer Card HTML Widget exceeds 32KB limit: {size_bytes} bytes"


def test_order_create_html_generation():
    html = build_order_create_html()
    assert "<!DOCTYPE html>" in html
    assert "cust-select" in html
    assert "qty-input" in html
    assert "price-input" in html
    assert "delivery-input" in html
    assert "calc-summary" in html
    assert "sum-total" in html
    assert "submitOrder" in html
    assert "TelegramWidget" in html

    # Size limitation check (Telegram Bot API 10.4 constraint <= 32KB)
    size_bytes = len(html.encode("utf-8"))
    assert size_bytes < 32768, f"Order Create HTML Widget exceeds 32KB limit: {size_bytes} bytes"


def test_calendar_toggle_blocked():
    test_date = "2026-12-01"
    assert widget_service.toggle_blocked_date(test_date) is True
    assert test_date in widget_service.blocked_dates
    assert widget_service.toggle_blocked_date(test_date) is False
    assert test_date not in widget_service.blocked_dates


def test_platform_compatibility_and_viewports():
    widgets = [
        build_dashboard_html(),
        build_order_card_html(),
        build_customer_card_html(),
        build_order_create_html(),
    ]
    for w in widgets:
        # 1. Viewport for iOS / Android mobile
        assert 'name="viewport"' in w
        assert "width=device-width" in w
        assert "user-scalable=no" in w

        # 2. Touch highlights and user-select for iOS/Android
        assert "-webkit-tap-highlight-color" in w
        assert "user-select: none" in w

        # 3. Theme custom properties for dark & light Telegram themes
        assert "--tg-theme-bg-color" in w
        assert "--tg-theme-text-color" in w

        # 4. TelegramWidget object integration
        assert "TelegramWidget" in w
        assert "chatDataChanged" in w


def test_widget_methods_serialization():
    send_w = SendWidget(
        chat_id=12345,
        html="<div>test</div>",
        chat_data=json.dumps({"test": 1}),
    )
    dumped = send_w.model_dump(exclude_none=True)
    assert dumped["chat_id"] == 12345
    assert dumped["html"] == "<div>test</div>"
    assert "chat_data" in dumped

    ans_w = AnswerWidgetQuery(
        widget_query_id="wq_123",
        text="Готово",
        show_alert=False,
    )
    assert ans_w.widget_query_id == "wq_123"

    edit_w = EditMessageWidgetData(
        chat_id=12345,
        message_id=99,
        chat_data="{}",
    )
    assert edit_w.chat_id == 12345
    assert edit_w.message_id == 99


def test_extract_widget_query():
    raw_update_data = {
        "update_id": 100,
        "widget_query": {
            "id": "wq_abc",
            "from": {"id": 42, "is_bot": False, "first_name": "Олександр"},
            "data": '{"action":"switch_tab","tab":"stats"}',
        },
    }
    update = Update.model_validate(raw_update_data)
    wq = extract_widget_query(update)
    assert wq is not None
    assert wq["id"] == "wq_abc"
    assert wq["from"]["id"] == 42
    assert "switch_tab" in wq["data"]


def test_bot_dispatcher_has_widget_router():
    bot, dp = create_bot_and_dispatcher()
    router_names = [r.name for r in dp.sub_routers]
    assert "widgets" in router_names
    assert "common" in router_names
    assert "customers" in router_names
    assert "orders" in router_names


def test_process_widget_action_dispatch():
    # Verify mock processing of widget query
    bot = AsyncMock()
    mock_state = {
        "activeTab": "customers",
        "orderFilter": "all",
        "orders": [],
        "customers": [{"id": 1, "name": "Тест"}],
        "deliveries": [],
        "calendar_days": [],
        "stats": {},
    }

    with patch.object(widget_service, "build_dashboard_state", AsyncMock(return_value=mock_state)), \
         patch.object(widget_service, "update_widget", AsyncMock(return_value=True)), \
         patch.object(widget_service, "answer_query", AsyncMock(return_value=True)):

        import asyncio
        asyncio.run(
            process_widget_action(
                query_id="wq_test",
                user_id=12345,
                raw_data=json.dumps({"action": "switch_tab", "tab": "customers"}),
                message_obj={"message_id": 10, "chat": {"id": 12345}},
                bot=bot,
            )
        )
