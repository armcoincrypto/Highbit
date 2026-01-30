import logging

from aiogram import Router, types

from services.rates import get_rate_client
from services.convert import convert_from_cny, convert_usd_to_cny
from utils.parse import parse_amount
from utils.messages import (
    format_cny_conversion,
    format_usd_conversion,
    MSG_USDT_NOT_SUPPORTED,
    MSG_CONVERSION_UNAVAILABLE,
)

log = logging.getLogger(__name__)
router = Router()


@router.message()
async def numeric_fallback(m: types.Message):
    text = (m.text or "").strip()
    kind, amt = parse_amount(text)

    if not kind:
        return  # Ignore non-numeric messages

    log.info("fallback parsed: kind=%s amt=%s from %s", kind, amt, m.from_user.id if m.from_user else "?")

    if kind == "REJECT_USDT":
        return await m.answer(MSG_USDT_NOT_SUPPORTED)

    try:
        rc = await get_rate_client()
        fiat = await rc.get_fiat()
        usdt_cny = await rc.get_usdt_cny()

        if kind == "CNY":
            out = convert_from_cny(amt, fiat, usdt_cny)
            msg = format_cny_conversion(amt, out)
        else:
            cny = convert_usd_to_cny(amt, fiat)
            msg = format_usd_conversion(amt, cny)
    except Exception as e:
        log.exception("fallback conversion failed: %s", e)
        msg = MSG_CONVERSION_UNAVAILABLE

    await m.answer(msg)
