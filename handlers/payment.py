import logging

from aiogram import F, Router
from aiogram.types import Message, PreCheckoutQuery

from services.state import BotState
from services import database as db
from utils.keyboards import main_menu_keyboard
from utils.messages import Msg

logger = logging.getLogger(__name__)
router = Router(name="payment")

PREMIUM_PAYLOAD = "premium_gender_filter"


@router.pre_checkout_query(F.invoice_payload == PREMIUM_PAYLOAD)
async def pre_checkout(query: PreCheckoutQuery) -> None:
    await query.answer(ok=True)
    logger.info("Pre-checkout approved for user %s", query.from_user.id)


@router.message(F.successful_payment.invoice_payload == PREMIUM_PAYLOAD)
async def successful_payment(message: Message, state_store: BotState) -> None:
    uid = message.from_user.id

    # Update in-memory state
    await state_store.set_premium(uid)

    # Persist to database
    await db.set_premium_db(uid)

    logger.info("User %s is now premium (Stars payment)", uid)
    await message.answer(Msg.PREMIUM_ACTIVATED, reply_markup=main_menu_keyboard())