"""
Inline query handler for conversions.
Users can type @HighbitChinabot 5000 to get conversion results inline.
Uses same rates as /rates and /convert (HTX P2P + CBA).
"""
import logging
from decimal import Decimal, ROUND_HALF_UP

from aiogram import Router, types

from utils.parse import parse_amount
from services.htx_p2p import get_htx_p2p_client
from services.cba_rates import get_cba_client
from services.settings import get_settings_service
from config import DISCOUNT_FIAT_LOW

log = logging.getLogger(__name__)
router = Router()

# CBA margin (+0.3%) - same as /rates and /convert
CBA_AMD_MARGIN = Decimal("0.003")


@router.inline_query()
async def inline_handler(iq: types.InlineQuery):
    q = (iq.query or "").strip()
    log.info("inline query from %s: %r", iq.from_user.id if iq.from_user else "?", q)
    kind, amt = parse_amount(q) if q else (None, None)

    results = []

    if kind == "REJECT_USDT":
        results.append(types.InlineQueryResultArticle(
            id="rej",
            title="USDT input not supported",
            description="Use: 3000 (CNY) or $300 / 300$ (USD) or 100000֏ (AMD)",
            input_message_content=types.InputTextMessageContent(
                message_text="❌ USDT as input is not supported."
            ),
        ))
        return await iq.answer(results=results, cache_time=5, is_personal=True)

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
            title = f"{amt:,.0f} CNY"
            desc = f"${usd_out:,.2f} USD · {amd_out:,.0f} AMD"
            msg = f"💱 {amt:,.0f} CNY ≈ ${usd_out:,.2f} USD · {amd_out:,.0f} AMD"
            results.append(types.InlineQueryResultArticle(
                id="cny",
                title=title,
                description=desc,
                input_message_content=types.InputTextMessageContent(message_text=msg),
            ))
        elif kind == "USD":
            cny_out = (amt * usd_cny).quantize(Decimal("0"), ROUND_HALF_UP)
            amd_out = (amt * usd_amd).quantize(Decimal("0"), ROUND_HALF_UP)
            title = f"${amt:,.2f} USD"
            desc = f"{cny_out:,.0f} CNY · {amd_out:,.0f} AMD"
            msg = f"💱 ${amt:,.2f} USD ≈ {cny_out:,.0f} CNY · {amd_out:,.0f} AMD"
            results.append(types.InlineQueryResultArticle(
                id="usd",
                title=title,
                description=desc,
                input_message_content=types.InputTextMessageContent(message_text=msg),
            ))
        elif kind == "AMD":
            cny_out = (amt / amd_cny).quantize(Decimal("0"), ROUND_HALF_UP)
            usd_out = (amt / usd_amd).quantize(Decimal("0.01"), ROUND_HALF_UP)
            title = f"{amt:,.0f} AMD"
            desc = f"{cny_out:,.0f} CNY · ${usd_out:,.2f} USD"
            msg = f"💱 {amt:,.0f} AMD ≈ {cny_out:,.0f} CNY · ${usd_out:,.2f} USD"
            results.append(types.InlineQueryResultArticle(
                id="amd",
                title=title,
                description=desc,
                input_message_content=types.InputTextMessageContent(message_text=msg),
            ))
        else:
            results.append(types.InlineQueryResultArticle(
                id="hint",
                title="Type: 3000 · $300 · 100000֏",
                description="CNY/USD/AMD conversion",
                input_message_content=types.InputTextMessageContent(
                    message_text="Tip: 3000 (CNY) · $300 (USD) · 100000֏ (AMD)"
                ),
            ))
    except Exception as e:
        log.exception("inline failed: %s", e)
        results.append(types.InlineQueryResultArticle(
            id="err",
            title="Service unavailable",
            description="Please try again shortly.",
            input_message_content=types.InputTextMessageContent(
                message_text="⚠️ Service temporarily unavailable. Please try again."
            ),
        ))

    await iq.answer(results=results, cache_time=5, is_personal=True)
