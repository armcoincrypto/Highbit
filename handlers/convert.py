from logging import getLogger
from aiogram import Router, types
from aiogram.filters import Command
from services.rates import RateClient
from services.convert import convert_from_cny, convert_usd_to_cny
from utils.parse import parse_amount

log = getLogger("h.convert")
router = Router()
rate_client = RateClient()

PROMPT = (
"Խնդրում եմ գրեք ցանկալի գումարի չափը CNY–ով և ես կհաշվեմ այն ձեզ համար.\n"
"Please enter the desired amount in CNY and I'll calculate it for you.\n"
"Пожалуйста, введите сумму в CNY, и я её посчитаю."
)

@router.message(Command("convert"))
async def convert_handler(m: types.Message):
    args = (m.text or "").split(maxsplit=1)
    if len(args) < 2:
        log.info("/convert prompt to %s", m.from_user.id if m.from_user else "?")
        return await m.answer(PROMPT)

    kind, amt = parse_amount(args[1])
    if kind == "REJECT_USDT":
        return await m.answer("❌ USDT as input is not supported.\nUse: 3000 (CNY) or 3000$ / $3000 (USD).")
    if not kind:
        return await m.answer(PROMPT)

    try:
        fiat = await rate_client.get_fiat()
        usdt_cny = await rate_client.get_usdt_cny()
        if kind == "CNY":
            out = convert_from_cny(amt, fiat, usdt_cny)
            text = (f"💱 {amt} CNY ≈\n"
                    f"• USD: {out['USD']}\n"
                    f"• AMD: {out['AMD']}\n"
                    f"• RUB: {out['RUB']}\n"
                    f"• USDT: {out['USDT']}")
        else:
            cny = convert_usd_to_cny(amt, fiat)
            text = f"💱 ${amt} ≈ {cny} CNY"
    except Exception as e:
        log.exception("/convert failed: %s", e)
        text = "⚠️ Conversion temporarily unavailable, please try again."
    await m.answer(text)
