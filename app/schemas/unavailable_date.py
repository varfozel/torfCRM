import datetime as dt
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class UnavailableDateCreate(BaseModel):
    date: dt.date = Field(..., description="Дата у форматі YYYY-MM-DD")
    reason: Optional[str] = Field(None, max_length=255, description="Причина (необов'язково)")


class UnavailableDateResponse(BaseModel):
    id: int
    date: dt.date
    reason: Optional[str] = None
    created_at: dt.datetime

    model_config = ConfigDict(from_attributes=True)

