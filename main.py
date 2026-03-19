"""
Anonymous Stranger Chat Bot — main.py
Entry point: registers all routers and starts polling.
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from handlers import onboarding, menu, chat, payment, moderation
from services.state import BotState
from utils.scheduler import start_scheduler

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Bootstrap and run the bot."""
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Shared in-memory state (injected via middleware / passed through workflow_data)
    state_store = BotState()

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # ── Inject shared state into every handler via workflow_data ───────────────
    dp["state_store"] = state_store

    # ── Register routers (order matters for priority) ──────────────────────────
    dp.include_router(onboarding.router)
    dp.include_router(payment.router)
    dp.include_router(chat.router)
    dp.include_router(moderation.router)
    dp.include_router(menu.router)

    # ── Background tasks (inactive-chat timeout, etc.) ────────────────────────
    scheduler = start_scheduler(bot, state_store)

    logger.info("Bot is starting …")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.cancel()
        await bot.session.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
