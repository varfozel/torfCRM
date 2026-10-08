from decimal import Decimal
import pytest
from httpx import AsyncClient

from app.models.order import DEFAULT_PRODUCT_NAME


@pytest.mark.asyncio
async def test_health_and_root(client: AsyncClient):
    resp_root = await client.get("/")
    assert resp_root.status_code == 200
    assert resp_root.json()["status"] == "online"

    resp_health = await client.get("/health")
    assert resp_health.status_code == 200
    assert resp_health.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_warehouse_location_endpoint(client: AsyncClient):
    resp = await client.get("/api/v1/warehouse")
    assert resp.status_code == 200
    data = resp.json()
    assert "name" in data
    assert "address" in data
    assert "latitude" in data
    assert "longitude" in data


@pytest.mark.asyncio
async def test_customer_api_crud(client: AsyncClient):
    # 1. Create customer
    payload = {
        "name": "ФОП Шевченко",
        "phone": "+380679998877",
        "address": "м. Луцьк, вул. Незалежності 14",
        "latitude": 51.298500,
        "longitude": 25.554000,
        "notes": "Постійний замовник",
    }
    create_resp = await client.post("/api/v1/customers/", json=payload)
    assert create_resp.status_code == 201
    created = create_resp.json()
    customer_id = created["id"]
    assert created["name"] == payload["name"]

    # 2. Get customer by ID
    get_resp = await client.get(f"/api/v1/customers/{customer_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["phone"] == payload["phone"]

    # 3. Search customer by phone
    search_resp = await client.get("/api/v1/customers/?q=9998877")
    assert search_resp.status_code == 200
    results = search_resp.json()
    assert len(results) == 1
    assert results[0]["id"] == customer_id

    # 4. Update customer
    patch_resp = await client.patch(
        f"/api/v1/customers/{customer_id}",
        json={"notes": "Оновлено: вивантажувати біля воріт"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["notes"] == "Оновлено: вивантажувати біля воріт"


@pytest.mark.asyncio
async def test_order_api_lifecycle_and_totals(client: AsyncClient):
    # 1. Create customer
    cust_payload = {
        "name": "Василь Кравчук",
        "phone": "+380504443322",
        "address": "с. Прилісне, вул. Сонячна 21",
        "latitude": 51.370000,
        "longitude": 25.520000,
    }
    cust_resp = await client.post("/api/v1/customers/", json=cust_payload)
    customer_id = cust_resp.json()["id"]

    # 2. Create order: 10 units at 200.00 + 350.00 delivery = 2350.00
    order_payload = {
        "customer_id": customer_id,
        "quantity": 10.0,
        "unit_price": 200.0,
        "delivery_price": 350.0,
    }
    order_resp = await client.post("/api/v1/orders/", json=order_payload)
    assert order_resp.status_code == 201
    order_data = order_resp.json()
    order_id = order_data["id"]

    assert order_data["product_name"] == DEFAULT_PRODUCT_NAME
    assert Decimal(order_data["product_total"]) == Decimal("2000.00")
    assert Decimal(order_data["delivery_price"]) == Decimal("350.00")
    assert Decimal(order_data["total_amount"]) == Decimal("2350.00")
    assert order_data["delivery_address"] == cust_payload["address"]
    assert order_data["status"] == "new"
    assert order_data["waze_url"] is not None

    # 3. Patch order delivery price to 400 -> total becomes 2400.00
    patch_resp = await client.patch(
        f"/api/v1/orders/{order_id}",
        json={"delivery_price": 400.0},
    )
    assert patch_resp.status_code == 200
    patched = patch_resp.json()
    assert Decimal(patched["delivery_price"]) == Decimal("400.00")
    assert Decimal(patched["total_amount"]) == Decimal("2400.00")

    # 4. Start delivery
    start_resp = await client.post(f"/api/v1/orders/{order_id}/start-delivery")
    assert start_resp.status_code == 200
    started_data = start_resp.json()
    assert started_data["status"] == "in_delivery"
    assert started_data["delivery_started_at"] is not None

    # 5. Complete delivery
    complete_resp = await client.post(f"/api/v1/orders/{order_id}/complete-delivery")
    assert complete_resp.status_code == 200
    completed_data = complete_resp.json()
    assert completed_data["status"] == "delivered"
    assert completed_data["delivery_completed_at"] is not None

    # 6. Bad request when starting already delivered order
    invalid_start = await client.post(f"/api/v1/orders/{order_id}/start-delivery")
    assert invalid_start.status_code == 400


@pytest.mark.asyncio
async def test_order_api_negative_validations(client: AsyncClient):
    cust_resp = await client.post(
        "/api/v1/customers/",
        json={"name": "Тест Помилки", "phone": "+380671112233", "address": "м. Ковель"},
    )
    customer_id = cust_resp.json()["id"]

    # Negative delivery price
    neg_deliv = await client.post(
        "/api/v1/orders/",
        json={
            "customer_id": customer_id,
            "quantity": 10.0,
            "unit_price": 200.0,
            "delivery_price": -50.0,
        },
    )
    assert neg_deliv.status_code in [400, 422]

    # Negative quantity
    neg_qty = await client.post(
        "/api/v1/orders/",
        json={
            "customer_id": customer_id,
            "quantity": -5.0,
            "unit_price": 200.0,
        },
    )
    assert neg_qty.status_code in [400, 422]


@pytest.mark.asyncio
async def test_order_date_and_distance_api(client: AsyncClient):
    # Create customer
    cust_resp = await client.post(
        "/api/v1/customers/",
        json={"name": "Олександр", "phone": "+380509990011", "address": "м. Луцьк"},
    )
    customer_id = cust_resp.json()["id"]

    # Create order with explicit order_date and distance_km
    order_resp = await client.post(
        "/api/v1/orders/",
        json={
            "customer_id": customer_id,
            "quantity": 2.0,
            "unit_price": 12500.0,
            "delivery_price": 500.0,
            "delivery_address": "м. Луцьк, вул. Рівненська 45",
            "order_date": "2026-10-15",
            "distance_km": 42.5,
        },
    )
    assert order_resp.status_code == 201
    data = order_resp.json()
    assert data["order_date"] == "2026-10-15"
    assert float(data["total_amount"]) == 25500.0  # 2 * 12500 + 500 delivery

    # Update order_date and delivery_price_per_km
    patch_resp = await client.patch(
        f"/api/v1/orders/{data['id']}",
        json={"order_date": "2026-10-20", "distance_km": 45.0, "delivery_price_per_km": 350.0},
    )
    assert patch_resp.status_code == 200
    patched = patch_resp.json()
    assert patched["order_date"] == "2026-10-20"
    assert float(patched["distance_km"]) == 45.0
    assert float(patched["delivery_price_per_km"]) == 350.0
    # 2 * 12500 + 45.0 * 350.0 = 25000 + 15750 = 40750
    assert float(patched["delivery_price"]) == 15750.0
    assert float(patched["total_amount"]) == 40750.0


@pytest.mark.asyncio
async def test_calculate_route_api(client: AsyncClient):
    resp = await client.post(
        "/api/v1/navigation/calculate-route",
        json={"latitude": 50.7472, "longitude": 25.3254},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["distance_km"] is not None
    assert "waze_url" in data


@pytest.mark.asyncio
async def test_order_api_calculation_create_and_update_with_multiple_tons(client: AsyncClient):
    """
    Test CREATE and UPDATE via REST API with:
    1. quantity=2, unit_price=12500, distance_km=80, delivery_price_per_km=70 -> 30600
       (and verify untrusted total_amount=18100 in payload is ignored)
    2. PATCH quantity=1.5, distance_km=68, delivery_price_per_km=70 -> 23510
    """
    # 1. Create customer
    cust_resp = await client.post(
        "/api/v1/customers/",
        json={"name": "Дмитро", "phone": "+380509998877", "address": "м. Луцьк"},
    )
    assert cust_resp.status_code == 201
    cust_id = cust_resp.json()["id"]

    # 2. CREATE order: 2 tons * 12500 + 80 km * 70 = 25000 + 5600 = 30600
    # Include malicious / erroneous total_amount=18100 in JSON payload
    create_resp = await client.post(
        "/api/v1/orders/",
        json={
            "customer_id": cust_id,
            "quantity": 2.0,
            "unit_price": 12500.0,
            "distance_km": 80.0,
            "delivery_price_per_km": 70.0,
            "delivery_price": 5600.0,
            "total_amount": 18100.0,  # Must be ignored!
        },
    )
    assert create_resp.status_code == 201
    created_data = create_resp.json()
    order_id = created_data["id"]

    assert Decimal(str(created_data["quantity"])) == Decimal("2.00")
    assert Decimal(str(created_data["unit_price"])) == Decimal("12500.00")
    assert Decimal(str(created_data["product_total"])) == Decimal("25000.00")
    assert Decimal(str(created_data["product_amount"])) == Decimal("25000.00")
    assert Decimal(str(created_data["distance_km"])) == Decimal("80.00")
    assert Decimal(str(created_data["delivery_price_per_km"])) == Decimal("70.00")
    assert Decimal(str(created_data["delivery_price"])) == Decimal("5600.00")
    assert Decimal(str(created_data["delivery_amount"])) == Decimal("5600.00")
    assert Decimal(str(created_data["total_amount"])) == Decimal("30600.00")

    # 3. UPDATE order: 1.5 tons * 12500 + 68 km * 70 = 18750 + 4760 = 23510
    # Include erroneous total_amount=99999.0 to verify backend recalculates
    patch_resp = await client.patch(
        f"/api/v1/orders/{order_id}",
        json={
            "quantity": 1.5,
            "distance_km": 68.0,
            "delivery_price_per_km": 70.0,
            "total_amount": 99999.0,  # Must be ignored!
        },
    )
    assert patch_resp.status_code == 200
    patched_data = patch_resp.json()

    assert Decimal(str(patched_data["quantity"])) == Decimal("1.50")
    assert Decimal(str(patched_data["unit_price"])) == Decimal("12500.00")
    assert Decimal(str(patched_data["product_total"])) == Decimal("18750.00")
    assert Decimal(str(patched_data["product_amount"])) == Decimal("18750.00")
    assert Decimal(str(patched_data["distance_km"])) == Decimal("68.00")
    assert Decimal(str(patched_data["delivery_price_per_km"])) == Decimal("70.00")
    assert Decimal(str(patched_data["delivery_price"])) == Decimal("4760.00")
    assert Decimal(str(patched_data["delivery_amount"])) == Decimal("4760.00")
    assert Decimal(str(patched_data["total_amount"])) == Decimal("23510.00")

