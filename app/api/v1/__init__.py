from fastapi import APIRouter

from app.api.v1.customers import router as customers_router
from app.api.v1.orders import router as orders_router
from app.services.navigation import navigation_service

router = APIRouter()

router.include_router(customers_router)
router.include_router(orders_router)


@router.get("/warehouse", tags=["Navigation & Warehouse"])
async def get_warehouse_location():
    """Отримати централізовані координати та адресу базового складу."""
    return navigation_service.warehouse_info
