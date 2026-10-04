from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class CustomerBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="ПІБ або назва організації")
    phone: str = Field(..., min_length=6, max_length=50, description="Номер телефону")
    address: str = Field(..., min_length=2, description="Адреса доставки або реєстрації")
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90, description="Широта")
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180, description="Довгота")
    notes: Optional[str] = Field(None, description="Примітки про клієнта")


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(None, min_length=6, max_length=50)
    address: Optional[str] = Field(None, min_length=2)
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    notes: Optional[str] = None


class CustomerResponse(CustomerBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
