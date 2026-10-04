from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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

    async def list_orders(
        self,
        session: AsyncSession,
        status: Optional[str] = None,
        customer_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Sequence[Order]:
        stmt = (
            select(Order)
            .options(selectinload(Order.customer))
            .order_by(Order.created_at.desc())
        )
        if status:
            stmt = stmt.where(Order.status == status)
        if customer_id:
            stmt = stmt.where(Order.customer_id == customer_id)

        stmt = stmt.offset(skip).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()

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
