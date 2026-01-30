import logging

from aiogram import Router, types
from aiogram.filters import Command

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

# Keep prompt here to preserve Armenian text encoding
CONVERT_PROMPT = (
    "Խնդրում եմ գրեք ցանկալի գումարի չափը CNY–ով և ես կհաշվեմ այն ձեզ համար.\n"
    "Please enter the desired amount in CNY and I'll calculate it for you.\n"
    "Пожалуйста, введите сумму в CNY, и я её посчитаю."
)


@router.message(Command("convert"))
async def convert_handler(m: types.Message):
    args = (m.text or "").split(maxsplit=1)
    if len(args) < 2:
        log.info("/convert prompt to %s", m.from_user.id if m.from_user else "?")
        return await m.answer(CONVERT_PROMPT)

    kind, amt = parse_amount(args[1])
    if kind == "REJECT_USDT":
        return await m.answer(MSG_USDT_NOT_SUPPORTED)
    if not kind:
        return await m.answer(CONVERT_PROMPT)

    try:
        rc = await get_rate_client()
        fiat = await rc.get_fiat()
        usdt_cny = await rc.get_usdt_cny()

        if kind == "CNY":
            out = convert_from_cny(amt, fiat, usdt_cny)
            text = format_cny_conversion(amt, out)
        else:
            cny = convert_usd_to_cny(amt, fiat)
            text = format_usd_conversion(amt, cny)
    except Exception as e:
        log.exception("/convert failed: %s", e)
        text = MSG_CONVERSION_UNAVAILABLE

    await m.answer(text)
