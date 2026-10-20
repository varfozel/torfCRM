from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.unavailable_date import UnavailableDateCreate, UnavailableDateResponse
from app.services.auth_service import ManagerUser, get_current_manager
from app.services.unavailable_date_service import unavailable_date_service

router = APIRouter(prefix="/calendar", tags=["Calendar & Unavailable Dates"])


class ActionResponse(BaseModel):
    success: bool
    message: str


@router.get(
    "/unavailable-dates",
    response_model=List[UnavailableDateResponse],
    summary="Отримати список небажаних дат у календарі",
)
async def list_unavailable_dates(
    from_date: Optional[date] = Query(None, description="Початкова дата фільтрації (YYYY-MM-DD)"),
    to_date: Optional[date] = Query(None, description="Кінцева дата фільтрації (YYYY-MM-DD)"),
    session: AsyncSession = Depends(get_db),
):
    """Отримати список усіх позначених небажаних дат доставки для календаря замовлень."""
    return await unavailable_date_service.list_unavailable_dates(
        session=session,
        from_date=from_date,
        to_date=to_date,
    )


@router.post(
    "/unavailable-dates",
    response_model=UnavailableDateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Позначити день як небажаний для замовлень",
)
async def add_unavailable_date(
    payload: UnavailableDateCreate,
    current_manager: ManagerUser = Depends(get_current_manager),
    session: AsyncSession = Depends(get_db),
):
    """
    Позначити день як небажаний (🔴) для створення замовлень / доставок.
    Вимагає авторизації менеджера.
    Не забороняє створення замовлень, лише створює попередження для персоналу.
    """
    try:
        return await unavailable_date_service.add_unavailable_date(
            session=session,
            target_date=payload.date,
            reason=payload.reason,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/unavailable-dates/{target_date}",
    response_model=ActionResponse,
    summary="Зняти позначку небажаного дня",
)
async def remove_unavailable_date(
    target_date: date,
    current_manager: ManagerUser = Depends(get_current_manager),
    session: AsyncSession = Depends(get_db),
):
    """
    Зняти позначку небажаного дня (🟢) з календаря.
    Вимагає авторизації менеджера.
    """
    deleted = await unavailable_date_service.remove_unavailable_date(
        session=session,
        target_date=target_date,
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Небажану дату {target_date} не знайдено.",
        )
    return ActionResponse(
        success=True,
        message=f"Позначку з дати {target_date} успішно знято.",
    )
