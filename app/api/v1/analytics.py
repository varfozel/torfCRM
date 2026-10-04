from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.analytics_service import analytics_service

router = APIRouter(prefix="/analytics", tags=["Analytics & Dashboard"])


@router.get("/dashboard")
async def get_dashboard(
    period: Optional[str] = Query("month", description="Період: today, week, month, year, all"),
    session: AsyncSession = Depends(get_db),
):
    """Отримати агреговану аналітику: KPI, графік продажів, розподіл статусів та доставку для карти."""
    return await analytics_service.get_dashboard_data(session=session, period=period or "month")
