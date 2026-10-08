from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import DEFAULT_PRODUCT_NAME, Order, OrderStatus
from app.repositories.customer_repo import customer_repo
from app.repositories.order_repo import order_repo
from app.schemas.order import OrderCreate, OrderResponse, OrderUpdate
from app.services.navigation import navigation_service


def calculate_order_financials(
    quantity_tons: Decimal,
    price_per_ton: Decimal,
    distance_km: Optional[Decimal] = None,
    delivery_price_per_km: Optional[Decimal] = None,
    delivery_price: Optional[Decimal] = None,
) -> tuple[Decimal, Decimal, Decimal]:
    """
    ЄДИНА ФОРМУЛА РОЗРАХУНКУ ВАРТОСТІ ЗАМОВЛЕННЯ:
      product_amount = quantity_tons * price_per_ton
      delivery_amount = distance_km * delivery_price_per_km (або delivery_price якщо без тарифу/км)
      total_amount = product_amount + delivery_amount

    Backend не довіряє зовнішнім розрахункам total_amount і завжди перераховує їх самостійно.

    Повертає кортеж: (product_amount, delivery_amount, total_amount)
    """
    if quantity_tons <= Decimal("0.00"):
        raise ValueError("Кількість товару повинна бути більшою за нуль.")
    if price_per_ton < Decimal("0.00"):
        raise ValueError("Ціна за одиницю не може бути від'ємною.")

    # 1. Вартість товару: product_amount = quantity_tons * price_per_ton
    product_amount = (quantity_tons * price_per_ton).quantize(Decimal("0.01"))

    # 2. Вартість доставки: delivery_amount = distance_km * delivery_price_per_km
    if delivery_price_per_km is not None:
        if delivery_price_per_km < Decimal("0.00"):
            raise ValueError("Ціна доставки за км не може бути від'ємною.")
        dist = distance_km if distance_km is not None else Decimal("0.00")
        if dist < Decimal("0.00"):
            raise ValueError("Кілометраж доставки не може бути від'ємним.")
        delivery_amount = (dist * delivery_price_per_km).quantize(Decimal("0.01"))
    elif delivery_price is not None:
        if delivery_price < Decimal("0.00"):
            raise ValueError("Вартість доставки не може бути від'ємною.")
        delivery_amount = delivery_price.quantize(Decimal("0.01"))
    else:
        delivery_amount = Decimal("0.00")

    # 3. Загальна сума: total_amount = product_amount + delivery_amount
    total_amount = (product_amount + delivery_amount).quantize(Decimal("0.01"))

    return product_amount, delivery_amount, total_amount


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

        # Розрахунок за єдиною формулою: backend самостійно перераховує автоматичну суму
        product_amount, delivery_amount, auto_total = calculate_order_financials(
            quantity_tons=order_in.quantity,
            price_per_ton=order_in.unit_price,
            distance_km=order_in.distance_km,
            delivery_price_per_km=order_in.delivery_price_per_km,
            delivery_price=order_in.delivery_price,
        )

        # Визначаємо, чи увімкнено ручний режим встановлення суми
        is_manual = bool(order_in.is_total_manual)
        manual_amount = order_in.manual_total_amount or order_in.final_total_amount
        if is_manual and manual_amount is not None:
            if manual_amount < Decimal("0.00"):
                raise ValueError("Фінальна сума не може бути від'ємною.")
            final_total = manual_amount.quantize(Decimal("0.01"))
        else:
            final_total = auto_total
            is_manual = False

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
            "product_name": order_in.product_name or DEFAULT_PRODUCT_NAME,
            "quantity": order_in.quantity,
            "unit_price": order_in.unit_price,
            "delivery_price_per_km": order_in.delivery_price_per_km,
            "delivery_price": delivery_amount,
            "calculated_total_amount": auto_total,
            "total_amount": final_total,
            "is_total_manual": is_manual,
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

        # 1. Відкидаємо небезпечні розрахункові поля
        for untrusted_key in ("total_amount", "total_price", "product_total", "product_amount", "delivery_amount", "calculated_total_amount"):
            data.pop(untrusted_key, None)

        # 2. Отримуємо параметри ручного редагування фінальної суми
        manual_total_val = None
        if "manual_total_amount" in data:
            manual_total_val = data.pop("manual_total_amount")
        elif "final_total_amount" in data:
            manual_total_val = data.pop("final_total_amount")

        # Визначаємо статус ручного режиму
        if "is_total_manual" in data:
            is_manual = bool(data["is_total_manual"])
        else:
            is_manual = order.is_total_manual

        # 3. Нормалізація аліасів
        if "quantity_tons" in data and "quantity" not in data:
            data["quantity"] = data.pop("quantity_tons")
        else:
            data.pop("quantity_tons", None)

        if "price_per_ton" in data and "unit_price" not in data:
            data["unit_price"] = data.pop("price_per_ton")
        else:
            data.pop("price_per_ton", None)

        if "status" in data and isinstance(data["status"], OrderStatus):
            data["status"] = data["status"].value

        # 4. Визначити актуальні значення для розрахунку
        qty = data.get("quantity", order.quantity)
        price = data.get("unit_price", order.unit_price)
        dist = data.get("distance_km", order.distance_km)

        # Визначення тарифу доставки
        if "delivery_price_per_km" in data:
            km_rate = data["delivery_price_per_km"]
            fixed_deliv = data.get("delivery_price", order.delivery_price)
        elif "delivery_price" in data and "distance_km" not in data:
            km_rate = None
            fixed_deliv = data["delivery_price"]
        else:
            km_rate = order.delivery_price_per_km
            fixed_deliv = data.get("delivery_price", order.delivery_price)

        # 5. Автоматичний розрахунок за єдиною формулою
        product_amount, delivery_amount, auto_total = calculate_order_financials(
            quantity_tons=qty,
            price_per_ton=price,
            distance_km=dist,
            delivery_price_per_km=km_rate,
            delivery_price=fixed_deliv,
        )

        data["delivery_price"] = delivery_amount
        data["calculated_total_amount"] = auto_total

        # 6. Визначення фінальної суми
        if not is_manual:
            # Автоматичний розрахунок (або скидання назад до автоматичного)
            data["is_total_manual"] = False
            data["total_amount"] = auto_total
        else:
            # Ручний режим активний
            data["is_total_manual"] = True
            if manual_total_val is not None:
                if manual_total_val < Decimal("0.00"):
                    raise ValueError("Фінальна сума не може бути від'ємною.")
                data["total_amount"] = manual_total_val.quantize(Decimal("0.01"))
            elif not order.is_total_manual:
                # Щойно увімкнено ручний режим без вказання суми -> беремо поточну автоматичну
                data["total_amount"] = auto_total
            else:
                # Вже було ручним, і параметри замовлення змінилися -> зберігаємо попередню ручну суму
                data["total_amount"] = order.total_amount

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
