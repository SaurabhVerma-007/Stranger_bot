from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    BOT_TOKEN: str
    ADMIN_ID: Optional[int] = None
    PAYMENT_PROVIDER_TOKEN: str = ""
    PREMIUM_STARS_PRICE: int = 50
    REPORTS_BEFORE_BAN: int = 3
    RATE_LIMIT_MESSAGES: int = 20
    RATE_LIMIT_WINDOW_SECONDS: int = 10
    CHAT_IDLE_TIMEOUT_SECONDS: int = 300
    SCHEDULER_INTERVAL_SECONDS: int = 60
    MAX_QUEUE_WAIT_SECONDS: int = 120


settings = Settings()