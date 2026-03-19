import logging

from aiogram import Bot, Router

from config import settings
from services.matchmaking import disconnect_user
from services.state import BotState
from services import database as db
from utils.messages import Msg

logger = logging.getLogger(__name__)
router = Router(name="moderation")


async def _do_report(
    bot: Bot,
    state_store: BotState,
    reporter_id: int,
    reported_id: int,
) -> None:
    # Save report to database and get total report count
    total_reports = await db.add_report(reporter_id, reported_id)

    # Update in-memory state
    was_banned = await state_store.report_user(
        reporter_id=reporter_id,
        reported_id=reported_id,
        threshold=settings.REPORTS_BEFORE_BAN,
    )

    if was_banned or total_reports >= settings.REPORTS_BEFORE_BAN:
        logger.warning("User %s auto-banned (%d reports)", reported_id, total_reports)

        # Save ban to database
        await db.ban_user_db(
            reported_id,
            reason=f"Auto-banned after {total_reports} reports",
            temporary=True,
        )

        partner_id = await state_store.get_partner(reported_id)
        if partner_id:
            await disconnect_user(bot, state_store, reported_id, skip_and_rematch=False)

        try:
            await bot.send_message(reported_id, Msg.YOU_ARE_BANNED)
        except Exception:
            pass

    await disconnect_user(bot, state_store, reporter_id, skip_and_rematch=True)