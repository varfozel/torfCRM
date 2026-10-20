from datetime import date
from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.unavailable_date import UnavailableDate


class UnavailableDateRepository:
    """Async repository for UnavailableDate database operations."""

    async def list_all(
        self,
        session: AsyncSession,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> Sequence[UnavailableDate]:
        stmt = select(UnavailableDate)
        if from_date:
            stmt = stmt.where(UnavailableDate.date >= from_date)
        if to_date:
            stmt = stmt.where(UnavailableDate.date <= to_date)
        stmt = stmt.order_by(UnavailableDate.date.asc())
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_by_date(self, session: AsyncSession, target_date: date) -> Optional[UnavailableDate]:
        stmt = select(UnavailableDate).where(UnavailableDate.date == target_date)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, session: AsyncSession, target_date: date, reason: Optional[str] = None) -> UnavailableDate:
        cleaned_reason = reason.strip() if reason and reason.strip() else None
        entry = UnavailableDate(date=target_date, reason=cleaned_reason)
        session.add(entry)
        await session.commit()
        await session.refresh(entry)
        return entry

    async def delete(self, session: AsyncSession, entry: UnavailableDate) -> None:
        await session.delete(entry)
        await session.commit()


unavailable_date_repo = UnavailableDateRepository()
