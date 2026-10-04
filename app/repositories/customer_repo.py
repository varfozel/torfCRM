from typing import Optional, Sequence
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate


class CustomerRepository:
    """Async repository for Customer database operations."""

    async def create(self, session: AsyncSession, customer_in: CustomerCreate) -> Customer:
        customer = Customer(
            name=customer_in.name.strip(),
            phone=customer_in.phone.strip(),
            address=customer_in.address.strip(),
            latitude=customer_in.latitude,
            longitude=customer_in.longitude,
            notes=customer_in.notes,
        )
        session.add(customer)
        await session.commit()
        await session.refresh(customer)
        return customer

    async def get_by_id(self, session: AsyncSession, customer_id: int) -> Optional[Customer]:
        stmt = select(Customer).where(Customer.id == customer_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def search(
        self,
        session: AsyncSession,
        query: str,
        limit: int = 50,
    ) -> Sequence[Customer]:
        """Search customers by phone number or name (case-insensitive)."""
        term = f"%{query.strip()}%"
        stmt = (
            select(Customer)
            .where(or_(Customer.name.ilike(term), Customer.phone.ilike(term)))
            .order_by(Customer.name.asc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    async def list_all(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 50,
    ) -> Sequence[Customer]:
        stmt = (
            select(Customer)
            .order_by(Customer.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    async def update(
        self,
        session: AsyncSession,
        customer: Customer,
        customer_update: CustomerUpdate,
    ) -> Customer:
        data = customer_update.model_dump(exclude_unset=True)
        for key, value in data.items():
            setattr(customer, key, value)
        await session.commit()
        await session.refresh(customer)
        return customer

    async def delete(self, session: AsyncSession, customer: Customer) -> None:
        await session.delete(customer)
        await session.commit()


customer_repo = CustomerRepository()
