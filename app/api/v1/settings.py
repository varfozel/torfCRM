from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

from app.config import get_settings
from app.services.navigation import navigation_service

settings = get_settings()

router = APIRouter(prefix="/settings", tags=["System Settings"])


class WarehouseSettings(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float


class CompanySettings(BaseModel):
    project_name: str
    currency: str = "UAH"
    currency_symbol: str = "грн"
    default_unit_price: float = 3800.00
    default_delivery_price: float = 400.00
    warehouse: WarehouseSettings
    manager_username: str
    version: str = "1.0.0"


@router.get("/", response_model=CompanySettings)
async def get_system_settings():
    """Отримати загальні налаштування системи Peat CRM."""
    wh = navigation_service.warehouse_info
    return CompanySettings(
        project_name=settings.PROJECT_NAME,
        currency="UAH",
        currency_symbol="грн",
        default_unit_price=3800.00,
        default_delivery_price=400.00,
        warehouse=WarehouseSettings(
            name=wh["name"],
            address=wh["address"],
            latitude=wh["latitude"],
            longitude=wh["longitude"],
        ),
        manager_username=settings.MANAGER_USERNAME,
        version="1.0.0",
    )
