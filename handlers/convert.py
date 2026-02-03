import logging
from decimal import Decimal, ROUND_HALF_UP

from aiogram import Router, types
from aiogram.filters import Command

from services.htx_p2p import get_htx_p2p_client
from services.cba_rates import get_cba_client
from services.settings import get_settings_service
from utils.parse import parse_amount
from utils.messages import (
    MSG_USDT_NOT_SUPPORTED,
    MSG_CONVERSION_UNAVAILABLE,
)
from config import (
    DISCOUNT_USDT_LOW, DISCOUNT_USDT_HIGH,
    DISCOUNT_FIAT_LOW, DISCOUNT_FIAT_HIGH,
    DISCOUNT_THRESHOLD_USD,
)

log = logging.getLogger(__name__)
router = Router()

# CBA margin for USD/AMD rate (+0.3%) - same as in /rates
CBA_AMD_MARGIN = Decimal("0.003")

# Keep prompt here to preserve Armenian text encoding
CONVERT_PROMPT = (
    "💱 <b>Փdelays / Convert</b>\n\n"
    "Delays delays delays:\n"
    "Enter the amount:\n\n"
    "  • <code>5000</code> — CNY\n"
    "  • <code>500$</code> — USD\n"
    "  • <code>100000֏</code> — AMD\n\n"
    "Delays: <code>/convert 5000</code>"
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
        # Get rates from same sources as /rates
        htx = await get_htx_p2p_client()
        cba = await get_cba_client()
        settings = await get_settings_service()

        usdt_cny, _ = await htx.get_usdt_cny_price()
        cba_rates, _ = await cba.get_rates()

        # Get CBA rates with margin
        usd_amd_raw = cba_rates.get("USD", Decimal("380"))
        usd_amd = (usd_amd_raw * (Decimal("1") + CBA_AMD_MARGIN)).quantize(
            Decimal("0.01"), ROUND_HALF_UP
        )

        # Get dynamic discounts
        discounts = await settings.get_all_discounts()
        usd_disc = discounts.get("usd_low", DISCOUNT_FIAT_LOW)

        # Calculate USD/CNY rate (with discount)
        usd_cny = (usdt_cny * (Decimal("1") + usd_disc)).quantize(
            Decimal("0.01"), ROUND_HALF_UP
        )

        # AMD/CNY = USD_AMD / USD_CNY
        amd_cny = (usd_amd / usd_cny).quantize(Decimal("0.01"), ROUND_HALF_UP)

        if kind == "CNY":
            # CNY → USD, AMD
            usd_out = (amt / usd_cny).quantize(Decimal("0.01"), ROUND_HALF_UP)
            amd_out = (amt * amd_cny).quantize(Decimal("0"), ROUND_HALF_UP)
            text = (
                f"💱 <b>{amt:,.0f} CNY</b> ≈\n\n"
                f"🇺🇸 <b>${usd_out:,.2f}</b> USD\n"
                f"🇦🇲 <b>{amd_out:,.0f}</b> AMD\n\n"
                f"<i>Rate: 1 USD = {usd_cny} CNY</i>"
            )
        elif kind == "USD":
            # USD → CNY, AMD
            cny_out = (amt * usd_cny).quantize(Decimal("0"), ROUND_HALF_UP)
            amd_out = (amt * usd_amd).quantize(Decimal("0"), ROUND_HALF_UP)
            text = (
                f"💱 <b>${amt:,.2f} USD</b> ≈\n\n"
                f"🇨🇳 <b>{cny_out:,.0f}</b> CNY\n"
                f"🇦🇲 <b>{amd_out:,.0f}</b> AMD\n\n"
                f"<i>Rate: 1 USD = {usd_cny} CNY</i>"
            )
        elif kind == "AMD":
            # AMD → CNY, USD
            cny_out = (amt / amd_cny).quantize(Decimal("0"), ROUND_HALF_UP)
            usd_out = (amt / usd_amd).quantize(Decimal("0.01"), ROUND_HALF_UP)
            text = (
                f"💱 <b>{amt:,.0f} AMD</b> ≈\n\n"
                f"🇨🇳 <b>{cny_out:,.0f}</b> CNY\n"
                f"🇺🇸 <b>${usd_out:,.2f}</b> USD\n\n"
                f"<i>Rate: 1 CNY = {amd_cny} AMD</i>"
            )
        else:
            text = CONVERT_PROMPT

    except Exception as e:
        log.exception("/convert failed: %s", e)
        text = MSG_CONVERSION_UNAVAILABLE

    await m.answer(text)
