"""
utils/messages.py
=================
Centralised message strings.
Keeping them here makes localisation and A/B testing trivial.
"""


class Msg:
    # ── Onboarding ─────────────────────────────────────────────────────────────
    ONBOARDING_INTRO = (
        "👋 <b>Welcome to StrangerChat!</b>\n\n"
        "Let's set up your profile quickly — it takes less than a minute."
    )
    ASK_GENDER  = "1️⃣ What is your gender?"
    ASK_AGE     = "2️⃣ How old are you? (Enter a number between 13 and 100)"
    ASK_REGION  = "3️⃣ Where are you from? (City or country)"
    INVALID_AGE = "⚠️ Please enter a valid age between 13 and 100."
    INVALID_REGION = "⚠️ Please enter a valid region (at least 2 characters)."

    SHOW_RULES = (
        "📋 <b>Community Guidelines</b>\n\n"
        "Please read and agree before continuing:\n\n"
        "• Be respectful and polite at all times\n"
        "• No harassment, hate speech, or abuse\n"
        "• No explicit or adult content\n"
        "• Do not share personal information (name, phone, address)\n"
        "• You can leave anytime with /next or /stop\n"
        "• Violating these rules may result in a permanent ban\n\n"
        "Do you agree to these guidelines?"
    )
    RULES_ACCEPTED = "✅ You've agreed to the guidelines."
    RULES_DECLINED = (
        "❌ You must agree to the guidelines to use StrangerChat.\n"
        "Send /start to try again."
    )
    SETUP_DONE = (
        "🎉 Profile created! You're all set.\n\n"
        "Use the menu below to find a stranger to chat with."
    )
    WELCOME_BACK = "👋 Welcome back! Use the menu to get started."
    NO_PROFILE   = "⚠️ Profile not found. Please send /start to set up your profile."

    # ── Matchmaking ────────────────────────────────────────────────────────────
    SEARCHING         = "🔍 Searching for a stranger… Please wait."
    MATCH_FOUND       = "🎉 <b>Connected!</b> Say hello to your new stranger!"
    PARTNER_DISCONNECTED = "👋 Stranger has disconnected."
    CHAT_ENDED        = "✅ Chat ended. Use the menu to find someone new."
    RETURN_TO_MENU    = "Use the menu below to find a new stranger."
    ALREADY_IN_CHAT   = "⚠️ You're already in a chat. Use /stop to end it first."
    NOT_IN_CHAT       = "⚠️ You're not in a chat right now."

    # ── Premium / Payment ──────────────────────────────────────────────────────
    PREMIUM_REQUIRED  = (
        "⭐ <b>Gender Filter is a Premium feature.</b>\n\n"
        "Unlock it with a one-time Telegram Stars purchase:"
    )
    CHOOSE_GENDER_FILTER = "👇 Choose which gender you'd like to chat with:"
    PREMIUM_ACTIVATED = (
        "⭐ <b>Premium activated!</b>\n\n"
        "You can now use the Gender Filter when finding strangers."
    )

    # ── Moderation ─────────────────────────────────────────────────────────────
    REPORT_SENT  = "✅ Report submitted. Thank you for keeping the community safe."
    YOU_ARE_BANNED = (
        "🚫 Your account has been temporarily banned due to multiple reports.\n"
        "Contact support if you believe this is an error."
    )
    BANNED = "🚫 You are currently banned from using StrangerChat."

    # ── Rate limiting ──────────────────────────────────────────────────────────
    RATE_LIMITED = "⏳ You're sending messages too fast. Please slow down."

    # ── Misc ───────────────────────────────────────────────────────────────────
    UNSUPPORTED_CONTENT = "⚠️ This type of content cannot be forwarded."
