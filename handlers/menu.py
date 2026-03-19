import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from services.matchmaking import find_or_wait
from services.payments import send_premium_invoice
from services.state import BotState
from services import database as db
from utils.keyboards import (
    gender_filter_keyboard,
    main_menu_keyboard,
    profile_keyboard,
    confirm_delete_keyboard,
)
from utils.messages import Msg
from utils.guards import require_profile

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
        await callback.message.answer(Msg.PREMIUM_REQUIRED)
        await send_premium_invoice(callback.bot, uid)
        return

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
    gender_pref = callback.data.replace("filter_", "")
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
        f"Gender  : {profile.gender.capitalize()}\n"
        f"Age     : {profile.age}\n"
        f"Region  : {profile.region}\n"
        f"Premium : {'⭐ Yes' if profile.premium else 'No'}"
    )
    await callback.message.answer(text, reply_markup=profile_keyboard())


@router.callback_query(F.data == "profile_back")
async def cb_profile_back(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.edit_text(
        "Main menu:", reply_markup=main_menu_keyboard()
    )


# ── 🗑 Delete Profile ────────────────────────────────────────────────────────────

@router.callback_query(F.data == "profile_delete")
async def cb_profile_delete(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.edit_text(
        "⚠️ <b>Are you sure you want to delete your profile?</b>\n\n"
        "This will remove all your data. You can create a new profile "
        "anytime by sending /start.",
        reply_markup=confirm_delete_keyboard(),
    )


@router.callback_query(F.data == "profile_delete_confirm")
async def cb_profile_delete_confirm(
    callback: CallbackQuery, state_store: BotState
) -> None:
    uid = callback.from_user.id
    await callback.answer()

    # End any active chat first
    partner_id = await state_store.end_chat(uid)
    if partner_id:
        try:
            await callback.bot.send_message(
                partner_id,
                "👋 Stranger has disconnected.",
                reply_markup=main_menu_keyboard(),
            )
        except Exception:
            pass

    # Remove from queue if waiting
    await state_store.dequeue(uid)

    # Delete from in-memory state
    async with state_store._lock:
        state_store.users.pop(uid, None)
        state_store.rate_limits.pop(uid, None)
        state_store.last_activity.pop(uid, None)

    # Delete from database
    await db.delete_user(uid)

    await callback.message.edit_text(
        "🗑 <b>Profile deleted.</b>\n\n"
        "Send /start anytime to create a new profile."
    )
    logger.info("User %s deleted their profile", uid)


@router.callback_query(F.data == "profile_delete_cancel")
async def cb_profile_delete_cancel(callback: CallbackQuery) -> None:
    await callback.answer("Cancelled.")
    await callback.message.edit_text(
        "✅ Profile kept. Back to menu:",
        reply_markup=main_menu_keyboard()
    )


# ── 🚫 Report User ──────────────────────────────────────────────────────────────

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