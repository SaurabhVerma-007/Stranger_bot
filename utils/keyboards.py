"""
utils/keyboards.py
==================
Factory functions for all inline keyboards used across handlers.
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Primary menu shown after onboarding and after each chat."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Find Stranger",        callback_data="menu_find")],
            [InlineKeyboardButton(text="⭐ Gender Filter (Premium)", callback_data="menu_gender_filter")],
            [InlineKeyboardButton(text="👤 Profile",              callback_data="menu_profile")],
            [InlineKeyboardButton(text="🚫 Report User",          callback_data="menu_report")],
        ]
    )


def gender_keyboard() -> InlineKeyboardMarkup:
    """Used during onboarding to select the user's own gender."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="♂ Male",   callback_data="gender_male"),
                InlineKeyboardButton(text="♀ Female", callback_data="gender_female"),
                InlineKeyboardButton(text="🌈 Other",  callback_data="gender_other"),
            ]
        ]
    )


def gender_filter_keyboard() -> InlineKeyboardMarkup:
    """Used by premium users to choose which gender they want to match with."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="♂ Male",   callback_data="filter_male"),
                InlineKeyboardButton(text="♀ Female", callback_data="filter_female"),
            ],
            [InlineKeyboardButton(text="🌍 Any",       callback_data="filter_any")],
        ]
    )
