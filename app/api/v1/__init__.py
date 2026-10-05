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


from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class CalculateRouteRequest(BaseModel):
    address: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None


class CalculateRouteResponse(BaseModel):
    success: bool
    distance_km: Optional[Decimal] = None
    duration_min: Optional[int] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    waze_url: Optional[str] = None
    google_maps_url: Optional[str] = None
    is_estimated: Optional[bool] = False
    message: Optional[str] = None


@router.get("/warehouse", tags=["Navigation & Warehouse"])
async def get_warehouse_location():
    """Отримати централізовані координати та адресу базового складу."""
    return navigation_service.warehouse_info


@router.post("/navigation/calculate-route", response_model=CalculateRouteResponse, tags=["Navigation & Warehouse"])
async def calculate_delivery_route(req: CalculateRouteRequest):
    """Розрахувати маршрут доставки, відстань у км та час від складу до адреси клієнта."""
    return await navigation_service.calculate_route(
        address=req.address,
        latitude=req.latitude,
        longitude=req.longitude,
    )

