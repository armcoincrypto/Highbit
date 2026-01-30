import time, random
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, InlineQuery

class AntiFloodMiddleware(BaseMiddleware):
    def __init__(self, cooldown_base: float = 0.5):
        super().__init__()
        self.cooldown = cooldown_base
        self.user_ts = {}

    async def __call__(self, handler, event, data):
        uid = _uid(event)
        if uid is None:
            return await handler(event, data)

        # allow commands instantly
        if isinstance(event, Message) and event.text and event.text.strip().startswith("/"):
            return await handler(event, data)

        now = time.time()
        last = self.user_ts.get(uid, 0.0)
        wait = self.cooldown + random.uniform(-0.15, 0.15)
        if now - last < wait:
            return  # drop silently
        self.user_ts[uid] = now
        return await handler(event, data)

def _uid(event):
    if isinstance(event, Message) and event.from_user:
        return event.from_user.id
    if isinstance(event, CallbackQuery) and event.from_user:
        return event.from_user.id
    if isinstance(event, InlineQuery) and event.from_user:
        return event.from_user.id
    return None
