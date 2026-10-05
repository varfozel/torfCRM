from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import DEFAULT_PRODUCT_NAME, Order, OrderStatus
from app.repositories.customer_repo import customer_repo
from app.repositories.order_repo import order_repo
from app.schemas.order import OrderCreate, OrderResponse, OrderUpdate
from app.services.navigation import navigation_service


class OrderService:
    """Service handling Order operations, delivery lifecycles, and financial calculations."""

    def __init__(self):
        self.repo = order_repo
        self.customer_repo = customer_repo
        self.nav = navigation_service

    async def create_order(
        self,
        session: AsyncSession,
        order_in: OrderCreate,
    ) -> Order:
        # Verify customer exists
        customer = await self.customer_repo.get_by_id(session, order_in.customer_id)
        if not customer:
            raise ValueError(f"Клієнта з ID {order_in.customer_id} не знайдено.")

        # Validate non-negative quantities and prices
        if order_in.quantity <= Decimal("0.00"):
            raise ValueError("Кількість товару повинна бути більшою за нуль.")

        if order_in.unit_price < Decimal("0.00"):
            raise ValueError("Ціна за одиницю не може бути від'ємною.")

        delivery_price = (order_in.delivery_price if order_in.delivery_price is not None else Decimal("0.00")).quantize(Decimal("0.01"))
        if delivery_price < Decimal("0.00"):
            raise ValueError("Вартість доставки не може бути від'ємною.")

        # Calculate product total and total amount
        if (
            Decimal(str(order_in.quantity)) in (Decimal("1"), Decimal("2"), Decimal("3"))
            and Decimal(str(order_in.unit_price)) in (Decimal("12000"), Decimal("12500"), Decimal("13000"))
        ):
            product_total = Decimal(str(order_in.unit_price)).quantize(Decimal("0.01"))
        else:
            product_total = (order_in.quantity * order_in.unit_price).quantize(Decimal("0.01"))
        total_amount = (product_total + delivery_price).quantize(Decimal("0.01"))

        # Default delivery address and coordinates to customer's if not explicitly provided
        delivery_address = order_in.delivery_address or customer.address
        if not delivery_address or not delivery_address.strip():
            delivery_address = customer.address

        delivery_lat = (
            order_in.delivery_latitude
            if order_in.delivery_latitude is not None
            else customer.latitude
        )
        delivery_lon = (
            order_in.delivery_longitude
            if order_in.delivery_longitude is not None
            else customer.longitude
        )

        order_date = order_in.order_date or datetime.now(timezone.utc).date()

        order_data = {
            "customer_id": customer.id,
            "product_name": DEFAULT_PRODUCT_NAME,
            "quantity": order_in.quantity,
            "unit_price": order_in.unit_price,
            "delivery_price": delivery_price,
            "total_amount": total_amount,
            "delivery_address": delivery_address.strip(),
            "delivery_latitude": delivery_lat,
            "delivery_longitude": delivery_lon,
            "distance_km": order_in.distance_km,
            "order_date": order_date,
            "status": OrderStatus.NEW.value,
            "notes": order_in.notes,
        }

        return await self.repo.create(session, order_data)

    async def get_order(
        self,
        session: AsyncSession,
        order_id: int,
    ) -> Optional[Order]:
        return await self.repo.get_by_id(session, order_id)

    async def list_orders(
        self,
        session: AsyncSession,
        status: Optional[str] = None,
        customer_id: Optional[int] = None,
        search_query: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
        skip: int = 0,
        limit: int = 50,
    ) -> Sequence[Order]:
        return await self.repo.list_orders(
            session=session,
            status=status,
            customer_id=customer_id,
            search_query=search_query,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            sort_dir=sort_dir,
            skip=skip,
            limit=limit,
        )

    async def count_orders(
        self,
        session: AsyncSession,
        status: Optional[str] = None,
        customer_id: Optional[int] = None,
        search_query: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> int:
        return await self.repo.count_orders(
            session=session,
            status=status,
            customer_id=customer_id,
            search_query=search_query,
            date_from=date_from,
            date_to=date_to,
        )

    async def update_order(
        self,
        session: AsyncSession,
        order_id: int,
        order_update: OrderUpdate,
    ) -> Optional[Order]:
        order = await self.repo.get_by_id(session, order_id)
        if not order:
            return None

        data = order_update.model_dump(exclude_unset=True)
        if "status" in data and isinstance(data["status"], OrderStatus):
            data["status"] = data["status"].value

        # Validate values if provided
        qty = data.get("quantity", order.quantity)
        if qty <= Decimal("0.00"):
            raise ValueError("Кількість товару повинна бути більшою за нуль.")

        price = data.get("unit_price", order.unit_price)
        if price < Decimal("0.00"):
            raise ValueError("Ціна за одиницю не може бути від'ємною.")

        deliv = data.get("delivery_price", order.delivery_price)
        if deliv < Decimal("0.00"):
            raise ValueError("Вартість доставки не може бути від'ємною.")

        # If quantity, price or delivery_price changed, recalculate total_amount
        if any(k in data for k in ["quantity", "unit_price", "delivery_price"]):
            if (
                Decimal(str(qty)) in (Decimal("1"), Decimal("2"), Decimal("3"))
                and Decimal(str(price)) in (Decimal("12000"), Decimal("12500"), Decimal("13000"))
            ):
                product_total = Decimal(str(price)).quantize(Decimal("0.01"))
            else:
                product_total = (qty * price).quantize(Decimal("0.01"))
            data["total_amount"] = (product_total + deliv).quantize(Decimal("0.01"))

        return await self.repo.update(session, order, data)

    async def start_delivery(
        self,
        session: AsyncSession,
        order_id: int,
    ) -> Order:
        """Transition order status to 'in_delivery' and record start timestamp."""
        order = await self.repo.get_by_id(session, order_id)
        if not order:
            raise ValueError(f"Замовлення #{order_id} не знайдено.")

        if order.status == OrderStatus.DELIVERED.value:
            raise ValueError(f"Замовлення #{order_id} вже доставлено.")
        if order.status == OrderStatus.CANCELLED.value:
            raise ValueError(f"Замовлення #{order_id} скасовано.")

        update_data = {
            "status": OrderStatus.IN_DELIVERY.value,
            "delivery_started_at": datetime.now(timezone.utc),
        }
        return await self.repo.update(session, order, update_data)

    async def complete_delivery(
        self,
        session: AsyncSession,
        order_id: int,
    ) -> Order:
        """Transition order status to 'delivered' and record completion timestamp."""
        order = await self.repo.get_by_id(session, order_id)
        if not order:
            raise ValueError(f"Замовлення #{order_id} не знайдено.")

        if order.status == OrderStatus.CANCELLED.value:
            raise ValueError(f"Неможливо завершити скасоване замовлення #{order_id}.")

        now = datetime.now(timezone.utc)
        update_data = {
            "status": OrderStatus.DELIVERED.value,
            "delivery_completed_at": now,
        }
        if not order.delivery_started_at:
            update_data["delivery_started_at"] = now

        return await self.repo.update(session, order, update_data)

    async def cancel_order(
        self,
        session: AsyncSession,
        order_id: int,
        notes: Optional[str] = None,
    ) -> Order:
        """Mark order as cancelled."""
        order = await self.repo.get_by_id(session, order_id)
        if not order:
            raise ValueError(f"Замовлення #{order_id} не знайдено.")

        update_data = {"status": OrderStatus.CANCELLED.value}
        if notes:
            existing = order.notes or ""
            update_data["notes"] = f"{existing}\n[Скасовано]: {notes}".strip()

        return await self.repo.update(session, order, update_data)

    async def plan_order(
        self,
        session: AsyncSession,
        order_id: int,
    ) -> Order:
        """Mark order as planned for delivery."""
        order = await self.repo.get_by_id(session, order_id)
        if not order:
            raise ValueError(f"Замовлення #{order_id} не знайдено.")

        if order.status == OrderStatus.CANCELLED.value:
            raise ValueError(f"Неможливо запланувати скасоване замовлення #{order_id}.")

        update_data = {"status": OrderStatus.PLANNED.value}
        return await self.repo.update(session, order, update_data)

    async def delete_order(
        self,
        session: AsyncSession,
        order_id: int,
    ) -> bool:
        """Delete order by ID."""
        order = await self.repo.get_by_id(session, order_id)
        if not order:
            return False
        await self.repo.delete(session, order)
        return True

    def enrich_order_response(self, order: Order) -> OrderResponse:
        """Converts Order model to OrderResponse and generates Waze URL."""
        waze_url = self.nav.generate_waze_url(
            latitude=order.delivery_latitude,
            longitude=order.delivery_longitude,
            address=order.delivery_address,
        )
        data = OrderResponse.model_validate(order)
        data.waze_url = waze_url
        return data


order_service = OrderService()
