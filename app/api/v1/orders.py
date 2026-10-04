from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.order import OrderStatus
from app.schemas.order import OrderCreate, OrderResponse, OrderUpdate
from app.services.order_service import order_service

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_in: OrderCreate,
    session: AsyncSession = Depends(get_db),
):
    """Створити нове замовлення."""
    try:
        order = await order_service.create_order(session, order_in)
        return order_service.enrich_order_response(order)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/", response_model=List[OrderResponse])
async def list_orders(
    response: Response,
    order_status: Optional[OrderStatus] = Query(None, alias="status", description="Фільтр за статусом"),
    customer_id: Optional[int] = Query(None, description="Фільтр за ID клієнта"),
    q: Optional[str] = Query(None, description="Пошук за номером замовлення, клієнтом, телефоном, адресою"),
    date_from: Optional[datetime] = Query(None, description="Початкова дата (ISO)"),
    date_to: Optional[datetime] = Query(None, description="Кінцева дата (ISO)"),
    sort_by: Optional[str] = Query("created_at", description="Поле сортування"),
    sort_dir: Optional[str] = Query("desc", description="Напрямок сортування (asc, desc)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
):
    """Отримати список замовлень з можливістю розширеного пошуку, фільтрації та пагінації."""
    status_val = order_status.value if order_status else None
    
    total_count = await order_service.count_orders(
        session=session,
        status=status_val,
        customer_id=customer_id,
        search_query=q,
        date_from=date_from,
        date_to=date_to,
    )
    response.headers["X-Total-Count"] = str(total_count)
    response.headers["Access-Control-Expose-Headers"] = "X-Total-Count"

    orders = await order_service.list_orders(
        session=session,
        status=status_val,
        customer_id=customer_id,
        search_query=q,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by or "created_at",
        sort_dir=sort_dir or "desc",
        skip=skip,
        limit=limit,
    )
    return [order_service.enrich_order_response(o) for o in orders]


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    session: AsyncSession = Depends(get_db),
):
    """Отримати деталі замовлення (включаючи інформацію про клієнта та навігаційне посилання Waze)."""
    order = await order_service.get_order(session, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Замовлення #{order_id} не знайдено",
        )
    return order_service.enrich_order_response(order)


@router.post("/{order_id}/plan", response_model=OrderResponse)
async def plan_order(
    order_id: int,
    session: AsyncSession = Depends(get_db),
):
    """Позначити замовлення як заплановане до доставки (змінює статус на planned)."""
    try:
        order = await order_service.plan_order(session, order_id)
        return order_service.enrich_order_response(order)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{order_id}/start-delivery", response_model=OrderResponse)
async def start_delivery(
    order_id: int,
    session: AsyncSession = Depends(get_db),
):
    """Розпочати доставку замовлення (фіксує час виїзду та змінює статус на in_delivery)."""
    try:
        order = await order_service.start_delivery(session, order_id)
        return order_service.enrich_order_response(order)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{order_id}/complete-delivery", response_model=OrderResponse)
async def complete_delivery(
    order_id: int,
    session: AsyncSession = Depends(get_db),
):
    """Завершити доставку замовлення (фіксує час доставки та змінює статус на delivered)."""
    try:
        order = await order_service.complete_delivery(session, order_id)
        return order_service.enrich_order_response(order)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: int,
    reason: Optional[str] = Query(None, description="Причина скасування"),
    session: AsyncSession = Depends(get_db),
):
    """Скасувати замовлення."""
    try:
        order = await order_service.cancel_order(session, order_id, notes=reason)
        return order_service.enrich_order_response(order)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.patch("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: int,
    order_update: OrderUpdate,
    session: AsyncSession = Depends(get_db),
):
    """Оновити замовлення (кількість, ціну, вартість доставки, адресу тощо)."""
    try:
        order = await order_service.update_order(session, order_id, order_update)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Замовлення #{order_id} не знайдено",
            )
        return order_service.enrich_order_response(order)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    order_id: int,
    session: AsyncSession = Depends(get_db),
):
    """Видалити замовлення."""
    deleted = await order_service.delete_order(session, order_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Замовлення #{order_id} не знайдено",
        )
