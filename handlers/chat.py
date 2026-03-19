"""
handlers/chat.py
================
Relays messages between paired users anonymously.

Supported content types:
  text, sticker, photo, video, audio, voice, document, animation

Commands while in chat:
  /next  → skip partner and rematch
  /stop  → end chat entirely
"""

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from config import settings
from services.matchmaking import disconnect_user
from services.state import BotState
from utils.messages import Msg

logger = logging.getLogger(__name__)
router = Router(name="chat")


async def _rate_guard(message: Message, state_store: BotState) -> bool:
    """Returns True if message is allowed, False if rate-limited."""
    allowed = await state_store.check_rate_limit(
        message.from_user.id,
        settings.RATE_LIMIT_MESSAGES,
        settings.RATE_LIMIT_WINDOW_SECONDS,
    )
    if not allowed:
        await message.reply(Msg.RATE_LIMITED)
    return allowed


# ── /next ───────────────────────────────────────────────────────────────────────

@router.message(Command("next"))
async def cmd_next(message: Message, state_store: BotState) -> None:
    uid = message.from_user.id
    if not await state_store.get_partner(uid):
        await message.answer(Msg.NOT_IN_CHAT)
        return
    await disconnect_user(message.bot, state_store, uid, skip_and_rematch=True)


# ── /stop ───────────────────────────────────────────────────────────────────────

@router.message(Command("stop"))
async def cmd_stop(message: Message, state_store: BotState) -> None:
    uid = message.from_user.id
    if not await state_store.get_partner(uid):
        await message.answer(Msg.NOT_IN_CHAT)
        return
    await disconnect_user(message.bot, state_store, uid, skip_and_rematch=False)


# ── /report (command shortcut) ──────────────────────────────────────────────────

@router.message(Command("report"))
async def cmd_report(message: Message, state_store: BotState) -> None:
    uid = message.from_user.id
    partner_id = await state_store.get_partner(uid)
    if not partner_id:
        await message.answer(Msg.NOT_IN_CHAT)
        return
    from handlers.moderation import _do_report
    await _do_report(message.bot, state_store, uid, partner_id)
    await message.answer(Msg.REPORT_SENT)


# ── Message relay ───────────────────────────────────────────────────────────────

@router.message(F.chat.type == "private")
async def relay_message(message: Message, state_store: BotState) -> None:
    """
    Forward any message from a user in an active chat to their partner.
    Messages from users not in a chat are silently ignored here
    (the menu handler will catch them if they press buttons).
    """
    uid = message.from_user.id
    partner_id = await state_store.get_partner(uid)

    if not partner_id:
        return  # not in a chat — other handlers will respond

    # Rate-limit check
    if not await _rate_guard(message, state_store):
        return

    # Update activity timestamp
    await state_store.touch_activity(uid)

    try:
        await _forward(message, partner_id)
    except Exception as exc:
        logger.warning("Relay failed %s→%s: %s", uid, partner_id, exc)
        # Partner likely blocked the bot — disconnect
        await disconnect_user(message.bot, state_store, uid, skip_and_rematch=False)


async def _forward(message: Message, target_id: int) -> None:
    """Copy message content to target without revealing the sender."""
    bot = message.bot

    if message.text:
        await bot.send_message(target_id, message.text)
    elif message.sticker:
        await bot.send_sticker(target_id, message.sticker.file_id)
    elif message.photo:
        await bot.send_photo(
            target_id, message.photo[-1].file_id, caption=message.caption
        )
    elif message.video:
        await bot.send_video(
            target_id, message.video.file_id, caption=message.caption
        )
    elif message.audio:
        await bot.send_audio(
            target_id, message.audio.file_id, caption=message.caption
        )
    elif message.voice:
        await bot.send_voice(target_id, message.voice.file_id)
    elif message.document:
        await bot.send_document(
            target_id, message.document.file_id, caption=message.caption
        )
    elif message.animation:
        await bot.send_animation(
            target_id, message.animation.file_id, caption=message.caption
        )
    elif message.video_note:
        await bot.send_video_note(target_id, message.video_note.file_id)
    else:
        # Unsupported type — notify sender
        await message.reply(Msg.UNSUPPORTED_CONTENT)
