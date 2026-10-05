from functools import lru_cache
from typing import Set
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "Peat CRM"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://peat_user:peat_secure_password@localhost:5432/peat_crm"

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = Field(
        default="",
        description="Telegram bot token obtained from @BotFather",
    )
    TELEGRAM_ALLOWED_USER_IDS: str = Field(
        default="",
        description="Comma-separated Telegram user IDs allowed to interact with the bot. Empty allows all.",
    )

    # Manager Web Authentication
    MANAGER_USERNAME: str = "admin"
    MANAGER_PASSWORD: str = "peat_manager_2026"
    JWT_SECRET_KEY: str = "peat_crm_secret_jwt_key_default_2026"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Warehouse Origin Location (Loaded from .env / environment)
    WAREHOUSE_NAME: str = "Склад торфу"
    WAREHOUSE_ADDRESS: str = ""
    WAREHOUSE_LAT: float = 50.747200
    WAREHOUSE_LON: float = 25.325400

    @property
    def allowed_telegram_ids(self) -> Set[int]:
        if not self.TELEGRAM_ALLOWED_USER_IDS.strip():
            return set()
        ids = set()
        for item in self.TELEGRAM_ALLOWED_USER_IDS.split(","):
            cleaned = item.strip()
            if cleaned.isdigit():
                ids.add(int(cleaned))
        return ids


@lru_cache()
def get_settings() -> Settings:
    return Settings()
