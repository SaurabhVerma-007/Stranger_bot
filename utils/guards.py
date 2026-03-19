"""
utils/guards.py
===============
Reusable pre-condition checks used by multiple handlers.
"""

from aiogram.types import Message

from services.state import BotState
from utils.messages import Msg


async def require_profile(message: Message, state_store: BotState, user_id: int) -> bool:
    """
    Return True if the user has a completed, rules-agreed profile.
    Send an error message and return False otherwise.
    """
    profile = await state_store.get_profile(user_id)
    if not profile or not profile.agreed_to_rules:
        await message.answer(
            "⚠️ You haven't completed your profile yet. Send /start to set it up."
        )
        return False
    return True


async def require_rules_agreed(message: Message, state_store: BotState, user_id: int) -> bool:
    """Check only rules agreement (used separately when needed)."""
    profile = await state_store.get_profile(user_id)
    if not profile or not profile.agreed_to_rules:
        await message.answer(Msg.NO_PROFILE)
        return False
    return True
