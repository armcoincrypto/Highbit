import logging
import time
import random
from typing import Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, InlineQuery

log = logging.getLogger(__name__)

# How long to keep user timestamps before pruning (seconds)
CLEANUP_THRESHOLD = 300  # 5 minutes
# How often to run cleanup (every N requests)
CLEANUP_INTERVAL = 100


class AntiFloodMiddleware(BaseMiddleware):
    """
    Rate limiting middleware with automatic cleanup to prevent memory leaks.
    """

    def __init__(self, cooldown_base: float = 0.5):
        super().__init__()
        self.cooldown = cooldown_base
        self.user_ts: Dict[int, float] = {}
        self._request_count = 0

    def _cleanup_old_entries(self):
        """Remove stale entries older than CLEANUP_THRESHOLD."""
        now = time.time()
        cutoff = now - CLEANUP_THRESHOLD
        old_size = len(self.user_ts)

        self.user_ts = {
            uid: ts for uid, ts in self.user_ts.items()
            if ts > cutoff
        }

        removed = old_size - len(self.user_ts)
        if removed > 0:
            log.debug("AntiFlood cleanup: removed %d stale entries", removed)

    async def __call__(self, handler, event, data):
        # Periodic cleanup to prevent memory growth
        self._request_count += 1
        if self._request_count >= CLEANUP_INTERVAL:
            self._cleanup_old_entries()
            self._request_count = 0

        uid = _uid(event)
        if uid is None:
            return await handler(event, data)

        # Allow commands instantly (no rate limiting)
        if isinstance(event, Message) and event.text and event.text.strip().startswith("/"):
            return await handler(event, data)

        now = time.time()
        last = self.user_ts.get(uid, 0.0)
        wait = self.cooldown + random.uniform(-0.15, 0.15)

        if now - last < wait:
            # Drop silently - user is flooding
            return

        self.user_ts[uid] = now
        return await handler(event, data)


def _uid(event) -> int | None:
    """Extract user ID from event."""
    if isinstance(event, Message) and event.from_user:
        return event.from_user.id
    if isinstance(event, CallbackQuery) and event.from_user:
        return event.from_user.id
    if isinstance(event, InlineQuery) and event.from_user:
        return event.from_user.id
    return None
