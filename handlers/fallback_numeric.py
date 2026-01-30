from logging import getLogger
from aiogram import Router, types
from services.rates import RateClient
from services.convert import convert_from_cny, convert_usd_to_cny
from utils.parse import parse_amount

log = getLogger("h.fallback")
router = Router()
rate_client = RateClient()

@router.message()
async def numeric_fallback(m: types.Message):
    text = (m.text or "").strip()
    kind, amt = parse_amount(text)
    if not kind:
        return  # ignore others

    log.info("fallback parsed: kind=%s amt=%s from %s", kind, amt, m.from_user.id if m.from_user else "?")

    if kind == "REJECT_USDT":
        return await m.answer("❌ USDT as input is not supported.\nUse: 3000 (CNY) or 3000$ / $3000 (USD).")

    fiat = await rate_client.get_fiat()
    usdt_cny = await rate_client.get_usdt_cny()
    if kind == "CNY":
        out = convert_from_cny(amt, fiat, usdt_cny)
        msg = (f"💱 {amt} CNY ≈\n"
               f"• USD: {out['USD']}\n"
               f"• AMD: {out['AMD']}\n"
               f"• RUB: {out['RUB']}\n"
               f"• USDT: {out['USDT']}")
    else:
        cny = convert_usd_to_cny(amt, fiat)
        msg = f"💱 ${amt} ≈ {cny} CNY"
    await m.answer(msg)
