from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import router as api_v1_router
from app.config import get_settings

settings = get_settings()


import asyncio
import logging

logger = logging.getLogger("peat_crm")


@asynccontextmanager
async def lifespan(app: FastAPI):
    bot_task = None
    bot_instance = None
    if settings.TELEGRAM_BOT_TOKEN and not settings.TELEGRAM_BOT_TOKEN.startswith("123456789:ABC"):
        try:
            from app.bot.bot import create_bot_and_dispatcher
            bot_instance, dp = create_bot_and_dispatcher()
            await bot_instance.delete_webhook(drop_pending_updates=True)
            bot_task = asyncio.create_task(dp.start_polling(bot_instance))
            logger.info("Telegram bot polling started in background.")
        except Exception as e:
            logger.error(f"Failed to start Telegram bot polling: {e}")

    yield

    if bot_task:
        bot_task.cancel()
        try:
            await bot_task
        except (asyncio.CancelledError, Exception):
            pass
    if bot_instance:
        await bot_instance.session.close()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="CRM та система управління доставками торфу для сімейного підприємства",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["System"])
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "status": "online",
        "docs": "/docs",
        "api_v1": settings.API_V1_PREFIX,
    }


@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "healthy"}
