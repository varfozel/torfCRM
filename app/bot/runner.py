import asyncio
import logging
import sys

from app.bot.bot import create_bot_and_dispatcher
from app.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    settings = get_settings()
    if not settings.TELEGRAM_BOT_TOKEN or settings.TELEGRAM_BOT_TOKEN.startswith("123456789:ABC"):
        logger.error(
            "TELEGRAM_BOT_TOKEN is not configured in .env! "
            "Please obtain a token from @BotFather and set TELEGRAM_BOT_TOKEN in .env"
        )
        sys.exit(1)

    bot, dp = create_bot_and_dispatcher()
    logger.info("Starting Telegram bot polling...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
