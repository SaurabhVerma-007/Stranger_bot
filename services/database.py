import logging
from typing import Optional

import asyncpg

from config import settings

logger = logging.getLogger(__name__)

_pool: Optional[asyncpg.Pool] = None


async def init_db() -> None:
    global _pool
    _pool = await asyncpg.create_pool(settings.DATABASE_URL, min_size=2, max_size=10)

    async with _pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     BIGINT PRIMARY KEY,
                username    TEXT,
                first_name  TEXT,
                gender      TEXT        NOT NULL,
                age         INTEGER     NOT NULL,
                region      TEXT        NOT NULL,
                premium     BOOLEAN     NOT NULL DEFAULT FALSE,
                joined_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                last_seen   TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS reports (
                id           SERIAL PRIMARY KEY,
                reporter_id  BIGINT      NOT NULL,
                reported_id  BIGINT      NOT NULL,
                reason       TEXT,
                reported_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS banned_users (
                user_id    BIGINT PRIMARY KEY,
                reason     TEXT,
                banned_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                temporary  BOOLEAN     NOT NULL DEFAULT TRUE
            );
        """)

    logger.info("PostgreSQL database initialised")


def _pool_check() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database not initialised — call init_db() first")
    return _pool


# ── Users ──────────────────────────────────────────────────────────────────────

async def upsert_user(
    user_id: int, gender: str, age: int, region: str,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    premium: bool = False,
) -> None:
    async with _pool_check().acquire() as conn:
        await conn.execute("""
            INSERT INTO users (user_id, username, first_name, gender, age, region, premium)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (user_id) DO UPDATE SET
                username   = EXCLUDED.username,
                first_name = EXCLUDED.first_name,
                gender     = EXCLUDED.gender,
                age        = EXCLUDED.age,
                region     = EXCLUDED.region,
                premium    = EXCLUDED.premium,
                last_seen  = NOW()
        """, user_id, username, first_name, gender, age, region, premium)


async def set_premium_db(user_id: int) -> None:
    async with _pool_check().acquire() as conn:
        await conn.execute(
            "UPDATE users SET premium = TRUE WHERE user_id = $1", user_id
        )


async def update_last_seen(user_id: int) -> None:
    async with _pool_check().acquire() as conn:
        await conn.execute(
            "UPDATE users SET last_seen = NOW() WHERE user_id = $1", user_id
        )


async def get_all_users() -> list[dict]:
    async with _pool_check().acquire() as conn:
        rows = await conn.fetch("SELECT * FROM users ORDER BY joined_at DESC")
        return [dict(r) for r in rows]


async def get_user_count() -> int:
    async with _pool_check().acquire() as conn:
        return await conn.fetchval("SELECT COUNT(*) FROM users")


async def get_premium_count() -> int:
    async with _pool_check().acquire() as conn:
        return await conn.fetchval("SELECT COUNT(*) FROM users WHERE premium = TRUE")


# ── Reports ────────────────────────────────────────────────────────────────────

async def add_report(
    reporter_id: int, reported_id: int, reason: Optional[str] = None
) -> int:
    async with _pool_check().acquire() as conn:
        await conn.execute("""
            INSERT INTO reports (reporter_id, reported_id, reason)
            VALUES ($1, $2, $3)
        """, reporter_id, reported_id, reason)

        return await conn.fetchval(
            "SELECT COUNT(*) FROM reports WHERE reported_id = $1", reported_id
        )


async def get_all_reports() -> list[dict]:
    async with _pool_check().acquire() as conn:
        rows = await conn.fetch("SELECT * FROM reports ORDER BY reported_at DESC")
        return [dict(r) for r in rows]


async def get_report_count() -> int:
    async with _pool_check().acquire() as conn:
        return await conn.fetchval("SELECT COUNT(*) FROM reports")


# ── Bans ───────────────────────────────────────────────────────────────────────

async def ban_user_db(user_id: int, reason: str, temporary: bool = True) -> None:
    async with _pool_check().acquire() as conn:
        await conn.execute("""
            INSERT INTO banned_users (user_id, reason, temporary)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO UPDATE SET
                reason    = EXCLUDED.reason,
                banned_at = NOW(),
                temporary = EXCLUDED.temporary
        """, user_id, reason, temporary)


async def unban_user_db(user_id: int) -> None:
    async with _pool_check().acquire() as conn:
        await conn.execute(
            "DELETE FROM banned_users WHERE user_id = $1", user_id
        )


async def get_all_bans() -> list[dict]:
    async with _pool_check().acquire() as conn:
        rows = await conn.fetch("SELECT * FROM banned_users ORDER BY banned_at DESC")
        return [dict(r) for r in rows]


async def get_ban_count() -> int:
    async with _pool_check().acquire() as conn:
        return await conn.fetchval("SELECT COUNT(*) FROM banned_users")


async def delete_user(user_id: int) -> None:
    async with _pool_check().acquire() as conn:
        await conn.execute("DELETE FROM users WHERE user_id = $1", user_id)