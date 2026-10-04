import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware, Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, TelegramObject

from app.bot.handlers import common_router, customers_router, orders_router
from app.config import get_settings

logger = logging.getLogger(__name__)


class AccessControlMiddleware(BaseMiddleware):
    """
    Middleware that restricts bot usage to authorized Telegram user IDs
    if TELEGRAM_ALLOWED_USER_IDS is configured in settings.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        settings = get_settings()
        allowed_ids = settings.allowed_telegram_ids

        # If no allowed IDs are configured, all users have access
        if not allowed_ids:
            return await handler(event, data)

        user = getattr(event, "from_user", None)
        if user and user.id not in allowed_ids:
            logger.warning(f"Unauthorized access attempt by user_id={user.id} username={user.username}")
            if isinstance(event, Message):
                await event.answer("⛔️ У вас немає доступу до цієї системи CRM.")
            return

        return await handler(event, data)


def create_bot_and_dispatcher() -> tuple[Bot, Dispatcher]:
    """Create and configure aiogram 3 Bot and Dispatcher instances."""
    settings = get_settings()
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN or "dummy:token")
    dp = Dispatcher(storage=MemoryStorage())

    # Register access control middleware
    dp.message.middleware(AccessControlMiddleware())
    dp.callback_query.middleware(AccessControlMiddleware())

    # Register routers
    dp.include_router(common_router)
    dp.include_router(customers_router)
    dp.include_router(orders_router)

    return bot, dp
