import logging

from aiogram import Router, types
from aiogram.filters import Command

from services.rates import get_rate_client
from utils.messages import format_daily_rates, MSG_RATES_UNAVAILABLE

log = logging.getLogger(__name__)
router = Router()


@router.message(Command("rates"))
async def rates_handler(m: types.Message):
    log.info("/rates by %s", m.from_user.id if m.from_user else "?")
    try:
        rc = await get_rate_client()
        fiat = await rc.get_fiat()
        usdt_cny = await rc.get_usdt_cny()
        text = format_daily_rates(fiat, usdt_cny)
    except Exception as e:
        log.exception("/rates failed: %s", e)
        text = MSG_RATES_UNAVAILABLE

    await m.answer(text)
