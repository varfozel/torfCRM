from decimal import Decimal
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import DEFAULT_PRODUCT_NAME, OrderStatus
from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.schemas.order import OrderCreate, OrderUpdate
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
            address="м. Луцьк, вул. Залізнична 10",
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
async def test_order_creation_formula_and_defaults(db_session: AsyncSession):
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

    # Test formula from user specification:
    # Quantity: 10, Unit price: 200, Delivery: 350
    # product_total = 10 * 200 = 2000
    # total_amount = 2000 + 350 = 2350
    order_in = OrderCreate(
        customer_id=customer.id,
        quantity=Decimal("10.00"),
        unit_price=Decimal("200.00"),
        delivery_price=Decimal("350.00"),
    )
    order = await order_service.create_order(db_session, order_in)

    assert order.id is not None
    assert order.product_name == DEFAULT_PRODUCT_NAME
    assert order.quantity == Decimal("10.00")
    assert order.unit_price == Decimal("200.00")
    assert order.product_total == Decimal("2000.00")
    assert order.delivery_price == Decimal("350.00")
    assert order.total_amount == Decimal("2350.00")

    # Verify address and coords inherited from customer
    assert order.delivery_address == "с. Троянівка, вул. Центральна 8"
    assert order.delivery_latitude == Decimal("51.350000")
    assert order.delivery_longitude == Decimal("25.600000")
    assert order.status == OrderStatus.NEW.value


@pytest.mark.asyncio
async def test_order_creation_per_km_formula(db_session: AsyncSession):
    customer = await customer_service.create_customer(
        db_session,
        CustomerCreate(
            name="Іван Тестовий",
            phone="+380991112233",
            address="с. Підгайці",
        ),
    )

    # User specification example:
    # 2 tons * 12500 грн + 60.1 km * 350 грн/km = 25000 + 21035 = 46035 грн
    order_in = OrderCreate(
        customer_id=customer.id,
        quantity=Decimal("2.00"),
        unit_price=Decimal("12500.00"),
        distance_km=Decimal("60.10"),
        delivery_price_per_km=Decimal("350.00"),
    )
    order = await order_service.create_order(db_session, order_in)

    assert order.quantity == Decimal("2.00")
    assert order.unit_price == Decimal("12500.00")
    assert order.product_total == Decimal("25000.00")
    assert order.distance_km == Decimal("60.10")
    assert order.delivery_price_per_km == Decimal("350.00")
    assert order.delivery_price == Decimal("21035.00")
    assert order.total_amount == Decimal("46035.00")


@pytest.mark.asyncio
async def test_order_free_delivery(db_session: AsyncSession):
    customer = await customer_service.create_customer(
        db_session,
        CustomerCreate(
            name="Ольга",
            phone="+380670001122",
            address="м. Луцьк",
        ),
    )

    # Free delivery (delivery_price = 0)
    order_in = OrderCreate(
        customer_id=customer.id,
        quantity=Decimal("5.00"),
        unit_price=Decimal("220.00"),
        delivery_price=Decimal("0.00"),
    )
    order = await order_service.create_order(db_session, order_in)
    assert order.delivery_price == Decimal("0.00")
    assert order.product_total == Decimal("1100.00")
    assert order.total_amount == Decimal("1100.00")


@pytest.mark.asyncio
async def test_order_validation_errors(db_session: AsyncSession):
    customer = await customer_service.create_customer(
        db_session,
        CustomerCreate(
            name="Тест Валідація",
            phone="+380509990011",
            address="м. Луцьк",
        ),
    )

    # 1. Pydantic schema validation rejects negative delivery price
    with pytest.raises(ValueError):
        OrderCreate(
            customer_id=customer.id,
            quantity=Decimal("10.00"),
            unit_price=Decimal("200.00"),
            delivery_price=Decimal("-50.00"),
        )

    # 2. Service level validation also rejects negative delivery price if constructed directly
    with pytest.raises(ValueError, match="доставки не може бути від'ємною"):
        invalid_order = OrderCreate.model_construct(
            customer_id=customer.id,
            product_name=DEFAULT_PRODUCT_NAME,
            quantity=Decimal("10.00"),
            unit_price=Decimal("200.00"),
            delivery_price=Decimal("-50.00"),
            delivery_address="м. Луцьк",
        )
        await order_service.create_order(db_session, invalid_order)

    # 3. Rejects zero or negative quantity
    with pytest.raises(ValueError):
        OrderCreate(
            customer_id=customer.id,
            quantity=Decimal("0.00"),
            unit_price=Decimal("200.00"),
            delivery_price=Decimal("100.00"),
        )

    with pytest.raises(ValueError, match="більшою за нуль"):
        invalid_qty = OrderCreate.model_construct(
            customer_id=customer.id,
            product_name=DEFAULT_PRODUCT_NAME,
            quantity=Decimal("0.00"),
            unit_price=Decimal("200.00"),
            delivery_price=Decimal("100.00"),
            delivery_address="м. Луцьк",
        )
        await order_service.create_order(db_session, invalid_qty)

    # 4. Rejects negative unit price
    with pytest.raises(ValueError):
        OrderCreate(
            customer_id=customer.id,
            quantity=Decimal("10.00"),
            unit_price=Decimal("-10.00"),
        )


