"""
services/state.py
=================
Single source of truth for all runtime state.

All public methods acquire an asyncio.Lock to guarantee freedom from race
conditions when two users match simultaneously.

Data structures
---------------
users           : {user_id: UserProfile}
waiting_queue   : list[QueueEntry]          — ordered by enqueue time
active_chats    : {user_id: partner_id}     — both directions stored
banned_users    : {user_id: BanRecord}
reports         : {reported_id: [reporter_id, …]}
rate_limits     : {user_id: RateBucket}
last_activity   : {user_id: datetime}
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


# ── Domain models ──────────────────────────────────────────────────────────────

@dataclass
class UserProfile:
    user_id: int
    gender: str                          # "male" | "female" | "other"
    age: int
    region: str
    premium: bool = False
    agreed_to_rules: bool = False
    interests: list[str] = field(default_factory=list)


@dataclass
class QueueEntry:
    user_id: int
    gender_filter: Optional[str]         # None = no filter; "male"/"female"
    enqueued_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class BanRecord:
    user_id: int
    reason: str
    banned_at: datetime = field(default_factory=datetime.utcnow)
    temporary: bool = True


@dataclass
class RateBucket:
    count: int = 0
    window_start: datetime = field(default_factory=datetime.utcnow)


# ── State store ────────────────────────────────────────────────────────────────

class BotState:
    """Async-safe, in-memory state container."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()

        self.users:          dict[int, UserProfile]    = {}
        self.waiting_queue:  list[QueueEntry]          = []
        self.active_chats:   dict[int, int]            = {}   # uid → partner_uid
        self.banned_users:   dict[int, BanRecord]      = {}
        self.reports:        dict[int, list[int]]      = {}   # reported → [reporters]
        self.rate_limits:    dict[int, RateBucket]     = {}
        self.last_activity:  dict[int, datetime]       = {}

    # ── Profile ────────────────────────────────────────────────────────────────

    async def save_profile(self, profile: UserProfile) -> None:
        async with self._lock:
            self.users[profile.user_id] = profile
            logger.debug("Profile saved: %s", profile.user_id)

    async def get_profile(self, user_id: int) -> Optional[UserProfile]:
        async with self._lock:
            return self.users.get(user_id)

    async def set_premium(self, user_id: int) -> bool:
        async with self._lock:
            if user_id in self.users:
                self.users[user_id].premium = True
                return True
            return False

    # ── Queue ──────────────────────────────────────────────────────────────────

    async def enqueue(self, user_id: int, gender_filter: Optional[str] = None) -> None:
        """Add user to the waiting queue (idempotent)."""
        async with self._lock:
            # Remove stale entry first
            self.waiting_queue = [e for e in self.waiting_queue if e.user_id != user_id]
            self.waiting_queue.append(QueueEntry(user_id=user_id, gender_filter=gender_filter))
            logger.info("Enqueued user %s (filter=%s)", user_id, gender_filter)

    async def dequeue(self, user_id: int) -> None:
        """Remove user from the waiting queue."""
        async with self._lock:
            self.waiting_queue = [e for e in self.waiting_queue if e.user_id != user_id]

    async def try_match(self, user_id: int) -> Optional[int]:
        """
        Attempt to find a compatible partner for *user_id*.

        Compatibility rules:
        - Partner must be waiting in queue (not the requester)
        - Neither party is banned
        - If requester has a gender_filter → partner.gender must match
        - If partner has a gender_filter    → requester.gender must match

        Returns partner_id if matched, else None.
        Matching is atomic: both entries are removed from queue and both
        active_chats entries are set inside the same lock acquisition.
        """
        async with self._lock:
            requester_entry = next(
                (e for e in self.waiting_queue if e.user_id == user_id), None
            )
            if not requester_entry:
                return None

            requester_profile = self.users.get(user_id)

            for entry in self.waiting_queue:
                if entry.user_id == user_id:
                    continue
                if entry.user_id in self.banned_users:
                    continue

                partner_profile = self.users.get(entry.user_id)
                if not partner_profile:
                    continue

                # Check requester's gender filter
                if requester_entry.gender_filter and requester_entry.gender_filter != "any":
                    if partner_profile.gender != requester_entry.gender_filter:
                        continue

                # Check partner's gender filter
                if entry.gender_filter and entry.gender_filter != "any":
                    if requester_profile and requester_profile.gender != entry.gender_filter:
                        continue

                # ── Match found ────────────────────────────────────────────────
                partner_id = entry.user_id
                self.waiting_queue = [
                    e for e in self.waiting_queue
                    if e.user_id not in (user_id, partner_id)
                ]
                self.active_chats[user_id]   = partner_id
                self.active_chats[partner_id] = user_id
                now = datetime.utcnow()
                self.last_activity[user_id]   = now
                self.last_activity[partner_id] = now
                logger.info("Matched %s ↔ %s", user_id, partner_id)
                return partner_id

            return None

    # ── Active chats ───────────────────────────────────────────────────────────

    async def get_partner(self, user_id: int) -> Optional[int]:
        async with self._lock:
            return self.active_chats.get(user_id)

    async def end_chat(self, user_id: int) -> Optional[int]:
        """
        Disconnect user from current chat.
        Returns the partner's id (so caller can notify them), or None.
        """
        async with self._lock:
            partner_id = self.active_chats.pop(user_id, None)
            if partner_id:
                self.active_chats.pop(partner_id, None)
                logger.info("Chat ended: %s ↔ %s", user_id, partner_id)
            return partner_id

    async def touch_activity(self, user_id: int) -> None:
        """Update last-activity timestamp (for idle timeout)."""
        async with self._lock:
            self.last_activity[user_id] = datetime.utcnow()

    async def get_idle_chat_pairs(self, timeout_seconds: int) -> list[tuple[int, int]]:
        """Return (user_id, partner_id) pairs that have been idle too long."""
        async with self._lock:
            now = datetime.utcnow()
            idle: list[tuple[int, int]] = []
            seen: set[int] = set()
            for uid, partner_id in list(self.active_chats.items()):
                if uid in seen:
                    continue
                last = self.last_activity.get(uid, now)
                if (now - last).total_seconds() > timeout_seconds:
                    idle.append((uid, partner_id))
                    seen.add(uid)
                    seen.add(partner_id)
            return idle

    # ── Moderation ─────────────────────────────────────────────────────────────

    async def report_user(
        self, reporter_id: int, reported_id: int, threshold: int
    ) -> bool:
        """
        Log a report.  Returns True if the reported user crosses the ban threshold.
        """
        async with self._lock:
            bucket = self.reports.setdefault(reported_id, [])
            if reporter_id not in bucket:
                bucket.append(reporter_id)

            if len(bucket) >= threshold and reported_id not in self.banned_users:
                self.banned_users[reported_id] = BanRecord(
                    user_id=reported_id,
                    reason=f"Auto-banned after {len(bucket)} reports",
                )
                logger.warning("Auto-banned user %s", reported_id)
                return True
            return False

    async def is_banned(self, user_id: int) -> bool:
        async with self._lock:
            return user_id in self.banned_users

    # ── Rate limiting ──────────────────────────────────────────────────────────

    async def check_rate_limit(
        self, user_id: int, max_msgs: int, window_secs: int
    ) -> bool:
        """
        Returns True if the user is within limits (i.e., message is allowed).
        Returns False if the user exceeds the rate limit.
        """
        async with self._lock:
            now = datetime.utcnow()
            bucket = self.rate_limits.get(user_id)
            if bucket is None or (now - bucket.window_start).total_seconds() > window_secs:
                self.rate_limits[user_id] = RateBucket(count=1, window_start=now)
                return True
            bucket.count += 1
            return bucket.count <= max_msgs
