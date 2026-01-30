from logging import getLogger
from aiogram import Router, types
from aiogram.filters import Command
from pytz import timezone
from datetime import datetime, time, timedelta
import os

from services.rates import RateClient
from services.convert import display_snapshot
from config import TIMEZONE, CHANNEL_ID

router = Router()
log = getLogger("h.admin")

_ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS","").split(",") if x.strip().isdigit()}

def _is_admin(user: types.User | None) -> bool:
    return bool(user and user.id in _ADMIN_IDS)

def _next_10_o_clock(tzname: str):
    tz = timezone(tzname)
    now = datetime.now(tz)
    today_10 = tz.localize(datetime.combine(now.date(), time(10, 0)))
    if now < today_10:
        return today_10
    return today_10 + timedelta(days=1)

@router.message(Command("when"))
async def when(m: types.Message):
    if not _is_admin(m.from_user):
        return await m.answer("⛔️ Not authorized.")
    tz = timezone(TIMEZONE)
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z")
    nrt = _next_10_o_clock(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S %Z")
    await m.answer(f"⏰ Timezone: {TIMEZONE}\n🕒 Now: {now}\n📮 Next daily post: {nrt}")

@router.message(Command("post_now"))
async def post_now(m: types.Message):
    if not _is_admin(m.from_user):
        return await m.answer("⛔️ Not authorized.")
    try:
        rc = RateClient()
        fiat = await rc.get_fiat()
        usdt_cny = await rc.get_usdt_cny()
        snap = display_snapshot(fiat, usdt_cny)
        text = (
            "📊 Exchange Rates of the Day\n"
            f"🔹 USD → CNY: {snap['USD→CNY']}\n"
            f"🔹 CNY → AMD: {snap['CNY→AMD']}\n"
            f"🔹 CNY → RUB: {snap['CNY→RUB']}\n"
            f"🔹 USDT → CNY: {snap['USDT→CNY']}\n\n"
            "📢 Channel: https://t.me/Highbitchannel\n"
            "Use our bot for any amount: @HighbitChinabot"
        )
        # Use the bot object we already have in the handler:
        if CHANNEL_ID:
            await m.bot.send_message(chat_id=CHANNEL_ID, text=text)
        await m.answer("✅ Posted to channel.")
    except Exception as e:
        log.exception("post_now failed: %s", e)
        await m.answer("⚠️ Failed to post.")
