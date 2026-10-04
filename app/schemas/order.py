from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.models.order import DEFAULT_PRODUCT_NAME, OrderStatus
from app.schemas.customer import CustomerResponse


class OrderBase(BaseModel):
    product_name: str = Field(
        default=DEFAULT_PRODUCT_NAME,
        min_length=2,
        max_length=255,
        description="Назва продукції (за замовчуванням 'Торф'яний брикет')",
    )
    quantity: Decimal = Field(..., gt=0, description="Кількість торф'яного брикету")
    unit_price: Decimal = Field(..., ge=0, description="Ціна за одиницю на момент замовлення (грн)")
    delivery_price: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        description="Вартість доставки в грн (0 якщо безкоштовно)",
    )
    delivery_address: Optional[str] = Field(
        None,
        description="Адреса доставки (якщо не вказано - береться адреса клієнта)",
    )
    delivery_latitude: Optional[Decimal] = Field(None, ge=-90, le=90, description="Широта місця вивантаження")
    delivery_longitude: Optional[Decimal] = Field(None, ge=-180, le=180, description="Довгота місця вивантаження")
    notes: Optional[str] = Field(None, description="Примітки до доставки/замовлення")


class OrderCreate(OrderBase):
    customer_id: int = Field(..., description="ID існуючого клієнта")


class OrderUpdate(BaseModel):
    quantity: Optional[Decimal] = Field(None, gt=0, description="Кількість")
    unit_price: Optional[Decimal] = Field(None, ge=0, description="Ціна за одиницю")
    delivery_price: Optional[Decimal] = Field(None, ge=0, description="Вартість доставки")
    delivery_address: Optional[str] = None
    delivery_latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    delivery_longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    status: Optional[OrderStatus] = None
    notes: Optional[str] = None


class OrderResponse(BaseModel):
    id: int
    customer_id: int
    product_name: str
    quantity: Decimal
    unit_price: Decimal
    delivery_price: Decimal
    total_amount: Decimal
    delivery_address: str
    delivery_latitude: Optional[Decimal] = None
    delivery_longitude: Optional[Decimal] = None
    status: OrderStatus
    notes: Optional[str] = None
    delivery_started_at: Optional[datetime] = None
    delivery_completed_at: Optional[datetime] = None
    created_at: datetime
    waze_url: Optional[str] = None
    customer: Optional[CustomerResponse] = None

    @computed_field
    def product_total(self) -> Decimal:
        """Сума вартості товару (quantity * unit_price)."""
        return (self.quantity * self.unit_price).quantize(Decimal("0.01"))

    model_config = ConfigDict(from_attributes=True)
