from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.customer import (
    CustomerCreate,
    CustomerDetailResponse,
    CustomerResponse,
    CustomerUpdate,
)
from app.services.customer_service import customer_service
from app.services.order_service import order_service

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_in: CustomerCreate,
    session: AsyncSession = Depends(get_db),
):
    """Створити нового клієнта."""
    customer = await customer_service.create_customer(session, customer_in)
    return customer_service.enrich_customer(customer)


@router.get("/", response_model=List[CustomerResponse])
async def list_customers(
    q: Optional[str] = Query(None, description="Пошук за телефоном або назвою клієнта"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
):
    """Отримати список клієнтів або виконати пошук за назвою чи номером телефону."""
    if q:
        customers = await customer_service.search_customers(session, q, limit=limit)
    else:
        customers = await customer_service.list_customers(session, skip=skip, limit=limit)
    return [customer_service.enrich_customer(c) for c in customers]


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: int,
    session: AsyncSession = Depends(get_db),
):
    """Отримати інформацію про клієнта за ID."""
    customer = await customer_service.get_customer(session, customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Клієнта з ID {customer_id} не знайдено",
        )
    return customer_service.enrich_customer(customer)


@router.get("/{customer_id}/detail", response_model=CustomerDetailResponse)
async def get_customer_detail(
    customer_id: int,
    session: AsyncSession = Depends(get_db),
):
    """Отримати деталі клієнта разом із повною історією замовлень."""
    customer = await customer_service.get_customer(session, customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Клієнта з ID {customer_id} не знайдено",
        )
    enriched = customer_service.enrich_customer(customer)
    orders = [
        order_service.enrich_order_response(o)
        for o in (customer.orders or [])
    ]
    enriched["orders"] = orders
    return enriched


@router.patch("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: int,
    customer_update: CustomerUpdate,
    session: AsyncSession = Depends(get_db),
):
    """Оновити інформацію про клієнта."""
    updated = await customer_service.update_customer(session, customer_id, customer_update)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Клієнта з ID {customer_id} не знайдено",
        )
    return customer_service.enrich_customer(updated)


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: int,
    session: AsyncSession = Depends(get_db),
):
    """Видалити клієнта та всі пов'язані замовлення."""
    deleted = await customer_service.delete_customer(session, customer_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Клієнта з ID {customer_id} не знайдено",
        )
