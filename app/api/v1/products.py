from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

router = APIRouter(prefix="/products", tags=["Products & Catalog"])


class ProductSpec(BaseModel):
    id: int
    name: str
    category: str
    base_price_per_ton: float
    unit: str
    moisture: str
    ash_content: str
    calorific_value: str
    packaging: str
    description: str
    stock_status: str  # in_stock, low_stock, out_of_stock
    in_stock_tons: float
    image_url: Optional[str] = None


PRODUCTS_CATALOG: List[ProductSpec] = [
    ProductSpec(
        id=1,
        name="Торф'яний брикет (Навалом)",
        category="Паливні брикети",
        base_price_per_ton=3800.00,
        unit="тонна (т)",
        moisture="16-18%",
        ash_content="до 14%",
        calorific_value="3900-4200 ккал/кг",
        packaging="Навалом (самоскиди 5-25 т)",
        description="Якісний волинський торфобрикет стандарту СТБ/ТУ. Оптимальний вибір для промислових та приватних твердопаливних котлів. Тривале тління до 8-10 годин.",
        stock_status="in_stock",
        in_stock_tons=145.0,
    ),
    ProductSpec(
        id=2,
        name="Торф'яний брикет (У Біг-Бегах)",
        category="Паливні брикети",
        base_price_per_ton=4400.00,
        unit="тонна (т)",
        moisture="15-17%",
        ash_content="до 13%",
        calorific_value="4000-4300 ккал/кг",
        packaging="Біг-бег 1000 кг (1 т) на піддоні",
        description="Фасований у міцні біг-беги з вологозахистом. Зручний для вивантаження маніпулятором або карою, відсутність пилу та чисте подвір'я.",
        stock_status="in_stock",
        in_stock_tons=85.0,
    ),
    ProductSpec(
        id=3,
        name="Торф'яний брикет (На піддонах у термоплівці)",
        category="Паливні брикети",
        base_price_per_ton=4900.00,
        unit="тонна (т)",
        moisture="14-16%",
        ash_content="до 12%",
        calorific_value="4100-4400 ккал/кг",
        packaging="Піддон 1000 кг (пачки по 10-11 кг)",
        description="Преміальний формат. Зручні пачки для перенесення вручну у будинок чи до каміна, охайне зберігання, найвища тепловіддача.",
        stock_status="in_stock",
        in_stock_tons=62.0,
    ),
    ProductSpec(
        id=4,
        name="Торфокрихта паливна (Фрезерний торф)",
        category="Сировина та крихта",
        base_price_per_ton=2400.00,
        unit="тонна (т)",
        moisture="до 25%",
        ash_content="до 18%",
        calorific_value="3200-3600 ккал/кг",
        packaging="Навалом (зерновози, щеповози)",
        description="Фрезерний паливний торф для промислових ТЕЦ, когенераційних установок та котелень зі шнековою подачею палива.",
        stock_status="in_stock",
        in_stock_tons=220.0,
    ),
]


@router.get("/", response_model=List[ProductSpec])
async def list_products(
    category: Optional[str] = Query(None, description="Фільтр за категорією"),
):
    """Отримати каталог продукції торф'яного брикету з характеристиками та цінами."""
    if category:
        return [p for p in PRODUCTS_CATALOG if p.category.lower() == category.lower()]
    return PRODUCTS_CATALOG


@router.get("/{product_id}", response_model=ProductSpec)
async def get_product(product_id: int):
    """Отримати детальну інформацію про продукцію за ID."""
    for p in PRODUCTS_CATALOG:
        if p.id == product_id:
            return p
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Товар з ID {product_id} не знайдено",
    )
