from decimal import Decimal
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import OrderStatus
from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.schemas.order import OrderCreate
from app.services.customer_service import customer_service
from app.services.navigation import navigation_service
from app.services.order_service import order_service


@pytest.mark.asyncio
async def test_customer_service_crud_and_search(db_session: AsyncSession):
    # Create customer
    c1 = await customer_service.create_customer(
        db_session,
        CustomerCreate(
            name="Олександр Ковальчук",
            phone="+380671234567",
            address="смт Маневичі, вул. Залізнична 10",
            notes="Дзвонити перед виїздом",
        ),
    )
    assert c1.id is not None
    assert c1.name == "Олександр Ковальчук"

    c2 = await customer_service.create_customer(
        db_session,
        CustomerCreate(
            name="ТОВ Торфовик",
            phone="+380509876543",
            address="м. Луцьк, вул. Ковельська 45",
        ),
    )
    assert c2.id is not None

    # Search by partial phone
    by_phone = await customer_service.search_customers(db_session, "1234567")
    assert len(by_phone) == 1
    assert by_phone[0].id == c1.id

    # Search by partial name
    by_name = await customer_service.search_customers(db_session, "Торфовик")
    assert len(by_name) == 1
    assert by_name[0].id == c2.id

    # Update customer
    updated = await customer_service.update_customer(
        db_session,
        c1.id,
        CustomerUpdate(notes="Оновлена примітка: доставка вранці"),
    )
    assert updated is not None
    assert updated.notes == "Оновлена примітка: доставка вранці"


@pytest.mark.asyncio
async def test_order_service_creation_and_defaults(db_session: AsyncSession):
    # Create customer with coordinates
    customer = await customer_service.create_customer(
        db_session,
        CustomerCreate(
            name="Микола Васильович",
            phone="+380931112233",
            address="с. Троянівка, вул. Центральна 8",
            latitude=Decimal("51.350000"),
            longitude=Decimal("25.600000"),
        ),
    )

    # Order 1: omit delivery address and total_amount -> defaults to customer's address & auto-computed total
    order_in = OrderCreate(
        customer_id=customer.id,
        product_name="Торф верховий кислий",
        quantity=Decimal("12.50"),
        unit_price=Decimal("800.00"),
    )
    order = await order_service.create_order(db_session, order_in)

    assert order.id is not None
    assert order.delivery_address == "с. Троянівка, вул. Центральна 8"
    assert order.delivery_latitude == Decimal("51.350000")
    assert order.delivery_longitude == Decimal("25.600000")
    # Total amount = 12.50 * 800.00 = 10000.00
    assert order.total_amount == Decimal("10000.00")
    assert order.status == OrderStatus.NEW.value


@pytest.mark.asyncio
async def test_order_delivery_lifecycle(db_session: AsyncSession):
    customer = await customer_service.create_customer(
        db_session,
        CustomerCreate(
            name="Сергій",
            phone="+380951231212",
            address="м. Ковель, вул. Варшавська 3",
        ),
    )

    order_in = OrderCreate(
        customer_id=customer.id,
        product_name="Торф для лохини (кислий)",
        quantity=Decimal("20.00"),
        unit_price=Decimal("850.00"),
    )
    order = await order_service.create_order(db_session, order_in)
    assert order.status == OrderStatus.NEW.value
    assert order.delivery_started_at is None
    assert order.delivery_completed_at is None

    # 1. Start delivery
    started_order = await order_service.start_delivery(db_session, order.id)
    assert started_order.status == OrderStatus.IN_DELIVERY.value
    assert started_order.delivery_started_at is not None
    assert started_order.delivery_completed_at is None

    # 2. Complete delivery
    completed_order = await order_service.complete_delivery(db_session, order.id)
    assert completed_order.status == OrderStatus.DELIVERED.value
    assert completed_order.delivery_completed_at is not None

    # 3. Invalid transition: cannot start an already delivered order
    with pytest.raises(ValueError, match="вже доставлено"):
        await order_service.start_delivery(db_session, order.id)


@pytest.mark.asyncio
async def test_order_cancellation(db_session: AsyncSession):
    customer = await customer_service.create_customer(
        db_session,
        CustomerCreate(
            name="Андрій",
            phone="+380678889900",
            address="смт Маневичі",
        ),
    )
    order = await order_service.create_order(
        db_session,
        OrderCreate(
            customer_id=customer.id,
            product_name="Брикет торф'яний",
            quantity=Decimal("3.00"),
            unit_price=Decimal("1600.00"),
        ),
    )
    cancelled = await order_service.cancel_order(db_session, order.id, notes="Клієнт змінив плани")
    assert cancelled.status == OrderStatus.CANCELLED.value
    assert "Клієнт змінив плани" in (cancelled.notes or "")

    with pytest.raises(ValueError, match="скасоване замовлення"):
        await order_service.complete_delivery(db_session, order.id)


def test_navigation_service():
    # Test Waze coordinate generation
    url_coords = navigation_service.generate_waze_url(
        latitude=Decimal("51.298100"),
        longitude=Decimal("25.553200"),
    )
    assert url_coords == "https://waze.com/ul?ll=51.298100,25.553200&navigate=yes"

    # Test Waze address fallback
    url_addr = navigation_service.generate_waze_url(address="смт Маневичі, Волинь")
    assert "https://waze.com/ul?q=" in url_addr
    assert "navigate=yes" in url_addr

    # Test coordinate parser from Viber-copied text
    # 1. Plain coordinates
    lat1, lon1 = navigation_service.parse_coordinates("51.2981, 25.5532")
    assert lat1 == Decimal("51.2981")
    assert lon1 == Decimal("25.5532")

    # 2. Google Maps URL pin
    lat2, lon2 = navigation_service.parse_coordinates(
        "https://www.google.com/maps?q=51.350123,25.612345"
    )
    assert lat2 == Decimal("51.350123")
    assert lon2 == Decimal("25.612345")

    # 3. Warehouse info centralized
    wh = navigation_service.warehouse_info
    assert "name" in wh
    assert "latitude" in wh
    assert "longitude" in wh
