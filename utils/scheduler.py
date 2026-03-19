"""
utils/scheduler.py
==================
Runs a periodic background task that:
  1. Disconnects chat pairs that have been idle for too long.
  2. (Extendable) Cleans up abandoned queue entries.
"""

import asyncio
import logging
from typing import Optional

from aiogram import Bot

from config import settings
from services.state import BotState
from utils.messages import Msg
from utils.keyboards import main_menu_keyboard

logger = logging.getLogger(__name__)


def start_scheduler(bot: Bot, state_store: BotState) -> asyncio.Task:
    """Create and return the background scheduler task."""
    return asyncio.create_task(_scheduler_loop(bot, state_store))


async def _scheduler_loop(bot: Bot, state_store: BotState) -> None:
    """Runs every SCHEDULER_INTERVAL_SECONDS."""
    while True:
        await asyncio.sleep(settings.SCHEDULER_INTERVAL_SECONDS)
        try:
            await _tick(bot, state_store)
        except Exception as exc:
            logger.error("Scheduler tick error: %s", exc, exc_info=True)


async def _tick(bot: Bot, state_store: BotState) -> None:
    """Single scheduler tick: handle idle timeouts."""
    idle_pairs = await state_store.get_idle_chat_pairs(
        settings.CHAT_IDLE_TIMEOUT_SECONDS
    )

    for user_id, partner_id in idle_pairs:
        logger.info("Idle timeout: disconnecting %s ↔ %s", user_id, partner_id)
        await state_store.end_chat(user_id)

        timeout_msg = "⏰ Chat ended due to inactivity."
        for uid in (user_id, partner_id):
            try:
                await bot.send_message(
                    uid, timeout_msg, reply_markup=main_menu_keyboard()
                )
            except Exception:
                pass
