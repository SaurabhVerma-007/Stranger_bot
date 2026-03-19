import asyncio
import logging
import os
from datetime import datetime
from typing import Optional

import aiosqlite

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "bot.db")


async def init_db() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                username    TEXT,
                first_name  TEXT,
                gender      TEXT    NOT NULL,
                age         INTEGER NOT NULL,
                region      TEXT    NOT NULL,
                premium     INTEGER NOT NULL DEFAULT 0,
                joined_at   TEXT    NOT NULL,
                last_seen   TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS reports (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                reporter_id  INTEGER NOT NULL,
                reported_id  INTEGER NOT NULL,
                reason       TEXT,
                reported_at  TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS banned_users (
                user_id     INTEGER PRIMARY KEY,
                reason      TEXT,
                banned_at   TEXT    NOT NULL,
                temporary   INTEGER NOT NULL DEFAULT 1
            );
        """)
        await db.commit()
    logger.info("Database initialised at %s", DB_PATH)


# ── Users ──────────────────────────────────────────────────────────────────────

async def upsert_user(
    user_id: int, gender: str, age: int, region: str,
    username: Optional[str] = None, first_name: Optional[str] = None,
    premium: bool = False,
) -> None:
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, username, first_name, gender, age, region, premium, joined_at, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username, first_name=excluded.first_name,
                gender=excluded.gender, age=excluded.age, region=excluded.region,
                premium=excluded.premium, last_seen=excluded.last_seen
        """, (user_id, username, first_name, gender, age, region, int(premium), now, now))
        await db.commit()


async def set_premium_db(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET premium = 1 WHERE user_id = ?", (user_id,))
        await db.commit()


async def update_last_seen(user_id: int) -> None:
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET last_seen = ? WHERE user_id = ?", (now, user_id))
        await db.commit()


async def get_all_users() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users ORDER BY joined_at DESC") as cursor:
            return [dict(r) for r in await cursor.fetchall()]


async def get_user_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def get_premium_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users WHERE premium = 1") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


# ── Reports ────────────────────────────────────────────────────────────────────

async def add_report(reporter_id: int, reported_id: int, reason: Optional[str] = None) -> int:
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO reports (reporter_id, reported_id, reason, reported_at) VALUES (?, ?, ?, ?)",
            (reporter_id, reported_id, reason, now)
        )
        await db.commit()
        async with db.execute(
            "SELECT COUNT(*) FROM reports WHERE reported_id = ?", (reported_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 1


async def get_all_reports() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM reports ORDER BY reported_at DESC") as cursor:
            return [dict(r) for r in await cursor.fetchall()]


async def get_report_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM reports") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


# ── Bans ───────────────────────────────────────────────────────────────────────

async def ban_user_db(user_id: int, reason: str, temporary: bool = True) -> None:
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO banned_users (user_id, reason, banned_at, temporary)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                reason=excluded.reason, banned_at=excluded.banned_at, temporary=excluded.temporary
        """, (user_id, reason, now, int(temporary)))
        await db.commit()


async def unban_user_db(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM banned_users WHERE user_id = ?", (user_id,))
        await db.commit()


async def get_all_bans() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM banned_users ORDER BY banned_at DESC") as cursor:
            return [dict(r) for r in await cursor.fetchall()]


async def get_ban_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM banned_users") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0