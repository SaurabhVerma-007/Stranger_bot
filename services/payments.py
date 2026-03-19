"""
services/payments.py
====================
Helpers for Telegram Stars (XTR) in-app purchases.

Telegram Stars overview
-----------------------
- provider_token must be an **empty string** ("") for Stars payments.
- Currency is always "XTR".
- No shipping address or phone number is required.
- The bot receives a `PreCheckoutQuery` that must be answered within 10 s.
- After successful payment the bot receives a `SuccessfulPayment` message.

Reference: https://core.telegram.org/bots/payments-stars
"""

import logging

from aiogram import Bot
from aiogram.types import LabeledPrice

from config import settings

logger = logging.getLogger(__name__)

CURRENCY = "XTR"   # Telegram Stars currency code


async def send_premium_invoice(bot: Bot, user_id: int) -> None:
    """
    Send a Telegram Stars invoice to unlock the Gender Filter feature.
    """
    await bot.send_invoice(
        chat_id=user_id,
        title="⭐ Premium — Gender Filter",
        description=(
            "Unlock the Gender Filter feature and choose who you want to "
            "chat with. One-time purchase."
        ),
        payload="premium_gender_filter",      # verified in pre-checkout handler
        provider_token=settings.PAYMENT_PROVIDER_TOKEN,  # "" for Stars
        currency=CURRENCY,
        prices=[
            LabeledPrice(
                label="Gender Filter (Lifetime)",
                amount=settings.PREMIUM_STARS_PRICE,  # in XTR units
            )
        ],
        # Stars-specific: protect content if desired
        protect_content=False,
    )
    logger.info("Invoice sent to user %s (%d XTR)", user_id, settings.PREMIUM_STARS_PRICE)
