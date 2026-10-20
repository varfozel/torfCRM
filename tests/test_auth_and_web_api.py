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
            "address": "м. Луцьк, пров. Тихий 3",
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


@pytest.mark.asyncio
async def test_calendar_unavailable_dates_api(client: AsyncClient):
    target_date = "2026-10-30"

    # 1. Authorization checks (must reject without Bearer token)
    unauth_post = await client.post(
        "/api/v1/calendar/unavailable-dates",
        json={"date": target_date, "reason": "Вихідний день водія"},
    )
    assert unauth_post.status_code == 401

    unauth_del = await client.delete(f"/api/v1/calendar/unavailable-dates/{target_date}")
    assert unauth_del.status_code == 401

    # 2. Login as manager to obtain JWT token
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": settings.MANAGER_USERNAME, "password": settings.MANAGER_PASSWORD},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # 3. Create unavailable date successfully
    create_resp = await client.post(
        "/api/v1/calendar/unavailable-dates",
        json={"date": target_date, "reason": "Вихідний день водія"},
        headers=auth_headers,
    )
    assert create_resp.status_code == 201
    created_data = create_resp.json()
    assert created_data["date"] == target_date
    assert created_data["reason"] == "Вихідний день водія"
    assert "id" in created_data
    assert "created_at" in created_data

    # 4. Duplicate date prevention (must reject second insertion with 400)
    dup_resp = await client.post(
        "/api/v1/calendar/unavailable-dates",
        json={"date": target_date, "reason": "Дублювання дати"},
        headers=auth_headers,
    )
    assert dup_resp.status_code == 400
    assert "вже позначена" in dup_resp.json()["detail"]

    # 5. List unavailable dates
    list_resp = await client.get("/api/v1/calendar/unavailable-dates")
    assert list_resp.status_code == 200
    dates_list = list_resp.json()
    assert any(d["date"] == target_date for d in dates_list)

    # 6. CRITICAL: Order creation on unavailable date must NOT be blocked
    cust_resp = await client.post(
        "/api/v1/customers/",
        json={
            "name": "Клієнт на небажану дату",
            "phone": "+380509998877",
            "address": "м. Луцьк, вул. Рівненська 12",
        },
    )
    assert cust_resp.status_code == 201
    cust_id = cust_resp.json()["id"]

    order_resp = await client.post(
        "/api/v1/orders/",
        json={
            "customer_id": cust_id,
            "quantity": 3.0,
            "unit_price": 3800.0,
            "delivery_price": 400.0,
            "order_date": target_date,
            "notes": "Менеджер підтвердив замовлення незважаючи на позначку",
        },
    )
    assert order_resp.status_code == 201
    assert order_resp.json()["order_date"] == target_date
    assert order_resp.json()["status"] == "new"

    # 7. Delete unavailable date
    del_resp = await client.delete(
        f"/api/v1/calendar/unavailable-dates/{target_date}",
        headers=auth_headers,
    )
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True

    # 8. Deleting again returns 404
    del_again = await client.delete(
        f"/api/v1/calendar/unavailable-dates/{target_date}",
        headers=auth_headers,
    )
    assert del_again.status_code == 404

    # 9. Verify date is removed from list
    list_after = await client.get("/api/v1/calendar/unavailable-dates")
    assert list_after.status_code == 200
    assert not any(d["date"] == target_date for d in list_after.json())

