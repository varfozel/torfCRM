from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional
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
    quantity: Optional[Decimal] = Field(None, gt=0, description="Кількість торф'яного брикету (тонн)")
    unit_price: Optional[Decimal] = Field(None, ge=0, description="Ціна за тонну (грн)")
    quantity_tons: Optional[Decimal] = Field(None, gt=0, description="Кількість торф'яного брикету в тоннах (синонім quantity)")
    price_per_ton: Optional[Decimal] = Field(None, ge=0, description="Ціна за тонну в грн (синонім unit_price)")
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
    delivery_amount: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Вартість доставки в грн (синонім delivery_price)",
    )
    is_total_manual: Optional[bool] = Field(
        default=False,
        description="Ознака ручного встановлення фінальної суми",
    )
    manual_total_amount: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Вручну встановлена фінальна сума замовлення (грн)",
    )
    final_total_amount: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Вручну встановлена фінальна сума замовлення (синонім manual_total_amount)",
    )
    calculated_total_amount: Optional[Decimal] = Field(
        default=None,
        description="Автоматично розрахована сума (визначається виключно бекендом)",
    )
    total_amount: Optional[Decimal] = Field(
        default=None,
        description="Загальна сума (визначається бекендом на основі is_total_manual)",
    )
    total_price: Optional[Decimal] = Field(
        default=None,
        description="Загальна сума (синонім total_amount)",
    )
    product_amount: Optional[Decimal] = Field(
        default=None,
        description="Вартість товару (синонім product_total, ігнорується бекендом)",
    )
    product_total: Optional[Decimal] = Field(
        default=None,
        description="Вартість товару (ігнорується бекендом)",
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

    @model_validator(mode="before")
    @classmethod
    def resolve_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if data.get("quantity") is None and data.get("quantity_tons") is not None:
                data["quantity"] = data["quantity_tons"]
            if data.get("unit_price") is None and data.get("price_per_ton") is not None:
                data["unit_price"] = data["price_per_ton"]
            if data.get("delivery_price") is None and data.get("delivery_amount") is not None:
                data["delivery_price"] = data["delivery_amount"]
            if data.get("manual_total_amount") is None and data.get("final_total_amount") is not None:
                data["manual_total_amount"] = data["final_total_amount"]
        return data


class OrderCreate(OrderBase):
    customer_id: int = Field(..., description="ID існуючого клієнта")

    @model_validator(mode="after")
    def validate_required_fields(self) -> "OrderCreate":
        if self.quantity is None:
            raise ValueError("Поле 'quantity' (або 'quantity_tons') є обов'язковим.")
        if self.unit_price is None:
            raise ValueError("Поле 'unit_price' (або 'price_per_ton') є обов'язковим.")
        return self


class OrderUpdate(BaseModel):
    quantity: Optional[Decimal] = Field(None, gt=0, description="Кількість (тонн)")
    unit_price: Optional[Decimal] = Field(None, ge=0, description="Ціна за тонну (грн)")
    quantity_tons: Optional[Decimal] = Field(None, gt=0, description="Кількість (тонн, синонім quantity)")
    price_per_ton: Optional[Decimal] = Field(None, ge=0, description="Ціна за тонну (грн, синонім unit_price)")
    delivery_price_per_km: Optional[Decimal] = Field(None, ge=0, description="Ціна доставки за км (грн/км)")
    delivery_price: Optional[Decimal] = Field(None, ge=0, description="Вартість доставки")
    delivery_amount: Optional[Decimal] = Field(None, ge=0, description="Вартість доставки (синонім delivery_price)")
    is_total_manual: Optional[bool] = Field(None, description="Ознака ручного встановлення фінальної суми")
    manual_total_amount: Optional[Decimal] = Field(None, ge=0, description="Вручну встановлена фінальна сума замовлення (грн)")
    final_total_amount: Optional[Decimal] = Field(None, ge=0, description="Вручну встановлена фінальна сума (синонім manual_total_amount)")
    calculated_total_amount: Optional[Decimal] = Field(None, description="Розрахована сума (визначається бекендом)")
    total_amount: Optional[Decimal] = Field(None, description="Загальна сума")
    total_price: Optional[Decimal] = Field(None, description="Загальна сума (синонім total_amount)")
    product_amount: Optional[Decimal] = Field(None, description="Вартість товару (синонім product_total)")
    product_total: Optional[Decimal] = Field(None, description="Вартість товару")
    delivery_address: Optional[str] = None
    delivery_latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    delivery_longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    distance_km: Optional[Decimal] = Field(None, ge=0)
    order_date: Optional[date] = None
    status: Optional[OrderStatus] = None
    notes: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def resolve_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if data.get("quantity") is None and data.get("quantity_tons") is not None:
                data["quantity"] = data["quantity_tons"]
            if data.get("unit_price") is None and data.get("price_per_ton") is not None:
                data["unit_price"] = data["price_per_ton"]
            if data.get("delivery_price") is None and data.get("delivery_amount") is not None:
                data["delivery_price"] = data["delivery_amount"]
            if data.get("manual_total_amount") is None and data.get("final_total_amount") is not None:
                data["manual_total_amount"] = data["final_total_amount"]
        return data


class OrderResponse(BaseModel):
    id: int
    customer_id: int
    product_name: str
    quantity: Decimal
    unit_price: Decimal
    delivery_price_per_km: Optional[Decimal] = None
    delivery_price: Decimal
    total_amount: Decimal
    calculated_total_amount: Decimal = Decimal("0.00")
    is_total_manual: bool = False
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
    def final_total_amount(self) -> Decimal:
        """Фінальна сума замовлення (синонім total_amount)."""
        return self.total_amount

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
    def product_amount(self) -> Decimal:
        """Вартість товару (синонім product_total): quantity * unit_price."""
        return (self.quantity * self.unit_price).quantize(Decimal("0.01"))

    @computed_field
    def delivery_amount(self) -> Decimal:
        """Вартість доставки (синонім delivery_price)."""
        return self.delivery_price

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
