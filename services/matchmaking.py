"""
services/matchmaking.py
=======================
High-level matchmaking helpers used by handlers.
Keeps handler code thin — all queue/match logic lives here.
"""

import asyncio
import logging
from typing import Optional

from aiogram import Bot

from services.state import BotState
from utils.keyboards import main_menu_keyboard
from utils.messages import Msg

logger = logging.getLogger(__name__)


async def find_or_wait(
    bot: Bot,
    state_store: BotState,
    user_id: int,
    gender_filter: Optional[str] = None,
) -> None:
    """
    Enqueue user and attempt an immediate match.
    Notifies both users if a match is found.
    """
    # Enqueue with optional gender preference
    await state_store.enqueue(user_id, gender_filter)

    partner_id = await state_store.try_match(user_id)

    if partner_id:
        await _notify_match(bot, user_id, partner_id)
    else:
        await bot.send_message(user_id, Msg.SEARCHING)


async def _notify_match(bot: Bot, user_a: int, user_b: int) -> None:
    """Send match-found notifications to both parties concurrently."""
    await asyncio.gather(
        bot.send_message(user_a, Msg.MATCH_FOUND),
        bot.send_message(user_b, Msg.MATCH_FOUND),
        return_exceptions=True,
    )


async def disconnect_user(
    bot: Bot,
    state_store: BotState,
    user_id: int,
    *,
    skip_and_rematch: bool = False,
) -> None:
    """
    End user's current chat, notify partner, and optionally re-queue.
    """
    partner_id = await state_store.end_chat(user_id)

    if partner_id:
        try:
            await bot.send_message(partner_id, Msg.PARTNER_DISCONNECTED)
            if skip_and_rematch:
                # Re-queue the remaining partner automatically
                await find_or_wait(bot, state_store, partner_id)
            else:
                await bot.send_message(
                    partner_id,
                    Msg.RETURN_TO_MENU,
                    reply_markup=main_menu_keyboard(),
                )
        except Exception:  # partner may have blocked the bot
            logger.warning("Could not notify partner %s", partner_id)

    if skip_and_rematch:
        await find_or_wait(bot, state_store, user_id)
    else:
        await bot.send_message(
            user_id, Msg.CHAT_ENDED, reply_markup=main_menu_keyboard()
        )