@pytest.mark.asyncio
async def test_order_update_recalculates_totals(db_session: AsyncSession):
    customer = await customer_service.create_customer(
        db_session,
        CustomerCreate(
            name="Григорій",
            phone="+380671239876",
            address="м. Луцьк",
        ),
    )
    order = await order_service.create_order(
        db_session,
        OrderCreate(
            customer_id=customer.id,
            quantity=Decimal("10.00"),
            unit_price=Decimal("200.00"),
            delivery_price=Decimal("300.00"),
        ),
    )
    assert order.total_amount == Decimal("2300.00")

    # Update delivery price to 400
    updated = await order_service.update_order(
        db_session,
        order.id,
        OrderUpdate(delivery_price=Decimal("400.00")),
    )
    assert updated.delivery_price == Decimal("400.00")
    assert updated.total_amount == Decimal("2400.00")

    # Update quantity to 15
    updated2 = await order_service.update_order(
        db_session,
        order.id,
        OrderUpdate(quantity=Decimal("15.00")),
    )
    assert updated2.quantity == Decimal("15.00")
    # 15 * 200 + 400 = 3400.00
    assert updated2.total_amount == Decimal("3400.00")


@pytest.mark.asyncio
async def test_order_creation_and_update_with_multiple_tons_and_untrusted_total(db_session: AsyncSession):
    """
    Verification of exact formula:
      product_amount = quantity_tons * price_per_ton
      delivery_amount = distance_km * delivery_price_per_km
      total_amount = product_amount + delivery_amount

    Backend must NOT trust frontend-provided total_amount and must recalculate itself.
    """
    customer = await customer_service.create_customer(
        db_session,
        CustomerCreate(
            name="Олександр",
            phone="+380501234567",
            address="м. Луцьк",
        ),
    )

    # 1. CREATE test case 1:
    # quantity_tons = 2, price_per_ton = 12500, distance_km = 80, delivery_price_per_km = 70
    # Expected: product_amount = 25000, delivery_amount = 5600, total_amount = 30600
    # Pass untrusted total_amount=18100 (bug symptom) to verify backend ignores it
    order_in1 = OrderCreate(
        customer_id=customer.id,
        quantity=Decimal("2.00"),
        unit_price=Decimal("12500.00"),
        distance_km=Decimal("80.00"),
        delivery_price_per_km=Decimal("70.00"),
        total_amount=Decimal("18100.00"),
    )
    order1 = await order_service.create_order(db_session, order_in1)

    assert order1.quantity == Decimal("2.00")
    assert order1.unit_price == Decimal("12500.00")
    assert order1.product_total == Decimal("25000.00")
    assert order1.product_amount == Decimal("25000.00")
    assert order1.distance_km == Decimal("80.00")
    assert order1.delivery_price_per_km == Decimal("70.00")
    assert order1.delivery_price == Decimal("5600.00")
    assert order1.delivery_amount == Decimal("5600.00")
    assert order1.total_amount == Decimal("30600.00")

    # 2. CREATE test case 2:
    # quantity_tons = 1.5, price_per_ton = 12500, distance_km = 68, delivery_price_per_km = 70
    # Expected: product_amount = 18750, delivery_amount = 4760, total_amount = 23510
    order_in2 = OrderCreate(
        customer_id=customer.id,
        quantity=Decimal("1.50"),
        unit_price=Decimal("12500.00"),
        distance_km=Decimal("68.00"),
        delivery_price_per_km=Decimal("70.00"),
    )
    order2 = await order_service.create_order(db_session, order_in2)

    assert order2.quantity == Decimal("1.50")
    assert order2.unit_price == Decimal("12500.00")
    assert order2.product_total == Decimal("18750.00")
    assert order2.product_amount == Decimal("18750.00")
    assert order2.distance_km == Decimal("68.00")
    assert order2.delivery_price_per_km == Decimal("70.00")
    assert order2.delivery_price == Decimal("4760.00")
    assert order2.delivery_amount == Decimal("4760.00")
    assert order2.total_amount == Decimal("23510.00")

    # 3. UPDATE test case:
    # Create an initial order with 1 ton
    order_init = await order_service.create_order(
        db_session,
        OrderCreate(
            customer_id=customer.id,
            quantity=Decimal("1.00"),
            unit_price=Decimal("12500.00"),
            delivery_price=Decimal("0.00"),
        ),
    )
    assert order_init.total_amount == Decimal("12500.00")

    # Now simulate EditOrderModal update with quantity=2, price=12500, distance_km=80, rate=70
    # Specifically ensure unit_price is NOT treated as total product cost, but multiplied by quantity (2 * 12500 = 25000)
    # Also pass untrusted total_amount=18100 to prove backend recalculates it to 30600
    updated_order = await order_service.update_order(
        db_session,
        order_init.id,
        OrderUpdate(
            quantity=Decimal("2.00"),
            unit_price=Decimal("12500.00"),
            distance_km=Decimal("80.00"),
            delivery_price_per_km=Decimal("70.00"),
            delivery_price=Decimal("5600.00"),
            total_amount=Decimal("18100.00"),
        ),
    )
    assert updated_order.quantity == Decimal("2.00")
    assert updated_order.unit_price == Decimal("12500.00")
    assert updated_order.product_total == Decimal("25000.00")
    assert updated_order.product_amount == Decimal("25000.00")
    assert updated_order.distance_km == Decimal("80.00")
    assert updated_order.delivery_price_per_km == Decimal("70.00")
    assert updated_order.delivery_price == Decimal("5600.00")
    assert updated_order.delivery_amount == Decimal("5600.00")
    assert updated_order.total_amount == Decimal("30600.00")  # (2 * 12500) + (80 * 70) = 30600, NOT 18100

    # 4. UPDATE test case with decimal quantity: 1.5 tons, 68 km, 70 грн/км
    updated_order2 = await order_service.update_order(
        db_session,
        order_init.id,
        OrderUpdate(
            quantity=Decimal("1.50"),
            distance_km=Decimal("68.00"),
            delivery_price_per_km=Decimal("70.00"),
        ),
    )
    assert updated_order2.quantity == Decimal("1.50")
    assert updated_order2.product_total == Decimal("18750.00")
    assert updated_order2.delivery_price == Decimal("4760.00")
    assert updated_order2.total_amount == Decimal("23510.00")


