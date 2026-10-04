from decimal import Decimal
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.models.order import DEFAULT_PRODUCT_NAME, Order, OrderStatus


@pytest.mark.asyncio
async def test_create_customer(db_session: AsyncSession):
    customer = Customer(
        name="ТОВ Волинь-Агро",
        phone="+380501234567",
        address="Волинська обл., м. Луцьк, вул. Рівненська 12",
        notes="Постійний гуртовий клієнт",
    )
    db_session.add(customer)
    await db_session.commit()
    await db_session.refresh(customer)

    assert customer.id is not None
    assert customer.name == "ТОВ Волинь-Агро"
    assert customer.phone == "+380501234567"
    assert customer.created_at is not None


@pytest.mark.asyncio
async def test_create_order_with_delivery_price_and_single_product(db_session: AsyncSession):
    customer = Customer(
        name="Іван Петренко",
        phone="+380671112233",
        address="смт Маневичі, вул. Лісова 5",
    )
    db_session.add(customer)
    await db_session.commit()
    await db_session.refresh(customer)

    # 10 units at 200.00 UAH/unit + 350.00 UAH delivery = 2350.00 UAH
    quantity = Decimal("10.00")
    unit_price = Decimal("200.00")
    delivery_price = Decimal("350.00")
    product_total = quantity * unit_price  # 2000.00
    total_amount = product_total + delivery_price  # 2350.00

    order = Order(
        customer_id=customer.id,
        quantity=quantity,
        unit_price=unit_price,
        delivery_price=delivery_price,
        total_amount=total_amount,
        delivery_address="смт Маневичі, вул. Лісова 5",
        delivery_latitude=Decimal("51.299100"),
        delivery_longitude=Decimal("25.554300"),
        status=OrderStatus.NEW.value,
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    assert order.id is not None
    assert order.customer_id == customer.id
    assert order.product_name == DEFAULT_PRODUCT_NAME
    assert order.quantity == Decimal("10.00")
    assert order.unit_price == Decimal("200.00")
    assert order.product_total == Decimal("2000.00")
    assert order.delivery_price == Decimal("350.00")
    assert order.total_amount == Decimal("2350.00")
    assert order.status == OrderStatus.NEW.value
    assert order.customer.name == "Іван Петренко"


@pytest.mark.asyncio
async def test_create_order_with_free_delivery(db_session: AsyncSession):
    customer = Customer(
        name="Петро Сидоренко",
        phone="+380672223344",
        address="смт Маневичі",
    )
    db_session.add(customer)
    await db_session.commit()

    order = Order(
        customer_id=customer.id,
        quantity=Decimal("5.00"),
        unit_price=Decimal("250.00"),
        delivery_price=Decimal("0.00"),
        total_amount=Decimal("1250.00"),
        delivery_address="смт Маневичі",
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    assert order.delivery_price == Decimal("0.00")
    assert order.product_total == Decimal("1250.00")
    assert order.total_amount == Decimal("1250.00")


@pytest.mark.asyncio
async def test_customer_orders_relationship(db_session: AsyncSession):
    customer = Customer(
        name="ФГ Світанок",
        phone="+380993334455",
        address="Ковельський р-н, с. Любитів",
    )
    db_session.add(customer)
    await db_session.commit()
    await db_session.refresh(customer)

    order1 = Order(
        customer_id=customer.id,
        quantity=Decimal("10.00"),
        unit_price=Decimal("200.00"),
        delivery_price=Decimal("300.00"),
        total_amount=Decimal("2300.00"),
        delivery_address="Ковельський р-н, с. Любитів",
        status=OrderStatus.NEW.value,
    )
    order2 = Order(
        customer_id=customer.id,
        quantity=Decimal("5.00"),
        unit_price=Decimal("220.00"),
        delivery_price=Decimal("0.00"),
        total_amount=Decimal("1100.00"),
        delivery_address="Ковельський р-н, с. Любитів",
        status=OrderStatus.PLANNED.value,
    )
    customer.orders.extend([order1, order2])
    await db_session.commit()
    await db_session.refresh(customer, attribute_names=["orders"])

    assert len(customer.orders) == 2
    assert customer.orders[0].product_name == DEFAULT_PRODUCT_NAME


@pytest.mark.asyncio
async def test_cascade_delete_customer_orders(db_session: AsyncSession):
    customer = Customer(
        name="ТзОВ Агропром",
        phone="+380970001122",
        address="м. Ковель",
    )
    order = Order(
        quantity=Decimal("20.00"),
        unit_price=Decimal("180.00"),
        delivery_price=Decimal("500.00"),
        total_amount=Decimal("4100.00"),
        delivery_address="м. Ковель",
    )
    customer.orders.append(order)
    db_session.add(customer)
    await db_session.commit()

    order_id = order.id
    customer_id = customer.id

    # Delete customer
    await db_session.delete(customer)
    await db_session.commit()

    # Verify both customer and order are deleted
    cust_res = await db_session.execute(select(Customer).where(Customer.id == customer_id))
    assert cust_res.scalar_one_or_none() is None

    ord_res = await db_session.execute(select(Order).where(Order.id == order_id))
    assert ord_res.scalar_one_or_none() is None
