from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderStatus
from app.repositories.customer_repo import customer_repo
from app.repositories.order_repo import order_repo
from app.schemas.order import OrderCreate, OrderResponse, OrderUpdate
from app.services.navigation import navigation_service


class OrderService:
    """Service handling Order operations and delivery lifecycles."""

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

        # Calculate total if not provided: quantity * unit_price
        total_amount = order_in.total_amount
        if total_amount is None:
            total_amount = (order_in.quantity * order_in.unit_price).quantize(Decimal("0.01"))

        order_data = {
            "customer_id": customer.id,
            "product_name": order_in.product_name.strip(),
            "quantity": order_in.quantity,
            "unit_price": order_in.unit_price,
            "total_amount": total_amount,
            "delivery_address": delivery_address.strip(),
            "delivery_latitude": delivery_lat,
            "delivery_longitude": delivery_lon,
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
        skip: int = 0,
        limit: int = 50,
    ) -> Sequence[Order]:
        return await self.repo.list_orders(
            session=session,
            status=status,
            customer_id=customer_id,
            skip=skip,
            limit=limit,
        )

    async def start_delivery(
        self,
        session: AsyncSession,
        order_id: int,
    ) -> Order:
        """
        Transition order status to 'in_delivery' and record start timestamp.
        """
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
        """
        Transition order status to 'delivered' and record completion timestamp.
        """
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
        """
        Mark order as cancelled.
        """
        order = await self.repo.get_by_id(session, order_id)
        if not order:
            raise ValueError(f"Замовлення #{order_id} не знайдено.")

        update_data = {"status": OrderStatus.CANCELLED.value}
        if notes:
            existing = order.notes or ""
            update_data["notes"] = f"{existing}\n[Скасовано]: {notes}".strip()

        return await self.repo.update(session, order, update_data)

    def enrich_order_response(self, order: Order) -> OrderResponse:
        """
        Converts Order model to OrderResponse and generates Waze URL.
        """
        waze_url = self.nav.generate_waze_url(
            latitude=order.delivery_latitude,
            longitude=order.delivery_longitude,
            address=order.delivery_address,
        )
        data = OrderResponse.model_validate(order)
        data.waze_url = waze_url
        return data


order_service = OrderService()
