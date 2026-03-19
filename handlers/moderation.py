"""
handlers/moderation.py
======================
Handles:
  - Report logic (_do_report helper used by other handlers)
  - Pre-checkout and successful-payment are in payment.py
"""

import logging

from aiogram import Bot, Router

from config import settings
from services.matchmaking import disconnect_user
from services.state import BotState
from utils.messages import Msg

logger = logging.getLogger(__name__)
router = Router(name="moderation")


async def _do_report(
    bot: Bot,
    state_store: BotState,
    reporter_id: int,
    reported_id: int,
) -> None:
    """
    Record a report against `reported_id`.
    If the threshold is crossed the reported user is auto-banned
    and immediately disconnected from any active chat.
    """
    was_banned = await state_store.report_user(
        reporter_id=reporter_id,
        reported_id=reported_id,
        threshold=settings.REPORTS_BEFORE_BAN,
    )

    if was_banned:
        logger.warning("User %s was auto-banned", reported_id)
        # Disconnect the newly banned user
        partner_id = await state_store.get_partner(reported_id)
        if partner_id:
            await disconnect_user(bot, state_store, reported_id, skip_and_rematch=False)

        try:
            await bot.send_message(reported_id, Msg.YOU_ARE_BANNED)
        except Exception:
            pass

    # Always end the reporter's current chat and re-queue them
    await disconnect_user(bot, state_store, reporter_id, skip_and_rematch=True)