@pytest.mark.asyncio
async def test_manual_total_amount_lifecycle(db_session: AsyncSession):
    """
    Test manual total amount functionality as requested:
    1. Auto calculation: 2 t * 12500 + 80 km * 70 = 30600.
    2. Manual total: auto = 30600, manager sets 30000 -> final_total_amount = 30000, is_total_manual = True.
    3. Parameter changes during manual total: auto amount changes, but final_total_amount stays 30000.
    4. Reset to auto: final_total_amount becomes equal to calculated_total_amount again.
    5. Validation: negative manual total rejected.
    """
    customer = await customer_service.create_customer(
        db_session,
        CustomerCreate(
            name="Віктор",
            phone="+380971234567",
            address="м. Володимир",
        ),
    )

    # 1. Автоматичний розрахунок за замовчуванням
    order = await order_service.create_order(
        db_session,
        OrderCreate(
            customer_id=customer.id,
            quantity=Decimal("2.00"),
            unit_price=Decimal("12500.00"),
            distance_km=Decimal("80.00"),
            delivery_price_per_km=Decimal("70.00"),
        ),
    )
    assert order.calculated_total_amount == Decimal("30600.00")
    assert order.total_amount == Decimal("30600.00")
    assert order.final_total_amount == Decimal("30600.00")
    assert order.is_total_manual is False

    # 2. Менеджер встановлює ручну суму 30 000
    order_manual = await order_service.update_order(
        db_session,
        order.id,
        OrderUpdate(
            is_total_manual=True,
            manual_total_amount=Decimal("30000.00"),
        ),
    )
    assert order_manual.is_total_manual is True
    assert order_manual.calculated_total_amount == Decimal("30600.00")
    assert order_manual.total_amount == Decimal("30000.00")
    assert order_manual.final_total_amount == Decimal("30000.00")

    # 3. Зміна параметрів (кількість збільшилась до 3 тонн, кілометраж до 100 км):
    # Новий автоматичний розрахунок: 3 * 12500 + 100 * 70 = 37500 + 7000 = 44500.
    # Але оскільки діє ручний режим, фінальна сума залишається 30000!
    order_params_changed = await order_service.update_order(
        db_session,
        order.id,
        OrderUpdate(
            quantity=Decimal("3.00"),
            distance_km=Decimal("100.00"),
        ),
    )
    assert order_params_changed.is_total_manual is True
    assert order_params_changed.calculated_total_amount == Decimal("44500.00")
    assert order_params_changed.total_amount == Decimal("30000.00")
    assert order_params_changed.final_total_amount == Decimal("30000.00")

    # 4. Повернення до автоматичного розрахунку:
    # Менеджер натискає «Повернути автоматичний розрахунок» (is_total_manual = False)
    order_reset = await order_service.update_order(
        db_session,
        order.id,
        OrderUpdate(
            is_total_manual=False,
        ),
    )
    assert order_reset.is_total_manual is False
    assert order_reset.calculated_total_amount == Decimal("44500.00")
    assert order_reset.total_amount == Decimal("44500.00")
    assert order_reset.final_total_amount == Decimal("44500.00")

    # 5. Створення замовлення одразу з ручною сумою:
    order_created_manual = await order_service.create_order(
        db_session,
        OrderCreate(
            customer_id=customer.id,
            quantity=Decimal("2.00"),
            unit_price=Decimal("12500.00"),
            distance_km=Decimal("80.00"),
            delivery_price_per_km=Decimal("70.00"),
            is_total_manual=True,
            manual_total_amount=Decimal("29500.00"),
        ),
    )
    assert order_created_manual.is_total_manual is True
    assert order_created_manual.calculated_total_amount == Decimal("30600.00")
    assert order_created_manual.total_amount == Decimal("29500.00")

    # 6. Валідація: від'ємна сума відхиляється
    with pytest.raises(ValueError):
        await order_service.update_order(
            db_session,
            order.id,
            OrderUpdate(
                is_total_manual=True,
                manual_total_amount=Decimal("-500.00"),
            ),
        )


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
        quantity=Decimal("20.00"),
        unit_price=Decimal("200.00"),
        delivery_price=Decimal("400.00"),
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
            address="м. Луцьк",
        ),
    )
    order = await order_service.create_order(
        db_session,
        OrderCreate(
            customer_id=customer.id,
            quantity=Decimal("3.00"),
            unit_price=Decimal("210.00"),
            delivery_price=Decimal("150.00"),
        ),
    )
    cancelled = await order_service.cancel_order(db_session, order.id, notes="Клієнт змінив плани")
    assert cancelled.status == OrderStatus.CANCELLED.value
    assert "Клієнт змінив плани" in (cancelled.notes or "")

    with pytest.raises(ValueError, match="скасоване замовлення"):
        await order_service.complete_delivery(db_session, order.id)


def test_navigation_service():
    url_coords = navigation_service.generate_waze_url(
        latitude=Decimal("51.298100"),
        longitude=Decimal("25.553200"),
    )
    assert url_coords == "https://waze.com/ul?ll=51.298100,25.553200&navigate=yes"

    url_addr = navigation_service.generate_waze_url(address="м. Луцьк, Волинь")
    assert "https://waze.com/ul?q=" in url_addr
    assert "navigate=yes" in url_addr

    lat1, lon1 = navigation_service.parse_coordinates("51.2981, 25.5532")
    assert lat1 == Decimal("51.2981")
    assert lon1 == Decimal("25.5532")

    lat2, lon2 = navigation_service.parse_coordinates(
        "https://www.google.com/maps?q=51.350123,25.612345"
    )
    assert lat2 == Decimal("51.350123")
    assert lon2 == Decimal("25.612345")

    wh = navigation_service.warehouse_info
    assert "name" in wh
    assert "latitude" in wh
    assert "longitude" in wh
