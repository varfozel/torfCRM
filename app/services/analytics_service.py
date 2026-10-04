from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.customer import Customer
from app.models.order import Order, OrderStatus
from app.services.navigation import navigation_service


class AnalyticsService:
    """Service providing aggregate analytics, KPI statistics, and dashboard summaries."""

    async def get_dashboard_data(
        self,
        session: AsyncSession,
        period: str = "month",
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        today_start = datetime.combine(now.date(), time.min).replace(tzinfo=timezone.utc)

        # Determine date filter for the chosen period
        if period == "today":
            period_start = today_start
        elif period == "week":
            period_start = now - timedelta(days=7)
        elif period == "month":
            period_start = now - timedelta(days=30)
        elif period == "year":
            period_start = now - timedelta(days=365)
        else:  # "all"
            period_start = None

        # 1. KPI: Total customers
        cust_count_stmt = select(func.count(Customer.id))
        total_customers = (await session.execute(cust_count_stmt)).scalar() or 0

        # 2. KPI: New orders count
        new_orders_stmt = select(func.count(Order.id)).where(Order.status == OrderStatus.NEW.value)
        new_orders_count = (await session.execute(new_orders_stmt)).scalar() or 0

        # 3. KPI: Today's deliveries count (in_delivery or delivered today)
        today_deliv_stmt = select(func.count(Order.id)).where(
            (Order.status == OrderStatus.IN_DELIVERY.value)
            | (
                (Order.status == OrderStatus.DELIVERED.value)
                & (
                    (Order.delivery_completed_at >= today_start)
                    | (Order.created_at >= today_start)
                )
            )
        )
        today_deliveries_count = (await session.execute(today_deliv_stmt)).scalar() or 0

        # 4. Period Revenue & Quantity (excluding cancelled orders)
        revenue_query = select(
            func.coalesce(func.sum(Order.total_amount), 0),
            func.coalesce(func.sum(Order.quantity), 0),
            func.count(Order.id),
        ).where(Order.status != OrderStatus.CANCELLED.value)

        if period_start:
            revenue_query = revenue_query.where(Order.created_at >= period_start)

        rev_result = (await session.execute(revenue_query)).one()
        period_revenue = Decimal(str(rev_result[0])).quantize(Decimal("0.01"))
        period_quantity = Decimal(str(rev_result[1])).quantize(Decimal("0.01"))
        period_orders_count = int(rev_result[2])

        # 5. Status distribution
        status_stmt = (
            select(
                Order.status,
                func.count(Order.id).label("count"),
                func.coalesce(func.sum(Order.total_amount), 0).label("total_sum"),
            )
            .group_by(Order.status)
        )
        status_results = (await session.execute(status_stmt)).all()
        status_map = {
            s.value: {"status": s.value, "count": 0, "total_sum": Decimal("0.00")}
            for s in OrderStatus
        }
        for row in status_results:
            st = row[0]
            cnt = int(row[1])
            tot = Decimal(str(row[2])).quantize(Decimal("0.01"))
            if st in status_map:
                status_map[st] = {"status": st, "count": cnt, "total_sum": tot}
            else:
                status_map[st] = {"status": st, "count": cnt, "total_sum": tot}

        status_distribution = list(status_map.values())

        # 6. Sales chart (grouped by day for the last 14 or 30 days)
        chart_days = 30 if period in ["month", "year", "all"] else 7
        if period == "today":
            chart_days = 1

        chart_start = today_start - timedelta(days=chart_days - 1)
        chart_orders_stmt = (
            select(Order)
            .where(
                Order.created_at >= chart_start,
                Order.status != OrderStatus.CANCELLED.value,
            )
            .order_by(Order.created_at.asc())
        )
        chart_orders = (await session.execute(chart_orders_stmt)).scalars().all()

        # Build day-by-day aggregated map
        sales_by_day = {}
        for i in range(chart_days):
            d = (chart_start + timedelta(days=i)).strftime("%Y-%m-%d")
            sales_by_day[d] = {
                "date": d,
                "revenue": Decimal("0.00"),
                "orders_count": 0,
                "tons": Decimal("0.00"),
            }

        for order in chart_orders:
            d = order.created_at.strftime("%Y-%m-%d")
            if d in sales_by_day:
                sales_by_day[d]["revenue"] += order.total_amount
                sales_by_day[d]["orders_count"] += 1
                sales_by_day[d]["tons"] += order.quantity

        sales_chart = [
            {
                "date": item["date"],
                "revenue": float(item["revenue"]),
                "orders_count": item["orders_count"],
                "tons": float(item["tons"]),
            }
            for item in sorted(sales_by_day.values(), key=lambda x: x["date"])
        ]

        # 7. Recent orders (top 10)
        recent_orders_stmt = (
            select(Order)
            .options(selectinload(Order.customer))
            .order_by(Order.created_at.desc())
            .limit(10)
        )
        recent_orders_raw = (await session.execute(recent_orders_stmt)).scalars().all()
        recent_orders = [
            {
                "id": o.id,
                "customer_id": o.customer_id,
                "customer_name": o.customer.name if o.customer else "—",
                "customer_phone": o.customer.phone if o.customer else "—",
                "product_name": o.product_name,
                "quantity": float(o.quantity),
                "unit_price": float(o.unit_price),
                "delivery_price": float(o.delivery_price),
                "total_amount": float(o.total_amount),
                "delivery_address": o.delivery_address,
                "status": o.status,
                "created_at": o.created_at.isoformat(),
                "has_coordinates": bool(o.delivery_latitude and o.delivery_longitude),
                "waze_url": navigation_service.generate_waze_url(
                    o.delivery_latitude, o.delivery_longitude, o.delivery_address
                ),
            }
            for o in recent_orders_raw
        ]

        # 8. Recent customers (top 5 with orders count and total spent)
        recent_cust_stmt = (
            select(Customer)
            .options(selectinload(Customer.orders))
            .order_by(Customer.created_at.desc())
            .limit(5)
        )
        recent_cust_raw = (await session.execute(recent_cust_stmt)).scalars().all()
        recent_customers = [
            {
                "id": c.id,
                "name": c.name,
                "phone": c.phone,
                "address": c.address,
                "orders_count": len(c.orders),
                "total_spent": float(
                    sum(
                        (o.total_amount for o in c.orders if o.status != OrderStatus.CANCELLED.value),
                        Decimal("0.00"),
                    )
                ),
                "created_at": c.created_at.isoformat(),
            }
            for c in recent_cust_raw
        ]

        # 9. Deliveries with coordinates for Map
        map_orders_stmt = (
            select(Order)
            .options(selectinload(Order.customer))
            .where(
                Order.delivery_latitude.isnot(None),
                Order.delivery_longitude.isnot(None),
            )
            .order_by(Order.created_at.desc())
            .limit(100)
        )
        map_orders_raw = (await session.execute(map_orders_stmt)).scalars().all()
        map_deliveries = [
            {
                "id": o.id,
                "customer_name": o.customer.name if o.customer else "—",
                "customer_phone": o.customer.phone if o.customer else "—",
                "delivery_address": o.delivery_address,
                "latitude": float(o.delivery_latitude),
                "longitude": float(o.delivery_longitude),
                "quantity": float(o.quantity),
                "total_amount": float(o.total_amount),
                "status": o.status,
                "created_at": o.created_at.isoformat(),
                "waze_url": navigation_service.generate_waze_url(
                    o.delivery_latitude, o.delivery_longitude, o.delivery_address
                ),
                "google_maps_url": (
                    f"https://www.google.com/maps/search/?api=1&query={o.delivery_latitude},{o.delivery_longitude}"
                ),
            }
            for o in map_orders_raw
        ]

        return {
            "period": period,
            "kpi": {
                "new_orders_count": new_orders_count,
                "today_deliveries_count": today_deliveries_count,
                "total_customers": total_customers,
                "period_revenue": float(period_revenue),
                "period_quantity_tons": float(period_quantity),
                "period_orders_count": period_orders_count,
            },
            "status_distribution": [
                {
                    "status": s["status"],
                    "count": s["count"],
                    "total_sum": float(s["total_sum"]),
                }
                for s in status_distribution
            ],
            "sales_chart": sales_chart,
            "recent_orders": recent_orders,
            "recent_customers": recent_customers,
            "map_deliveries": map_deliveries,
            "warehouse": navigation_service.warehouse_info,
        }


analytics_service = AnalyticsService()
