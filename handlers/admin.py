import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import settings
from services import database as db

logger = logging.getLogger(__name__)
router = Router(name="admin")


def is_admin(user_id: int) -> bool:
    return settings.ADMIN_ID is not None and user_id == settings.ADMIN_ID


def admin_only(handler):
    async def wrapper(message: Message, **kwargs):
        if not is_admin(message.from_user.id):
            return
        return await handler(message, **kwargs)
    return wrapper


@router.message(Command("admin"))
@admin_only
async def cmd_admin(message: Message) -> None:
    users   = await db.get_user_count()
    premium = await db.get_premium_count()
    reports = await db.get_report_count()
    bans    = await db.get_ban_count()

    await message.answer(
        f"🛠 <b>Admin Dashboard</b>\n\n"
        f"👤 Total users   : <b>{users}</b>\n"
        f"⭐ Premium users : <b>{premium}</b>\n"
        f"🚩 Total reports : <b>{reports}</b>\n"
        f"🚫 Banned users  : <b>{bans}</b>\n\n"
        f"/users — recent users\n"
        f"/reports — all reports\n"
        f"/bans — banned users\n"
        f"/unban &lt;user_id&gt; — unban someone\n"
        f"/broadcast &lt;text&gt; — message all users"
    )


@router.message(Command("users"))
@admin_only
async def cmd_users(message: Message) -> None:
    users = await db.get_all_users()
    if not users:
        await message.answer("No users yet.")
        return

    lines = []
    for u in users[:20]:
        tag = "⭐" if u["premium"] else ""
        lines.append(
            f"{tag}<code>{u['user_id']}</code> | {u['gender']} {u['age']} | "
            f"{u['region']} | joined {u['joined_at'][:10]}"
        )

    await message.answer(
        f"👤 <b>Users</b> (showing {min(20, len(users))} of {len(users)})\n\n"
        + "\n".join(lines)
    )


@router.message(Command("reports"))
@admin_only
async def cmd_reports(message: Message) -> None:
    reports = await db.get_all_reports()
    if not reports:
        await message.answer("No reports yet.")
        return

    lines = []
    for r in reports[:20]:
        lines.append(
            f"🚩 <code>{r['reporter_id']}</code> → <code>{r['reported_id']}</code> | "
            f"{r['reported_at'][:16]}"
            + (f" | {r['reason']}" if r.get("reason") else "")
        )

    await message.answer(
        f"🚩 <b>Reports</b> ({len(reports)} total)\n\n" + "\n".join(lines)
    )


@router.message(Command("bans"))
@admin_only
async def cmd_bans(message: Message) -> None:
    bans = await db.get_all_bans()
    if not bans:
        await message.answer("No banned users.")
        return

    lines = []
    for b in bans:
        temp = "temp" if b["temporary"] else "permanent"
        lines.append(
            f"🚫 <code>{b['user_id']}</code> | {temp} | {b['reason']} | {b['banned_at'][:16]}"
        )

    await message.answer(f"🚫 <b>Banned Users</b> ({len(bans)})\n\n" + "\n".join(lines))


@router.message(Command("unban"))
@admin_only
async def cmd_unban(message: Message) -> None:
    parts = (message.text or "").split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Usage: /unban &lt;user_id&gt;")
        return
    user_id = int(parts[1])
    await db.unban_user_db(user_id)
    await message.answer(f"✅ User <code>{user_id}</code> unbanned.")


@router.message(Command("broadcast"))
@admin_only
async def cmd_broadcast(message: Message) -> None:
    text = (message.text or "").partition(" ")[2].strip()
    if not text:
        await message.answer("Usage: /broadcast &lt;your message&gt;")
        return

    users = await db.get_all_users()
    sent = failed = 0
    for u in users:
        try:
            await message.bot.send_message(u["user_id"], f"📢 {text}")
            sent += 1
        except Exception:
            failed += 1

    await message.answer(f"📢 Done. ✅ Sent: {sent} | ❌ Failed: {failed}")