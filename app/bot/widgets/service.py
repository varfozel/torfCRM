import json
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from aiogram import Bot
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.widgets.methods import AnswerWidgetQuery, EditMessageWidgetData, SendWidget
from app.bot.widgets.templates.dashboard import build_dashboard_html
from app.bot.widgets.templates.order_card import build_order_card_html
from app.bot.widgets.templates.customer_card import build_customer_card_html
from app.bot.widgets.templates.order_create import build_order_create_html
from app.database import AsyncSessionLocal
from app.models.customer import Customer
from app.models.order import Order, OrderStatus
from app.services.analytics_service import AnalyticsService
from app.services.customer_service import customer_service
from app.services.navigation import navigation_service
from app.services.order_service import order_service

logger = logging.getLogger(__name__)


def decimal_serializer(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (datetime,)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


class WidgetService:
    """
    Backend service powering HTML Widgets in Peat CRM.
    Integrates DB operations, business logic, and widget state delivery.
    """

    def __init__(self):
        self.analytics = AnalyticsService()
        self.orders = order_service
        self.customers = customer_service
        self.nav = navigation_service
        self.blocked_dates: set[str] = set()
        self._dashboard_html = build_dashboard_html()
        self._order_card_html = build_order_card_html()
        self._customer_card_html = build_customer_card_html()
        self._order_create_html = build_order_create_html()

    async def build_dashboard_state(
        self,
        session: AsyncSession,
        tab: str = "orders",
        order_filter: str = "all",
        period: str = "month",
        search_query: str = "",
    ) -> Dict[str, Any]:
        """
        Builds a compact JSON-serializable state dictionary for the dashboard widget.
        """
        now = datetime.now(timezone.utc)
        today_date = now.date()

        # 1. Orders section data
        status_filter_val = None
        if order_filter == "new":
            status_filter_val = OrderStatus.NEW.value
        elif order_filter == "in_work":
            # Will be filtered below for in_delivery and planned
            status_filter_val = None
        elif order_filter == "delivered":
            status_filter_val = OrderStatus.DELIVERED.value
        elif order_filter == "cancelled":
            status_filter_val = OrderStatus.CANCELLED.value

        raw_orders = await self.orders.list_orders(
            session=session,
            status=status_filter_val,
            limit=12,
        )

        formatted_orders = []
        for o in raw_orders:
            if order_filter == "in_work" and o.status not in [OrderStatus.PLANNED.value, OrderStatus.IN_DELIVERY.value]:
                continue
            formatted_orders.append({
                "id": o.id,
                "customer_name": o.customer.name if o.customer else f"ID {o.customer_id}",
                "customer_phone": o.customer.phone if o.customer else "",
                "quantity": float(o.quantity),
                "delivery_price": float(o.delivery_price),
                "total_amount": float(o.total_amount),
                "status": o.status,
                "delivery_address": o.delivery_address,
                "created_at": o.created_at.strftime("%d.%m %H:%M"),
            })

        # 2. Customers section data
        raw_customers = await self.customers.search_customers(
            session=session,
            query=search_query,
            limit=10,
        )
        formatted_customers = []
        for c in raw_customers:
            spent = sum(
                (o.total_amount for o in c.orders if o.status != OrderStatus.CANCELLED.value),
                Decimal("0.00"),
            )
            formatted_customers.append({
                "id": c.id,
                "name": c.name,
                "phone": c.phone,
                "address": c.address,
                "orders_count": len(c.orders),
                "total_spent": float(spent),
            })

        # 3. Deliveries section data
        # Fetch deliveries for today or currently active in_delivery
        deliv_stmt = (
            select(Order)
            .where(
                (Order.status == OrderStatus.IN_DELIVERY.value)
                | (Order.order_date == today_date)
            )
            .order_by(Order.created_at.desc())
            .limit(10)
        )
        deliv_res = (await session.execute(deliv_stmt)).scalars().all()
        formatted_deliveries = []
        for d in deliv_res:
            waze = self.nav.generate_waze_url(
                d.delivery_latitude, d.delivery_longitude, d.delivery_address
            )
            formatted_deliveries.append({
                "id": d.id,
                "customer_name": d.customer.name if d.customer else f"ID {d.customer_id}",
                "customer_phone": d.customer.phone if d.customer else "",
                "quantity": float(d.quantity),
                "total_amount": float(d.total_amount),
                "status": d.status,
                "delivery_address": d.delivery_address,
                "waze_url": waze,
            })

        # 4. Calendar section data (next 7 days)
        calendar_days = []
        for i in range(7):
            d = today_date + timedelta(days=i)
            # count orders on this date
            day_orders_stmt = select(
                func.count(Order.id),
                func.coalesce(func.sum(Order.quantity), 0),
            ).where(Order.order_date == d, Order.status != OrderStatus.CANCELLED.value)
            day_res = (await session.execute(day_orders_stmt)).one()
            cnt = int(day_res[0])
            tons = float(Decimal(str(day_res[1])).quantize(Decimal("0.1")))
            is_today = (i == 0)
            date_label = d.strftime("%d.%m (%a)")

            is_blocked = (d.isoformat() in self.blocked_dates)

            # Fetch orders for this day
            day_orders_query = (
                select(Order)
                .where(Order.order_date == d, Order.status != OrderStatus.CANCELLED.value)
                .limit(3)
            )
            day_orders_res = (await session.execute(day_orders_query)).scalars().all()
            day_orders_list = [
                {
                    "id": o.id,
                    "customer_name": o.customer.name if o.customer else f"ID {o.customer_id}",
                    "quantity": float(o.quantity),
                    "status": o.status,
                }
                for o in day_orders_res
            ]

            if is_blocked:
                deliv_text = "⛔️ День позначено як недоступний для виїзду"
            elif cnt >= 3:
                deliv_text = f"🔥 Високе завантаження: {cnt} рейсів ({tons} т)"
            elif cnt > 0:
                deliv_text = f"Заплановано рейсів: {cnt} ({tons} т)"
            else:
                deliv_text = "Вільний день для нових замовлень"

            calendar_days.append({
                "date": d.isoformat(),
                "date_label": date_label,
                "is_today": is_today,
                "is_blocked": is_blocked,
                "orders_count": cnt,
                "tons": tons,
                "deliveries_text": deliv_text,
                "orders": day_orders_list,
            })

        # 5. Stats section data
        dash_data = await self.analytics.get_dashboard_data(session=session, period=period)
        in_work_count = sum(
            item["count"] for item in dash_data.get("status_distribution", [])
            if item["status"] in [OrderStatus.NEW.value, OrderStatus.PLANNED.value, OrderStatus.IN_DELIVERY.value]
        )

        status_breakdown = [
            {
                "status": item["status"],
                "count": item["count"],
                "total_sum": float(item["total_sum"]),
            }
            for item in dash_data.get("status_distribution", [])
        ]

        stats = {
            "revenue": float(dash_data.get("period_revenue", 0.0)),
            "quantity": float(dash_data.get("period_quantity", 0.0)),
            "orders_count": dash_data.get("period_orders_count", 0),
            "in_work_count": in_work_count,
            "total_customers": dash_data.get("total_customers", 0),
            "today_deliveries_count": dash_data.get("today_deliveries_count", 0),
            "warehouse_address": self.nav.warehouse_info.get("address", ""),
            "status_breakdown": status_breakdown,
        }

        return {
            "activeTab": tab,
            "orderFilter": order_filter,
            "period": period,
            "today_deliveries_count": stats["today_deliveries_count"],
            "orders": formatted_orders,
            "customers": formatted_customers,
            "deliveries": formatted_deliveries,
            "calendar_days": calendar_days,
            "stats": stats,
        }

    def toggle_blocked_date(self, date_str: str) -> bool:
        """
        Toggles date as blocked/unavailable for delivery. Returns True if now blocked, False if unblocked.
        """
        if date_str in self.blocked_dates:
            self.blocked_dates.remove(date_str)
            return False
        else:
            self.blocked_dates.add(date_str)
            return True

    async def build_order_card_state(
        self,
        session: AsyncSession,
        order_id: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Builds payload for a single order interactive card widget.
        """
        order = await self.orders.get_order(session, order_id)
        if not order:
            return None

        waze = self.nav.generate_waze_url(
            order.delivery_latitude, order.delivery_longitude, order.delivery_address
        )
        gmaps = self.nav.generate_google_maps_url(
            order.delivery_latitude, order.delivery_longitude, order.delivery_address
        )

        return {
            "order": {
                "id": order.id,
                "customer_id": order.customer_id,
                "customer_name": order.customer.name if order.customer else f"ID {order.customer_id}",
                "customer_phone": order.customer.phone if order.customer else "—",
                "product_name": order.product_name,
                "quantity": float(order.quantity),
                "unit_price": float(order.unit_price),
                "product_total": float(order.product_total),
                "delivery_price": float(order.delivery_price),
                "total_amount": float(order.total_amount),
                "delivery_address": order.delivery_address,
                "delivery_latitude": float(order.delivery_latitude) if order.delivery_latitude else None,
                "delivery_longitude": float(order.delivery_longitude) if order.delivery_longitude else None,
                "order_date": order.order_date.isoformat() if order.order_date else "",
                "status": order.status,
                "notes": order.notes or "",
                "delivery_started_at": order.delivery_started_at.strftime("%d.%m.%Y %H:%M") if order.delivery_started_at else None,
                "delivery_completed_at": order.delivery_completed_at.strftime("%d.%m.%Y %H:%M") if order.delivery_completed_at else None,
                "waze_url": waze,
                "google_maps_url": gmaps,
            }
        }

    async def send_order_card(
        self,
        bot: Bot,
        chat_id: int,
        order_id: int,
    ) -> bool:
        """
        Sends the interactive HTML Widget card for a specific order.
        """
        async with AsyncSessionLocal() as session:
            state = await self.build_order_card_state(session, order_id)

        if not state:
            return False

        chat_data_str = json.dumps(state, default=decimal_serializer, ensure_ascii=False)

        try:
            method = SendWidget(
                chat_id=chat_id,
                html=self._order_card_html,
                chat_data=chat_data_str,
                caption=f"📦 Замовлення #{order_id} — Інтерактивна картка",
                protect_content=True,
            )
            await bot(method)
            return True
        except Exception as e:
            logger.warning(f"Failed to send order widget via sendWidget ({e}). Fallback to standard message.")
            return False

    async def update_order_card(
        self,
        bot: Bot,
        chat_id: int,
        message_id: int,
        order_id: int,
    ) -> bool:
        """
        Updates the chat_data of an existing order card widget.
        """
        async with AsyncSessionLocal() as session:
            state = await self.build_order_card_state(session, order_id)

        if not state:
            return False

        return await self.update_widget(
            bot=bot,
            chat_id=chat_id,
            message_id=message_id,
            new_state=state,
        )

    async def build_customer_card_state(
        self,
        session: AsyncSession,
        customer_id: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Builds payload for a single customer interactive card widget.
        """
        customer = await self.customers.get_customer(session, customer_id)
        if not customer:
            return None

        map_url = self.nav.generate_google_maps_url(
            customer.latitude, customer.longitude, customer.address
        )

        spent = sum(
            (o.total_amount for o in customer.orders if o.status != OrderStatus.CANCELLED.value),
            Decimal("0.00"),
        )

        orders_history = []
        for o in customer.orders[:10]:
            orders_history.append({
                "id": o.id,
                "quantity": float(o.quantity),
                "total_amount": float(o.total_amount),
                "status": o.status,
                "order_date": o.order_date.strftime("%d.%m.%Y") if o.order_date else "",
            })

        return {
            "customer": {
                "id": customer.id,
                "name": customer.name,
                "phone": customer.phone,
                "address": customer.address,
                "latitude": float(customer.latitude) if customer.latitude else None,
                "longitude": float(customer.longitude) if customer.longitude else None,
                "notes": customer.notes or "",
                "orders_count": len(customer.orders),
                "total_spent": float(spent),
                "map_url": map_url,
                "orders": orders_history,
            }
        }

    async def send_customer_card(
        self,
        bot: Bot,
        chat_id: int,
        customer_id: int,
    ) -> bool:
        """
        Sends the interactive HTML Widget card for a specific customer.
        """
        async with AsyncSessionLocal() as session:
            state = await self.build_customer_card_state(session, customer_id)

        if not state:
            return False

        chat_data_str = json.dumps(state, default=decimal_serializer, ensure_ascii=False)

        try:
            method = SendWidget(
                chat_id=chat_id,
                html=self._customer_card_html,
                chat_data=chat_data_str,
                caption=f"👤 Клієнт #{customer_id} — Інтерактивна картка",
                protect_content=True,
            )
            await bot(method)
            return True
        except Exception as e:
            logger.warning(f"Failed to send customer widget via sendWidget ({e}). Fallback to standard message.")
            return False

    async def update_customer_card(
        self,
        bot: Bot,
        chat_id: int,
        message_id: int,
        customer_id: int,
    ) -> bool:
        """
        Updates the chat_data of an existing customer card widget.
        """
        async with AsyncSessionLocal() as session:
            state = await self.build_customer_card_state(session, customer_id)

        if not state:
            return False

        return await self.update_widget(
            bot=bot,
            chat_id=chat_id,
            message_id=message_id,
            new_state=state,
        )

    async def build_order_create_state(
        self,
        session: AsyncSession,
        selected_customer_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Builds initial state for the interactive Order Creation widget.
        """
        raw_customers = await self.customers.search_customers(session, query="", limit=50)
        formatted_customers = [
            {
                "id": c.id,
                "name": c.name,
                "phone": c.phone,
                "address": c.address,
            }
            for c in raw_customers
        ]

        return {
            "selected_customer_id": selected_customer_id,
            "customers": formatted_customers,
            "default_unit_price": 200.00,
            "product_name": "Торф'яний брикет",
        }

    async def send_order_create(
        self,
        bot: Bot,
        chat_id: int,
        selected_customer_id: Optional[int] = None,
    ) -> bool:
        """
        Sends the interactive HTML Widget for creating an order.
        """
        async with AsyncSessionLocal() as session:
            state = await self.build_order_create_state(session, selected_customer_id)

        chat_data_str = json.dumps(state, default=decimal_serializer, ensure_ascii=False)

        try:
            method = SendWidget(
                chat_id=chat_id,
                html=self._order_create_html,
                chat_data=chat_data_str,
                caption="➕ Оформлення нового замовлення",
                protect_content=True,
            )
            await bot(method)
            return True
        except Exception as e:
            logger.warning(f"Failed to send order create widget via sendWidget ({e}). Fallback to standard wizard.")
            return False

    async def send_dashboard(
        self,
        bot: Bot,
        chat_id: int,
        initial_tab: str = "orders",
    ) -> bool:
        """
        Sends the HTML Widget dashboard to the user.
        """
        async with AsyncSessionLocal() as session:
            state = await self.build_dashboard_state(session, tab=initial_tab)

        chat_data_str = json.dumps(state, default=decimal_serializer, ensure_ascii=False)

        try:
            method = SendWidget(
                chat_id=chat_id,
                html=self._dashboard_html,
                chat_data=chat_data_str,
                caption="🪵 Peat CRM — Панель управління",
                protect_content=True,
            )
            await bot(method)
            return True
        except Exception as e:
            logger.warning(f"Failed to send HTML widget via sendWidget ({e}). Fallback to standard message.")
            return False

    async def update_widget(
        self,
        bot: Bot,
        chat_id: int,
        message_id: int,
        new_state: Dict[str, Any],
    ) -> bool:
        """
        Updates the chat_data of an existing widget message.
        """
        chat_data_str = json.dumps(new_state, default=decimal_serializer, ensure_ascii=False)
        try:
            method = EditMessageWidgetData(
                chat_id=chat_id,
                message_id=message_id,
                chat_data=chat_data_str,
            )
            await bot(method)
            return True
        except Exception as e:
            logger.error(f"Error updating widget message: {e}")
            return False

    async def answer_query(
        self,
        bot: Bot,
        widget_query_id: str,
        text: Optional[str] = None,
        show_alert: bool = False,
    ) -> bool:
        """
        Answers a widget_query callback within 15 seconds.
        """
        try:
            method = AnswerWidgetQuery(
                widget_query_id=widget_query_id,
                text=text,
                show_alert=show_alert,
            )
            await bot(method)
            return True
        except Exception as e:
            logger.error(f"Error answering widget query {widget_query_id}: {e}")
            return False


widget_service = WidgetService()
