import json
import logging
from typing import Any, Dict, Optional
from aiogram import Bot, Router
from aiogram.types import CallbackQuery, Update

from app.bot.widgets.service import widget_service
from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models.order import OrderStatus
from app.services.customer_service import customer_service
from app.services.navigation import navigation_service
from app.services.order_service import order_service

logger = logging.getLogger(__name__)

router = Router(name="widgets")


def extract_widget_query(update: Update) -> Optional[Dict[str, Any]]:
    """
    Extracts widget_query payload from an aiogram Update.
    """
    wq = getattr(update, "widget_query", None)
    if wq:
        return wq
    extra = getattr(update, "__pydantic_extra__", None)
    if extra and "widget_query" in extra:
        return extra["widget_query"]
    return None


async def process_widget_action(
    query_id: str,
    user_id: int,
    raw_data: str,
    message_obj: Optional[Dict[str, Any]],
    bot: Bot,
):
    """
    Core business handler for interactive HTML Widget actions.
    """
    chat_id = message_obj.get("chat", {}).get("id") if message_obj else user_id
    message_id = message_obj.get("message_id") if message_obj else None

    # 1. Access Control Check
    settings = get_settings()
    allowed_ids = settings.allowed_telegram_ids
    if allowed_ids and user_id not in allowed_ids:
        logger.warning(f"Unauthorized widget action by user_id={user_id}")
        await widget_service.answer_query(
            bot=bot,
            widget_query_id=query_id,
            text="⛔️ У вас немає доступу до цієї системи CRM.",
            show_alert=True,
        )
        return

    # 2. Parse payload
    try:
        if raw_data.startswith("{"):
            payload = json.loads(raw_data)
        else:
            payload = {"action": raw_data}
    except Exception:
        payload = {"action": raw_data}

    action = payload.get("action", "")
    logger.info(f"Processing widget query action={action} user_id={user_id}")

    try:
        # Route actions
        if action in ["switch_tab", "filter_orders", "change_period", "refresh"]:
            tab = payload.get("tab", "orders")
            order_filter = payload.get("filter", "all")
            period = payload.get("period", "month")
            query = payload.get("query", "")

            async with AsyncSessionLocal() as session:
                new_state = await widget_service.build_dashboard_state(
                    session=session,
                    tab=tab,
                    order_filter=order_filter,
                    period=period,
                    search_query=query,
                )

            if message_id:
                await widget_service.update_widget(
                    bot=bot,
                    chat_id=chat_id,
                    message_id=message_id,
                    new_state=new_state,
                )
            await widget_service.answer_query(bot=bot, widget_query_id=query_id)

        elif action == "search_customers":
            query = payload.get("query", "")
            async with AsyncSessionLocal() as session:
                new_state = await widget_service.build_dashboard_state(
                    session=session,
                    tab="customers",
                    search_query=query,
                )
            if message_id:
                await widget_service.update_widget(
                    bot=bot,
                    chat_id=chat_id,
                    message_id=message_id,
                    new_state=new_state,
                )
            await widget_service.answer_query(bot=bot, widget_query_id=query_id)

        elif action in ["change_order_status", "order_change_status"]:
            order_id = int(payload.get("order_id", 0))
            new_status = payload.get("status")

            async with AsyncSessionLocal() as session:
                if new_status == OrderStatus.PLANNED.value:
                    await order_service.update_order_status(session, order_id, OrderStatus.PLANNED)
                    alert_text = f"🗓 Замовлення #{order_id} заплановано до виїзду"
                elif new_status == OrderStatus.IN_DELIVERY.value:
                    await order_service.start_delivery(session, order_id)
                    alert_text = f"🚚 Замовлення #{order_id} переведено в статус 'В дорозі'"
                elif new_status == OrderStatus.DELIVERED.value:
                    await order_service.complete_delivery(session, order_id)
                    alert_text = f"✅ Замовлення #{order_id} позначено як доставлене!"
                elif new_status == OrderStatus.CANCELLED.value:
                    await order_service.cancel_order(session, order_id, notes="Скасовано з віджета")
                    alert_text = f"❌ Замовлення #{order_id} скасовано"
                else:
                    alert_text = "Статус оновлено"

            if message_id:
                # If this came from order card widget, update order card
                if action == "order_change_status":
                    await widget_service.update_order_card(
                        bot=bot,
                        chat_id=chat_id,
                        message_id=message_id,
                        order_id=order_id,
                    )
                else:
                    # Otherwise update dashboard widget
                    async with AsyncSessionLocal() as session:
                        new_state = await widget_service.build_dashboard_state(
                            session=session,
                            tab=payload.get("tab", "deliveries"),
                        )
                    await widget_service.update_widget(
                        bot=bot,
                        chat_id=chat_id,
                        message_id=message_id,
                        new_state=new_state,
                    )

            await widget_service.answer_query(
                bot=bot,
                widget_query_id=query_id,
                text=alert_text,
                show_alert=False,
            )

        elif action == "calendar_toggle_blocked":
            target_date = payload.get("date", "")
            is_now_blocked = widget_service.toggle_blocked_date(target_date)
            alert_text = (
                f"⛔️ Дату {target_date} позначено як недоступну для доставки"
                if is_now_blocked
                else f"🟢 Дату {target_date} знову відкрито для доставок"
            )

            if message_id:
                async with AsyncSessionLocal() as session:
                    new_state = await widget_service.build_dashboard_state(
                        session=session,
                        tab="calendar",
                    )
                await widget_service.update_widget(
                    bot=bot,
                    chat_id=chat_id,
                    message_id=message_id,
                    new_state=new_state,
                )

            await widget_service.answer_query(
                bot=bot,
                widget_query_id=query_id,
                text=alert_text,
                show_alert=False,
            )

        elif action == "refresh_order":
            order_id = int(payload.get("order_id", 0))
            if message_id and order_id:
                await widget_service.update_order_card(
                    bot=bot,
                    chat_id=chat_id,
                    message_id=message_id,
                    order_id=order_id,
                )
            await widget_service.answer_query(bot=bot, widget_query_id=query_id)

        elif action == "open_order":
            order_id = int(payload.get("order_id", 0))
            sent_widget = await widget_service.send_order_card(bot=bot, chat_id=chat_id, order_id=order_id)
            if not sent_widget:
                async with AsyncSessionLocal() as session:
                    order = await order_service.get_order(session, order_id)
                if order:
                    info = (
                        f"📦 **Замовлення #{order.id}** ({order.status})\n"
                        f"👤 {order.customer.name if order.customer else 'Клієнт'} (📞 `{order.customer.phone if order.customer else ''}`)\n"
                        f"🧱 {order.quantity} т торфобрикету | Разом: **{order.total_amount} грн**\n"
                        f"🏠 {order.delivery_address}\n\n"
                        f"👉 Повна картка: `/order_{order.id}`"
                    )
                    await bot.send_message(chat_id=chat_id, text=info, parse_mode="Markdown")
            await widget_service.answer_query(bot=bot, widget_query_id=query_id)

        elif action in ["open_customer", "order_open_customer"]:
            order_id = payload.get("order_id")
            cust_id = payload.get("customer_id")
            if not cust_id and order_id:
                async with AsyncSessionLocal() as session:
                    order = await order_service.get_order(session, int(order_id))
                    if order:
                        cust_id = order.customer_id

            if cust_id:
                sent_widget = await widget_service.send_customer_card(
                    bot=bot,
                    chat_id=chat_id,
                    customer_id=int(cust_id),
                )
                if not sent_widget:
                    async with AsyncSessionLocal() as session:
                        cust = await customer_service.get_customer(session, int(cust_id))
                    if cust:
                        info = (
                            f"👤 **{cust.name}** (ID: `{cust.id}`)\n"
                            f"📞 `{cust.phone}`\n"
                            f"🏠 {cust.address}\n"
                            f"Всього замовлень: {len(cust.orders)}\n\n"
                            f"👉 Пошук клієнта: `/customers {cust.phone}`"
                        )
                        await bot.send_message(chat_id=chat_id, text=info, parse_mode="Markdown")
            await widget_service.answer_query(bot=bot, widget_query_id=query_id)

        elif action == "refresh_customer":
            cust_id = payload.get("customer_id")
            if message_id and cust_id:
                await widget_service.update_customer_card(
                    bot=bot,
                    chat_id=chat_id,
                    message_id=message_id,
                    customer_id=int(cust_id),
                )
            await widget_service.answer_query(bot=bot, widget_query_id=query_id)

        elif action == "cust_new_order":
            cust_id = payload.get("customer_id")
            sent_widget = await widget_service.send_order_create(
                bot=bot,
                chat_id=chat_id,
                selected_customer_id=int(cust_id) if cust_id else None,
            )
            if not sent_widget:
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"➕ Створення замовлення для клієнта #{cust_id}:\nСкористайтесь командою: /new_order",
                )
            await widget_service.answer_query(bot=bot, widget_query_id=query_id)

        elif action == "submit_new_order":
            from decimal import Decimal
            from datetime import datetime
            from app.schemas.order import OrderCreate

            cust_id = int(payload.get("customer_id", 0))
            quantity = Decimal(str(payload.get("quantity", "10")))
            unit_price = Decimal(str(payload.get("unit_price", "200")))
            delivery_price = Decimal(str(payload.get("delivery_price", "0")))
            delivery_address = payload.get("delivery_address", "")
            notes = payload.get("notes") or None

            order_date_raw = payload.get("order_date")
            order_date = None
            if order_date_raw:
                try:
                    order_date = datetime.strptime(order_date_raw, "%Y-%m-%d").date()
                except Exception:
                    order_date = None

            order_in = OrderCreate(
                customer_id=cust_id,
                quantity=quantity,
                unit_price=unit_price,
                delivery_price=delivery_price,
                delivery_address=delivery_address if delivery_address else None,
                order_date=order_date,
                notes=notes,
            )

            async with AsyncSessionLocal() as session:
                new_order = await order_service.create_order(session, order_in)

            await widget_service.answer_query(
                bot=bot,
                widget_query_id=query_id,
                text=f"✅ Замовлення #{new_order.id} успішно створено!",
                show_alert=True,
            )

            # Відкриваємо інтерактивну картку створеного замовлення
            await widget_service.send_order_card(
                bot=bot,
                chat_id=chat_id,
                order_id=new_order.id,
            )

        elif action == "cancel_order_create":
            await widget_service.answer_query(
                bot=bot,
                widget_query_id=query_id,
                text="Створення замовлення скасовано.",
                show_alert=False,
            )

        elif action == "trigger_new_customer":
            await bot.send_message(
                chat_id=chat_id,
                text="➕ Для створення нового клієнта скористайтесь командою: /new_customer",
            )
            await widget_service.answer_query(bot=bot, widget_query_id=query_id)

        else:
            await widget_service.answer_query(bot=bot, widget_query_id=query_id)

    except Exception as e:
        logger.error(f"Error handling widget action '{action}': {e}", exc_info=True)
        await widget_service.answer_query(
            bot=bot,
            widget_query_id=query_id,
            text=f"Помилка обробки: {e}",
            show_alert=True,
        )


async def handle_widget_update(update: Update, bot: Bot):
    """
    Handler registered on dp.update to capture Bot API 10.4 widget_query updates.
    """
    wq = extract_widget_query(update)
    if not wq:
        return

    query_id = wq.get("id")
    from_user = wq.get("from", {})
    user_id = from_user.get("id")
    raw_data = wq.get("data", "")
    message_obj = wq.get("message")

    await process_widget_action(
        query_id=query_id,
        user_id=user_id,
        raw_data=raw_data,
        message_obj=message_obj,
        bot=bot,
    )
