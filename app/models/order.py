from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Optional
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BIGINT_ID

if TYPE_CHECKING:
    from app.models.customer import Customer

DEFAULT_PRODUCT_NAME = "Торф'яний брикет"


class OrderStatus(str, Enum):
    NEW = "new"
    PLANNED = "planned"
    IN_DELIVERY = "in_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(BIGINT_ID, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(
        BIGINT_ID,
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_name: Mapped[str] = mapped_column(
        String(255),
        default=DEFAULT_PRODUCT_NAME,
        server_default=DEFAULT_PRODUCT_NAME,
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    delivery_price_per_km: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )
    delivery_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        server_default="0.00",
        nullable=False,
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    calculated_total_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        server_default="0.00",
        nullable=False,
    )
    is_total_manual: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=text("false"),
        nullable=False,
    )

    delivery_address: Mapped[str] = mapped_column(Text, nullable=False)
    delivery_latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6), nullable=True)
    delivery_longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6), nullable=True)
    distance_km: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)

    order_date: Mapped[date] = mapped_column(
        Date,
        default=func.current_date(),
        server_default=func.current_date(),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default=OrderStatus.NEW.value,
        nullable=False,
        index=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    delivery_started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    delivery_completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    customer: Mapped["Customer"] = relationship(
        "Customer",
        back_populates="orders",
        lazy="selectin",
    )

    @property
    def quantity_tons(self) -> Decimal:
        return self.quantity

    @property
    def price_per_ton(self) -> Decimal:
        return self.unit_price

    @property
    def product_total(self) -> Decimal:
        """Вартість товару: quantity * unit_price."""
        return (self.quantity * self.unit_price).quantize(Decimal("0.01"))

    @property
    def product_amount(self) -> Decimal:
        """Вартість товару (синонім product_total): quantity * unit_price."""
        return self.product_total

    @property
    def delivery_amount(self) -> Decimal:
        """Вартість доставки (синонім delivery_price)."""
        return self.delivery_price

    @property
    def total_price(self) -> Decimal:
        return self.total_amount

    @property
    def final_total_amount(self) -> Decimal:
        """Фінальна сума замовлення (синонім total_amount)."""
        return self.total_amount

    def __repr__(self) -> str:
        return (
            f"<Order(id={self.id}, customer_id={self.customer_id}, "
            f"product='{self.product_name}', delivery_price={self.delivery_price}, "
            f"total_amount={self.total_amount})>"
        )
