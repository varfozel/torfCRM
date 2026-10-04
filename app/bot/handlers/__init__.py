from app.bot.handlers.common import router as common_router
from app.bot.handlers.customers import router as customers_router
from app.bot.handlers.orders import router as orders_router

__all__ = ["common_router", "customers_router", "orders_router"]
