from logging import getLogger
from aiogram import Router, types
from aiogram.filters import Command
from services.rates import RateClient
from services.convert import display_snapshot

log = getLogger("h.rates")
router = Router()
rate_client = RateClient()

@router.message(Command("rates"))
async def rates_handler(m: types.Message):
    log.info("/rates by %s", m.from_user.id if m.from_user else "?")
    try:
        fiat = await rate_client.get_fiat()
        usdt_cny = await rate_client.get_usdt_cny()
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
    except Exception as e:
        log.exception("/rates failed: %s", e)
        text = "⚠️ Rates temporarily unavailable. Try again in a minute."
    await m.answer(text)
