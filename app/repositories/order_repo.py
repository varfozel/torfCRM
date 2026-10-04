from datetime import datetime
from typing import Optional, Sequence
from sqlalchemy import cast, func, or_, select, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.customer import Customer
from app.models.order import Order


class OrderRepository:
    """Async repository for Order database operations."""

    async def create(self, session: AsyncSession, order_data: dict) -> Order:
        order = Order(**order_data)
        session.add(order)
        await session.commit()
        await session.refresh(order)
        # Ensure customer relationship is loaded
        stmt = select(Order).options(selectinload(Order.customer)).where(Order.id == order.id)
        result = await session.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, session: AsyncSession, order_id: int) -> Optional[Order]:
        stmt = (
            select(Order)
            .options(selectinload(Order.customer))
            .where(Order.id == order_id)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    def _apply_filters(
        self,
        stmt,
        status: Optional[str] = None,
        customer_id: Optional[int] = None,
        search_query: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ):
        if status:
            stmt = stmt.where(Order.status == status)
        if customer_id:
            stmt = stmt.where(Order.customer_id == customer_id)
        if date_from:
            stmt = stmt.where(Order.created_at >= date_from)
        if date_to:
            stmt = stmt.where(Order.created_at <= date_to)
        if search_query and search_query.strip():
            term = f"%{search_query.strip()}%"
            # Join with customer to search across customer name, phone, order id, or address
            clean_term = search_query.strip().lstrip("#")
            filters = [
                Order.delivery_address.ilike(term),
                Customer.name.ilike(term),
                Customer.phone.ilike(term),
            ]
            if clean_term.isdigit():
                filters.append(Order.id == int(clean_term))

            stmt = stmt.join(Order.customer).where(or_(*filters))
        return stmt

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
        stmt = select(Order).options(selectinload(Order.customer))
        stmt = self._apply_filters(
            stmt,
            status=status,
            customer_id=customer_id,
            search_query=search_query,
            date_from=date_from,
            date_to=date_to,
        )

        # Sorting
        sort_col = getattr(Order, sort_by, Order.created_at)
        if sort_dir.lower() == "asc":
            stmt = stmt.order_by(sort_col.asc())
        else:
            stmt = stmt.order_by(sort_col.desc())

        stmt = stmt.offset(skip).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def count_orders(
        self,
        session: AsyncSession,
        status: Optional[str] = None,
        customer_id: Optional[int] = None,
        search_query: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> int:
        stmt = select(func.count(Order.id))
        stmt = self._apply_filters(
            stmt,
            status=status,
            customer_id=customer_id,
            search_query=search_query,
            date_from=date_from,
            date_to=date_to,
        )
        result = await session.execute(stmt)
        return result.scalar() or 0

    async def update(
        self,
        session: AsyncSession,
        order: Order,
        update_data: dict,
    ) -> Order:
        for key, value in update_data.items():
            setattr(order, key, value)
        await session.commit()
        await session.refresh(order)
        return order

    async def delete(self, session: AsyncSession, order: Order) -> None:
        await session.delete(order)
        await session.commit()


order_repo = OrderRepository()
