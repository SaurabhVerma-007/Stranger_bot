"""
handlers/onboarding.py
======================
Handles /start and the multi-step profile-setup FSM:
  Step 1 → Gender
  Step 2 → Age
  Step 3 → Region
  Step 4 → Rules agreement
"""

import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from services.state import BotState, UserProfile
from utils.keyboards import gender_keyboard, main_menu_keyboard
from utils.messages import Msg

logger = logging.getLogger(__name__)
router = Router(name="onboarding")


# ── FSM States ─────────────────────────────────────────────────────────────────

class OnboardingStates(StatesGroup):
    waiting_gender = State()
    waiting_age    = State()
    waiting_region = State()
    waiting_rules  = State()


# ── /start ─────────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, state_store: BotState) -> None:
    """Entry point — greet user and begin onboarding."""
    user_id = message.from_user.id

    # Check if already onboarded
    existing = await state_store.get_profile(user_id)
    if existing and existing.agreed_to_rules:
        await message.answer(Msg.WELCOME_BACK, reply_markup=main_menu_keyboard())
        return

    await message.answer(Msg.ONBOARDING_INTRO)
    await message.answer(Msg.ASK_GENDER, reply_markup=gender_keyboard())
    await state.set_state(OnboardingStates.waiting_gender)


# ── Step 1: Gender ──────────────────────────────────────────────────────────────

@router.callback_query(
    OnboardingStates.waiting_gender,
    F.data.in_({"gender_male", "gender_female", "gender_other"}),
)
async def cb_gender(callback: CallbackQuery, state: FSMContext) -> None:
    gender = callback.data.replace("gender_", "")
    await state.update_data(gender=gender)
    await callback.message.edit_text(f"✅ Gender set to <b>{gender.capitalize()}</b>.")
    await callback.message.answer(Msg.ASK_AGE)
    await state.set_state(OnboardingStates.waiting_age)
    await callback.answer()


# ── Step 2: Age ─────────────────────────────────────────────────────────────────

@router.message(OnboardingStates.waiting_age, F.text)
async def msg_age(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text.isdigit() or not (13 <= int(text) <= 100):
        await message.answer(Msg.INVALID_AGE)
        return

    await state.update_data(age=int(text))
    await message.answer(Msg.ASK_REGION)
    await state.set_state(OnboardingStates.waiting_region)


# ── Step 3: Region ──────────────────────────────────────────────────────────────

@router.message(OnboardingStates.waiting_region, F.text)
async def msg_region(message: Message, state: FSMContext) -> None:
    region = (message.text or "").strip()[:64]   # cap length
    if len(region) < 2:
        await message.answer(Msg.INVALID_REGION)
        return

    await state.update_data(region=region)
    await message.answer(Msg.SHOW_RULES, reply_markup=_rules_keyboard())
    await state.set_state(OnboardingStates.waiting_rules)


def _rules_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ I Agree", callback_data="rules_agree")],
            [InlineKeyboardButton(text="❌ I Decline", callback_data="rules_decline")],
        ]
    )


# ── Step 4: Rules agreement ────────────────────────────────────────────────────

@router.callback_query(OnboardingStates.waiting_rules, F.data == "rules_agree")
async def cb_rules_agree(
    callback: CallbackQuery, state: FSMContext, state_store: BotState
) -> None:
    data = await state.get_data()
    profile = UserProfile(
        user_id=callback.from_user.id,
        gender=data["gender"],
        age=data["age"],
        region=data["region"],
        agreed_to_rules=True,
    )
    await state_store.save_profile(profile)
    await state.clear()
    await callback.message.edit_text(Msg.RULES_ACCEPTED)
    await callback.message.answer(Msg.SETUP_DONE, reply_markup=main_menu_keyboard())
    await callback.answer()
    logger.info("User %s completed onboarding", callback.from_user.id)


@router.callback_query(OnboardingStates.waiting_rules, F.data == "rules_decline")
async def cb_rules_decline(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(Msg.RULES_DECLINED)
    await callback.answer()
