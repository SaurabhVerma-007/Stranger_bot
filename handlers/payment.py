"""
handlers/payment.py
===================
Telegram Stars payment flow:
  1. Bot sends invoice (services/payments.py)
  2. Telegram sends PreCheckoutQuery  → bot must answer within 10 s
  3. User confirms  → Telegram sends SuccessfulPayment message
  4. Bot sets premium_status = True

Reference: https://core.telegram.org/bots/payments-stars
"""

import logging

from aiogram import F, Router
from aiogram.types import Message, PreCheckoutQuery

from services.state import BotState
from utils.keyboards import main_menu_keyboard
from utils.messages import Msg

logger = logging.getLogger(__name__)
router = Router(name="payment")

PREMIUM_PAYLOAD = "premium_gender_filter"


# ── Pre-checkout ────────────────────────────────────────────────────────────────

@router.pre_checkout_query(F.invoice_payload == PREMIUM_PAYLOAD)
async def pre_checkout(query: PreCheckoutQuery) -> None:
    """
    Must be answered within 10 seconds.
    Approve unconditionally — in production you could add stock checks here.
    """
    await query.answer(ok=True)
    logger.info("Pre-checkout approved for user %s", query.from_user.id)


# ── Successful payment ──────────────────────────────────────────────────────────

@router.message(F.successful_payment.invoice_payload == PREMIUM_PAYLOAD)
async def successful_payment(message: Message, state_store: BotState) -> None:
    """Grant premium status after successful Stars payment."""
    uid = message.from_user.id
    await state_store.set_premium(uid)
    logger.info("User %s is now premium (Stars payment)", uid)
    await message.answer(Msg.PREMIUM_ACTIVATED, reply_markup=main_menu_keyboard())
