from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Find Stranger",          callback_data="menu_find")],
            [InlineKeyboardButton(text="⭐ Gender Filter (Premium)", callback_data="menu_gender_filter")],
            [InlineKeyboardButton(text="👤 Profile",                callback_data="menu_profile")],
            [InlineKeyboardButton(text="🚫 Report User",            callback_data="menu_report")],
        ]
    )


def gender_keyboard() -> InlineKeyboardMarkup:
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
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="♂ Male",   callback_data="filter_male"),
                InlineKeyboardButton(text="♀ Female", callback_data="filter_female"),
            ],
            [InlineKeyboardButton(text="🌍 Any", callback_data="filter_any")],
        ]
    )


def profile_keyboard() -> InlineKeyboardMarkup:
    """Profile view with delete option."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Delete My Profile", callback_data="profile_delete")],
            [InlineKeyboardButton(text="🔙 Back to Menu",      callback_data="profile_back")],
        ]
    )


def confirm_delete_keyboard() -> InlineKeyboardMarkup:
    """Confirmation before deleting profile."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Yes, Delete",  callback_data="profile_delete_confirm"),
                InlineKeyboardButton(text="❌ Cancel",       callback_data="profile_delete_cancel"),
            ]
        ]
    )