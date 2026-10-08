from decimal import Decimal
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.mark.asyncio
async def test_migration_compatibility_with_old_orders():
    """
    Test that existing orders created under the previous schema
    are preserved safely when the new delivery_price column is added.
    """
    engine = create_async_engine(TEST_DB_URL, echo=False)

    # 1. Create tables as they existed in initial migration (without delivery_price)
    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(255) NOT NULL,
                phone VARCHAR(50) NOT NULL,
                address TEXT NOT NULL,
                latitude NUMERIC(9, 6),
                longitude NUMERIC(9, 6),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
            );
        """))
        await conn.execute(text("""
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
                product_name VARCHAR(255) NOT NULL,
                quantity NUMERIC(10, 2) NOT NULL,
                unit_price NUMERIC(10, 2) NOT NULL,
                total_amount NUMERIC(10, 2) NOT NULL,
                delivery_address TEXT NOT NULL,
                delivery_latitude NUMERIC(9, 6),
                delivery_longitude NUMERIC(9, 6),
                status VARCHAR(30) DEFAULT 'new' NOT NULL,
                notes TEXT,
                delivery_started_at TIMESTAMP,
                delivery_completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
            );
        """))

        # 2. Insert historical customer & order
        await conn.execute(text("""
            INSERT INTO customers (id, name, phone, address)
            VALUES (1, 'Іван Старий', '+380501112233', 'м. Луцьк');
        """))
        await conn.execute(text("""
            INSERT INTO orders (id, customer_id, product_name, quantity, unit_price, total_amount, delivery_address)
            VALUES (1, 1, 'Торф фрезерний старий', 10.00, 200.00, 2000.00, 'м. Луцьк');
        """))

    # 3. Simulate migration 002: ALTER TABLE orders ADD COLUMN delivery_price NUMERIC(10, 2) DEFAULT 0.00
    async with engine.begin() as conn:
        await conn.execute(text("""
            ALTER TABLE orders ADD COLUMN delivery_price NUMERIC(10, 2) DEFAULT 0.00 NOT NULL;
        """))

    # 4. Simulate migration 003: ALTER TABLE orders ADD COLUMN order_date DATE; ADD COLUMN distance_km NUMERIC(10, 2)
    async with engine.begin() as conn:
        await conn.execute(text("""
            ALTER TABLE orders ADD COLUMN order_date DATE;
        """))
        await conn.execute(text("""
            UPDATE orders SET order_date = '2026-10-05' WHERE order_date IS NULL;
        """))
        await conn.execute(text("""
            ALTER TABLE orders ADD COLUMN distance_km NUMERIC(10, 2);
        """))

    # 5. Simulate migration 004: ALTER TABLE orders ADD COLUMN delivery_price_per_km NUMERIC(10, 2)
    async with engine.begin() as conn:
        await conn.execute(text("""
            ALTER TABLE orders ADD COLUMN delivery_price_per_km NUMERIC(10, 2);
        """))

    # 6. Simulate migration 005: ALTER TABLE orders ADD COLUMN calculated_total_amount NUMERIC(10, 2); is_total_manual BOOLEAN
    async with engine.begin() as conn:
        await conn.execute(text("""
            ALTER TABLE orders ADD COLUMN calculated_total_amount NUMERIC(10, 2);
        """))
        await conn.execute(text("""
            UPDATE orders SET calculated_total_amount = total_amount WHERE calculated_total_amount IS NULL;
        """))
        await conn.execute(text("""
            ALTER TABLE orders ADD COLUMN is_total_manual BOOLEAN DEFAULT FALSE;
        """))

    # 7. Verify existing order data is preserved intact
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession)
    async with session_factory() as session:
        result = await session.execute(text("SELECT id, product_name, quantity, unit_price, delivery_price, total_amount, calculated_total_amount, is_total_manual, order_date, distance_km, delivery_price_per_km FROM orders WHERE id = 1"))
        row = result.mappings().one()

        assert row["id"] == 1
        assert row["product_name"] == "Торф фрезерний старий"
        assert Decimal(str(row["quantity"])) == Decimal("10.00")
        assert Decimal(str(row["unit_price"])) == Decimal("200.00")
        assert Decimal(str(row["delivery_price"])) == Decimal("0.00")
        assert Decimal(str(row["total_amount"])) == Decimal("2000.00")
        assert Decimal(str(row["calculated_total_amount"])) == Decimal("2000.00")
        assert bool(row["is_total_manual"]) is False
        assert row["order_date"] is not None
        assert row["distance_km"] is None
        assert row["delivery_price_per_km"] is None

    await engine.dispose()

