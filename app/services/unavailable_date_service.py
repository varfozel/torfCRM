from datetime import date
from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.unavailable_date import UnavailableDate
from app.repositories.unavailable_date_repo import unavailable_date_repo


class UnavailableDateService:
    """Service handling unavailable/undesirable calendar date management."""

    def __init__(self):
        self.repo = unavailable_date_repo

    async def list_unavailable_dates(
        self,
        session: AsyncSession,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> Sequence[UnavailableDate]:
        return await self.repo.list_all(session, from_date=from_date, to_date=to_date)

    async def get_by_date(self, session: AsyncSession, target_date: date) -> Optional[UnavailableDate]:
        return await self.repo.get_by_date(session, target_date)

    async def is_date_unavailable(self, session: AsyncSession, target_date: date) -> bool:
        entry = await self.repo.get_by_date(session, target_date)
        return entry is not None

    async def add_unavailable_date(
        self,
        session: AsyncSession,
        target_date: date,
        reason: Optional[str] = None,
    ) -> UnavailableDate:
        existing = await self.repo.get_by_date(session, target_date)
        if existing:
            raise ValueError(f"Дата {target_date} вже позначена як небажана.")
        return await self.repo.create(session, target_date=target_date, reason=reason)

    async def remove_unavailable_date(self, session: AsyncSession, target_date: date) -> bool:
        existing = await self.repo.get_by_date(session, target_date)
        if not existing:
            return False
        await self.repo.delete(session, existing)
        return True


unavailable_date_service = UnavailableDateService()
