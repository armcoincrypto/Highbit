"""
Fallback handler for numeric messages.
Users can type just "5000" or "500$" and get conversion without /convert.
Uses same rates as /rates and /convert (HTX P2P + CBA).
"""
import logging
from decimal import Decimal, ROUND_HALF_UP

from aiogram import Router, types

from services.htx_p2p import get_htx_p2p_client
from services.cba_rates import get_cba_client
from services.settings import get_settings_service
from utils.parse import parse_amount
from utils.messages import MSG_USDT_NOT_SUPPORTED, MSG_CONVERSION_UNAVAILABLE
from config import DISCOUNT_FIAT_LOW

log = logging.getLogger(__name__)
router = Router()

# CBA margin (+0.3%) - same as /rates and /convert
CBA_AMD_MARGIN = Decimal("0.003")


@router.message()
async def numeric_fallback(m: types.Message):
    """Handle plain numeric input like '5000' or '500$'."""
    text = (m.text or "").strip()
    kind, amt = parse_amount(text)

    if not kind:
        return  # Ignore non-numeric messages

    log.info("fallback parsed: kind=%s amt=%s from %s", kind, amt, m.from_user.id if m.from_user else "?")

    if kind == "REJECT_USDT":
        return await m.answer(MSG_USDT_NOT_SUPPORTED)

    try:
        # Use same rates as /rates and /convert
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
            usd_out = (amt / usd_cny).quantize(Decimal("0.01"), ROUND_HALF_UP)
            amd_out = (amt * amd_cny).quantize(Decimal("0"), ROUND_HALF_UP)
            msg = (
                f"💱 <b>{amt:,.0f} CNY</b> ≈\n\n"
                f"🇺🇸 <b>${usd_out:,.2f}</b> USD\n"
                f"🇦🇲 <b>{amd_out:,.0f}</b> AMD\n\n"
                f"<i>Rate: 1 USD = {usd_cny} CNY</i>"
            )
        elif kind == "USD":
            cny_out = (amt * usd_cny).quantize(Decimal("0"), ROUND_HALF_UP)
            amd_out = (amt * usd_amd).quantize(Decimal("0"), ROUND_HALF_UP)
            msg = (
                f"💱 <b>${amt:,.2f} USD</b> ≈\n\n"
                f"🇨🇳 <b>{cny_out:,.0f}</b> CNY\n"
                f"🇦🇲 <b>{amd_out:,.0f}</b> AMD\n\n"
                f"<i>Rate: 1 USD = {usd_cny} CNY</i>"
            )
        elif kind == "AMD":
            cny_out = (amt / amd_cny).quantize(Decimal("0"), ROUND_HALF_UP)
            usd_out = (amt / usd_amd).quantize(Decimal("0.01"), ROUND_HALF_UP)
            msg = (
                f"💱 <b>{amt:,.0f} AMD</b> ≈\n\n"
                f"🇨🇳 <b>{cny_out:,.0f}</b> CNY\n"
                f"🇺🇸 <b>${usd_out:,.2f}</b> USD\n\n"
                f"<i>Rate: 1 CNY = {amd_cny} AMD</i>"
            )
        else:
            return

    except Exception as e:
        log.exception("fallback conversion failed: %s", e)
        msg = MSG_CONVERSION_UNAVAILABLE

    await m.answer(msg)
