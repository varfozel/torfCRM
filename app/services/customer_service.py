from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.repositories.customer_repo import customer_repo
from app.schemas.customer import CustomerCreate, CustomerUpdate


class CustomerService:
    """Service handling Customer business operations."""

    def __init__(self):
        self.repo = customer_repo

    async def create_customer(
        self,
        session: AsyncSession,
        customer_in: CustomerCreate,
    ) -> Customer:
        return await self.repo.create(session, customer_in)

    async def get_customer(
        self,
        session: AsyncSession,
        customer_id: int,
    ) -> Optional[Customer]:
        return await self.repo.get_by_id(session, customer_id)

    async def search_customers(
        self,
        session: AsyncSession,
        query: str,
        limit: int = 50,
    ) -> Sequence[Customer]:
        if not query or not query.strip():
            return await self.repo.list_all(session, limit=limit)
        return await self.repo.search(session, query, limit=limit)

    async def list_customers(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 50,
    ) -> Sequence[Customer]:
        return await self.repo.list_all(session, skip=skip, limit=limit)

    async def update_customer(
        self,
        session: AsyncSession,
        customer_id: int,
        customer_update: CustomerUpdate,
    ) -> Optional[Customer]:
        customer = await self.repo.get_by_id(session, customer_id)
        if not customer:
            return None
        return await self.repo.update(session, customer, customer_update)

    async def delete_customer(
        self,
        session: AsyncSession,
        customer_id: int,
    ) -> bool:
        customer = await self.repo.get_by_id(session, customer_id)
        if not customer:
            return False
        await self.repo.delete(session, customer)
        return True


customer_service = CustomerService()
