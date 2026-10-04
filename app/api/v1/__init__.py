from fastapi import APIRouter

from app.api.v1.analytics import router as analytics_router
from app.api.v1.auth import router as auth_router
from app.api.v1.customers import router as customers_router
from app.api.v1.orders import router as orders_router
from app.api.v1.products import router as products_router
from app.api.v1.settings import router as settings_router
from app.services.navigation import navigation_service

router = APIRouter()

router.include_router(auth_router)
router.include_router(analytics_router)
router.include_router(customers_router)
router.include_router(orders_router)
router.include_router(products_router)
router.include_router(settings_router)


@router.get("/warehouse", tags=["Navigation & Warehouse"])
async def get_warehouse_location():
    """Отримати централізовані координати та адресу базового складу."""
    return navigation_service.warehouse_info
