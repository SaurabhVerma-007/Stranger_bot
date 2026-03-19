import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import settings
from handlers import onboarding, menu, chat, payment, moderation, admin
from services.state import BotState
from services.database import init_db
from utils.scheduler import start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    await init_db()

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    state_store = BotState()
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp["state_store"] = state_store

    dp.include_router(onboarding.router)
    dp.include_router(payment.router)
    dp.include_router(chat.router)
    dp.include_router(moderation.router)
    dp.include_router(admin.router)
    dp.include_router(menu.router)

    scheduler = start_scheduler(bot, state_store)

    await bot.set_my_commands([
        BotCommand(command="start",   description="Start the bot & setup profile"),
        BotCommand(command="next",    description="Skip to a new stranger"),
        BotCommand(command="stop",    description="End current chat"),
        BotCommand(command="report",  description="Report current stranger"),
        BotCommand(command="profile", description="View your profile"),
    ])

    logger.info("Bot is starting …")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.cancel()
        await bot.session.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())