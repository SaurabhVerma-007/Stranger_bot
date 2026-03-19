"""
config.py — Central configuration loaded from environment variables.
Copy .env.example → .env and fill in your values.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Required ───────────────────────────────────────────────────────────────
    BOT_TOKEN: str

    # ── Telegram Payments ──────────────────────────────────────────────────────
    # For Telegram Stars, the provider_token is an empty string ("").
    PAYMENT_PROVIDER_TOKEN: str = ""          # empty string = Telegram Stars
    PREMIUM_STARS_PRICE: int = 50             # cost in XTR (Telegram Stars)

    # ── Moderation ─────────────────────────────────────────────────────────────
    REPORTS_BEFORE_BAN: int = 3              # reports needed to auto-ban
    RATE_LIMIT_MESSAGES: int = 20            # max messages per window
    RATE_LIMIT_WINDOW_SECONDS: int = 10      # window size in seconds

    # ── Timeouts ───────────────────────────────────────────────────────────────
    CHAT_IDLE_TIMEOUT_SECONDS: int = 300     # 5 min idle → auto-disconnect
    SCHEDULER_INTERVAL_SECONDS: int = 60     # how often the background task runs

    # ── Matching ───────────────────────────────────────────────────────────────
    MAX_QUEUE_WAIT_SECONDS: int = 120        # max time before queue notification


settings = Settings()
