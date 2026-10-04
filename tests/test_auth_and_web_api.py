from decimal import Decimal
import pytest
from httpx import AsyncClient

from app.config import get_settings

settings = get_settings()


@pytest.mark.asyncio
async def test_auth_login_and_me(client: AsyncClient):
    # 1. Failed login with wrong password
    bad_login = await client.post(
        "/api/v1/auth/login",
        json={"username": settings.MANAGER_USERNAME, "password": "wrong_password"},
    )
    assert bad_login.status_code == 401

    # 2. Successful login
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": settings.MANAGER_USERNAME, "password": settings.MANAGER_PASSWORD},
    )
    assert login_resp.status_code == 200
    data = login_resp.json()
    assert "access_token" in data
    token = data["access_token"]
    assert data["manager"]["username"] == settings.MANAGER_USERNAME

    # 3. /auth/me with Bearer token
    me_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["username"] == settings.MANAGER_USERNAME

    # 4. /auth/me without token -> 401
    unauth_resp = await client.get("/api/v1/auth/me")
    assert unauth_resp.status_code == 401


@pytest.mark.asyncio
async def test_analytics_dashboard_endpoint(client: AsyncClient):
    # Create customer and order
    cust_resp = await client.post(
        "/api/v1/customers/",
        json={
            "name": "Аналітика Клієнт",
            "phone": "+380501234567",
            "address": "м. Луцьк, вул. Ковельська 45",
            "latitude": 50.7593,
            "longitude": 25.3424,
        },
    )
    assert cust_resp.status_code == 201
    cust_id = cust_resp.json()["id"]

    order_resp = await client.post(
        "/api/v1/orders/",
        json={
            "customer_id": cust_id,
            "quantity": 15.0,
            "unit_price": 3800.0,
            "delivery_price": 500.0,
        },
    )
    assert order_resp.status_code == 201

    # Query dashboard data
    dash_resp = await client.get("/api/v1/analytics/dashboard?period=month")
    assert dash_resp.status_code == 200
    dash = dash_resp.json()
    assert "kpi" in dash
    assert dash["kpi"]["total_customers"] >= 1
    assert dash["kpi"]["new_orders_count"] >= 1
    assert dash["kpi"]["period_revenue"] > 0
    assert "status_distribution" in dash
    assert "sales_chart" in dash
    assert "map_deliveries" in dash
    assert len(dash["map_deliveries"]) >= 1


@pytest.mark.asyncio
async def test_products_catalog(client: AsyncClient):
    resp = await client.get("/api/v1/products/")
    assert resp.status_code == 200
    products = resp.json()
    assert len(products) >= 3
    assert any("Торф'яний брикет" in p["name"] for p in products)

    # Single product
    first_id = products[0]["id"]
    single = await client.get(f"/api/v1/products/{first_id}")
    assert single.status_code == 200
    assert single.json()["id"] == first_id


@pytest.mark.asyncio
async def test_settings_endpoint(client: AsyncClient):
    resp = await client.get("/api/v1/settings/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["project_name"] == settings.PROJECT_NAME
    assert data["currency"] == "UAH"
    assert "warehouse" in data
    assert data["warehouse"]["name"] == settings.WAREHOUSE_NAME


@pytest.mark.asyncio
async def test_orders_search_and_planning(client: AsyncClient):
    # Create customer and order
    cust_resp = await client.post(
        "/api/v1/customers/",
        json={
            "name": "Оксана Мельник",
            "phone": "+380671239876",
            "address": "смт Маневичі, пров. Тихий 3",
        },
    )
    cust_id = cust_resp.json()["id"]

    order_resp = await client.post(
        "/api/v1/orders/",
        json={
            "customer_id": cust_id,
            "quantity": 5.0,
            "unit_price": 4000.0,
            "delivery_price": 200.0,
        },
    )
    order_id = order_resp.json()["id"]

    # Plan order
    plan_resp = await client.post(f"/api/v1/orders/{order_id}/plan")
    assert plan_resp.status_code == 200
    assert plan_resp.json()["status"] == "planned"

    # Search orders by customer name
    search_resp = await client.get("/api/v1/orders/?q=Оксана")
    assert search_resp.status_code == 200
    assert "X-Total-Count" in search_resp.headers
    results = search_resp.json()
    assert any(o["id"] == order_id for o in results)

    # Customer detail with order history
    detail_resp = await client.get(f"/api/v1/customers/{cust_id}/detail")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["orders_count"] >= 1
    assert len(detail["orders"]) >= 1
