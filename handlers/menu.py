"""
handlers/menu.py
================
Main menu actions:
  - 🔍 Find Stranger
  - ⭐ Gender Filter (Premium)
  - 👤 Profile
  - 🚫 Report User
"""

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from services.matchmaking import find_or_wait
from services.payments import send_premium_invoice
from services.state import BotState
from utils.keyboards import (
    gender_filter_keyboard,
    main_menu_keyboard,
)
from utils.messages import Msg
from utils.guards import require_profile, require_rules_agreed

logger = logging.getLogger(__name__)
router = Router(name="menu")


class GenderFilterStates(StatesGroup):
    choosing_filter = State()


# ── 🔍 Find Stranger ────────────────────────────────────────────────────────────

@router.callback_query(F.data == "menu_find")
async def cb_find_stranger(
    callback: CallbackQuery, state: FSMContext, state_store: BotState
) -> None:
    uid = callback.from_user.id

    if not await require_profile(callback.message, state_store, uid):
        return
    if await state_store.is_banned(uid):
        await callback.message.answer(Msg.BANNED)
        return
    if await state_store.get_partner(uid):
        await callback.message.answer(Msg.ALREADY_IN_CHAT)
        return

    await callback.answer()
    await callback.message.answer(Msg.SEARCHING)
    await find_or_wait(callback.bot, state_store, uid)


# ── ⭐ Gender Filter ─────────────────────────────────────────────────────────────

@router.callback_query(F.data == "menu_gender_filter")
async def cb_gender_filter(
    callback: CallbackQuery, state: FSMContext, state_store: BotState
) -> None:
    uid = callback.from_user.id

    if not await require_profile(callback.message, state_store, uid):
        return

    profile = await state_store.get_profile(uid)
    await callback.answer()

    if not profile.premium:
        # Prompt payment
        await callback.message.answer(Msg.PREMIUM_REQUIRED)
        await send_premium_invoice(callback.bot, uid)
        return

    # Premium user — ask preference
    await callback.message.answer(
        Msg.CHOOSE_GENDER_FILTER, reply_markup=gender_filter_keyboard()
    )
    await state.set_state(GenderFilterStates.choosing_filter)


@router.callback_query(
    GenderFilterStates.choosing_filter,
    F.data.in_({"filter_male", "filter_female", "filter_any"}),
)
async def cb_apply_filter(
    callback: CallbackQuery, state: FSMContext, state_store: BotState
) -> None:
    uid = callback.from_user.id
    gender_pref = callback.data.replace("filter_", "")  # "male" | "female" | "any"
    await state.clear()
    await callback.answer()
    await callback.message.edit_text(
        f"✅ Gender filter set to <b>{gender_pref.capitalize()}</b>. Searching…"
    )
    await find_or_wait(callback.bot, state_store, uid, gender_filter=gender_pref)


# ── 👤 Profile ──────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "menu_profile")
async def cb_profile(callback: CallbackQuery, state_store: BotState) -> None:
    uid = callback.from_user.id
    profile = await state_store.get_profile(uid)
    await callback.answer()

    if not profile:
        await callback.message.answer(Msg.NO_PROFILE)
        return

    text = (
        f"👤 <b>Your Profile</b>\n\n"
        f"Gender : {profile.gender.capitalize()}\n"
        f"Age    : {profile.age}\n"
        f"Region : {profile.region}\n"
        f"Premium: {'⭐ Yes' if profile.premium else 'No'}"
    )
    await callback.message.answer(text, reply_markup=main_menu_keyboard())


# ── 🚫 Report User (from menu) ──────────────────────────────────────────────────

@router.callback_query(F.data == "menu_report")
async def cb_report_from_menu(
    callback: CallbackQuery, state_store: BotState
) -> None:
    uid = callback.from_user.id
    partner_id = await state_store.get_partner(uid)
    await callback.answer()

    if not partner_id:
        await callback.message.answer(Msg.NOT_IN_CHAT)
        return

    from handlers.moderation import _do_report
    await _do_report(callback.bot, state_store, uid, partner_id)
    await callback.message.answer(Msg.REPORT_SENT, reply_markup=main_menu_keyboard())
