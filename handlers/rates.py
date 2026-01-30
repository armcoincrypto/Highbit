import logging

from aiogram import Router, types
from aiogram.filters import Command

from services.htx_p2p import get_htx_p2p_client
from services.cba_rates import get_cba_client
from utils.messages import format_daily_rates_new, MSG_RATES_UNAVAILABLE

log = logging.getLogger(__name__)
router = Router()


@router.message(Command("rates"))
async def rates_handler(m: types.Message):
    """Display current exchange rates using CBA + HTX P2P services."""
    log.info("/rates by %s", m.from_user.id if m.from_user else "?")

    try:
        # Fetch from new services
        htx = await get_htx_p2p_client()
        cba = await get_cba_client()

        # Get rates (both have caching + fallback)
        usdt_cny, htx_meta = await htx.get_usdt_cny_price()
        cba_rates, cba_meta = await cba.get_rates()

        # Format message
        text = format_daily_rates_new(usdt_cny, cba_rates, htx_meta)

        # Add stale warning if data is old
        if htx_meta.get("stale") or cba_meta.get("stale"):
            text += "\n\n⚠️ <i>Some rates may be cached due to API issues</i>"

    except Exception as e:
        log.exception("/rates failed: %s", e)
        text = MSG_RATES_UNAVAILABLE

    await m.answer(text)
