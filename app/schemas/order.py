from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from app.models.order import DEFAULT_PRODUCT_NAME, OrderStatus
from app.schemas.customer import CustomerResponse


class OrderBase(BaseModel):
    product_name: str = Field(
        default=DEFAULT_PRODUCT_NAME,
        min_length=2,
        max_length=255,
        description="Назва продукції (за замовчуванням 'Торф'яний брикет')",
    )
    quantity: Decimal = Field(..., gt=0, description="Кількість торф'яного брикету (тонн)")
    unit_price: Decimal = Field(..., ge=0, description="Ціна за тонну (грн)")
    delivery_price_per_km: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Ціна доставки за км (грн/км)",
    )
    delivery_price: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Вартість доставки в грн (якщо не розраховується за км)",
    )
    delivery_address: Optional[str] = Field(
        None,
        description="Адреса доставки (якщо не вказано - береться адреса клієнта)",
    )
    delivery_latitude: Optional[Decimal] = Field(None, ge=-90, le=90, description="Широта місця вивантаження")
    delivery_longitude: Optional[Decimal] = Field(None, ge=-180, le=180, description="Довгота місця вивантаження")
    distance_km: Optional[Decimal] = Field(None, ge=0, description="Кілометраж доставки від складу (км)")
    order_date: Optional[date] = Field(None, description="Дата замовлення (за замовчуванням поточна дата)")
    notes: Optional[str] = Field(None, description="Примітки до доставки/замовлення")


class OrderCreate(OrderBase):
    customer_id: int = Field(..., description="ID існуючого клієнта")


class OrderUpdate(BaseModel):
    quantity: Optional[Decimal] = Field(None, gt=0, description="Кількість (тонн)")
    unit_price: Optional[Decimal] = Field(None, ge=0, description="Ціна за тонну (грн)")
    delivery_price_per_km: Optional[Decimal] = Field(None, ge=0, description="Ціна доставки за км (грн/км)")
    delivery_price: Optional[Decimal] = Field(None, ge=0, description="Вартість доставки")
    delivery_address: Optional[str] = None
    delivery_latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    delivery_longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    distance_km: Optional[Decimal] = Field(None, ge=0)
    order_date: Optional[date] = None
    status: Optional[OrderStatus] = None
    notes: Optional[str] = None


class OrderResponse(BaseModel):
    id: int
    customer_id: int
    product_name: str
    quantity: Decimal
    unit_price: Decimal
    delivery_price_per_km: Optional[Decimal] = None
    delivery_price: Decimal
    total_amount: Decimal
    delivery_address: str
    delivery_latitude: Optional[Decimal] = None
    delivery_longitude: Optional[Decimal] = None
    distance_km: Optional[Decimal] = None
    order_date: Optional[date] = None
    status: OrderStatus
    notes: Optional[str] = None
    delivery_started_at: Optional[datetime] = None
    delivery_completed_at: Optional[datetime] = None
    created_at: datetime
    waze_url: Optional[str] = None
    customer: Optional[CustomerResponse] = None

    @computed_field
    def quantity_tons(self) -> Decimal:
        """Кількість тонн (синонім quantity)."""
        return self.quantity

    @computed_field
    def price_per_ton(self) -> Decimal:
        """Ціна за тонну (синонім unit_price)."""
        return self.unit_price

    @computed_field
    def product_total(self) -> Decimal:
        """Вартість товару: quantity * unit_price."""
        return (self.quantity * self.unit_price).quantize(Decimal("0.01"))

    @computed_field
    def total_price(self) -> Decimal:
        """Загальна сума (синонім total_amount)."""
        return self.total_amount

    @model_validator(mode="after")
    def ensure_order_date(self) -> "OrderResponse":
        if self.order_date is None and self.created_at is not None:
            self.order_date = self.created_at.date()
        return self

    model_config = ConfigDict(from_attributes=True)

