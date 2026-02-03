"""
Centralized message templates for the bot.
DRY: All rate display messages use these functions.
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Optional

from services.convert import display_snapshot


def format_daily_rates(fiat: Dict[str, Decimal], usdt_cny: Decimal) -> str:
    """
    Format the daily rates message (legacy version).
    Used by: legacy code that still uses services.rates
    """
    snap = display_snapshot(fiat, usdt_cny)
    return (
        "📊 Exchange Rates of the Day\n"
        f"🔹 USD → CNY: {snap['USD→CNY']}\n"
        f"🔹 CNY → AMD: {snap['CNY→AMD']}\n"
        f"🔹 CNY → RUB: {snap['CNY→RUB']}\n"
        f"🔹 USDT → CNY: {snap['USDT→CNY']}\n\n"
        "📢 Channel: https://t.me/Highbitchannel\n"
        "Use our bot for any amount: @HighbitChinabot"
    )


def format_daily_rates_new(
    usdt_cny: Decimal,
    cba_rates: Dict[str, Decimal],
    htx_meta: Optional[dict] = None,
    discounts: Optional[Dict[str, Decimal]] = None
) -> str:
    """
    Format daily rates using new CBA + HTX P2P services.
    Shows rates for USD, AMD, and USDT with their respective thresholds.

    Args:
        usdt_cny: USDT/CNY price from P2P (market rate)
        cba_rates: CBA official rates (AMD-based)
        htx_meta: Metadata from P2P (source, stale flag)
        discounts: Dynamic discount values from settings service
                   Keys: usd_low, usd_high, amd_low, amd_high, usdt_low, usdt_high

    Returns:
        Formatted rates message with beautiful layout
    """
    from config import (
        DISCOUNT_USDT_LOW, DISCOUNT_USDT_HIGH,
        DISCOUNT_FIAT_LOW, DISCOUNT_FIAT_HIGH
    )

    # CBA margin for USD/AMD rate (+0.3%)
    CBA_AMD_MARGIN = Decimal("0.003")

    # Get CBA rate: how many AMD per 1 USD (with margin)
    usd_amd_raw = cba_rates.get("USD", Decimal("380"))
    usd_amd = (usd_amd_raw * (Decimal("1") + CBA_AMD_MARGIN)).quantize(Decimal("0.01"), ROUND_HALF_UP)

    # Use dynamic discounts if provided, otherwise fallback to config
    if discounts:
        usd_low_disc = discounts.get("usd_low", DISCOUNT_FIAT_LOW)
        usd_high_disc = discounts.get("usd_high", DISCOUNT_FIAT_HIGH)
        amd_low_disc = discounts.get("amd_low", DISCOUNT_FIAT_LOW)
        amd_high_disc = discounts.get("amd_high", DISCOUNT_FIAT_HIGH)
        usdt_low_disc = discounts.get("usdt_low", DISCOUNT_USDT_LOW)
        usdt_high_disc = discounts.get("usdt_high", DISCOUNT_USDT_HIGH)
    else:
        usd_low_disc = DISCOUNT_FIAT_LOW
        usd_high_disc = DISCOUNT_FIAT_HIGH
        amd_low_disc = DISCOUNT_FIAT_LOW
        amd_high_disc = DISCOUNT_FIAT_HIGH
        usdt_low_disc = DISCOUNT_USDT_LOW
        usdt_high_disc = DISCOUNT_USDT_HIGH

    # USD multipliers
    usd_low = Decimal("1") + usd_low_disc
    usd_high = Decimal("1") + usd_high_disc

    # AMD multipliers (can be different from USD)
    amd_low = Decimal("1") + amd_low_disc
    amd_high = Decimal("1") + amd_high_disc

    # USDT multipliers
    usdt_low = Decimal("1") + usdt_low_disc
    usdt_high = Decimal("1") + usdt_high_disc

    # USD/CNY rates (using USD discount)
    usd_cny_standard = (usdt_cny * usd_low).quantize(Decimal("0.01"), ROUND_HALF_UP)
    usd_cny_vip = (usdt_cny * usd_high).quantize(Decimal("0.01"), ROUND_HALF_UP)

    # AMD/CNY rates = USD_AMD / USD_CNY (using displayed USD/CNY rate)
    # This ensures consistency: if 1 USD = 6.81 CNY, then AMD/CNY = 379/6.81
    cny_amd_standard = (usd_amd / usd_cny_standard).quantize(Decimal("0.01"), ROUND_HALF_UP)
    cny_amd_vip = (usd_amd / usd_cny_vip).quantize(Decimal("0.01"), ROUND_HALF_UP)

    # USDT/CNY rates (using USDT discount)
    usdt_cny_standard = (usdt_cny * usdt_low).quantize(Decimal("0.01"), ROUND_HALF_UP)
    usdt_cny_vip = (usdt_cny * usdt_high).quantize(Decimal("0.01"), ROUND_HALF_UP)

    # Source indicator
    source = ""
    if htx_meta:
        if htx_meta.get("stale"):
            source = " ⚠️"

    return (
        "📊 <b>Highbit — Our Rates</b>\n\n"
        f"🇺🇸 USD → CNY\n"
        f"├ &lt; $4,000:     1 USD = <b>{usd_cny_standard}</b> CNY\n"
        f"└ ≥ $4,000:     1 USD = <b>{usd_cny_vip}</b> CNY\n\n"
        f"🇦🇲 AMD → CNY\n"
        f"├ &lt; 1.5M AMD:  1 CNY = <b>{cny_amd_standard}</b> AMD\n"
        f"└ ≥ 1.5M AMD:  1 CNY = <b>{cny_amd_vip}</b> AMD\n\n"
        f"📲 USDT → CNY\n"
        f"├ &lt; $4,000:     1 USDT = <b>{usdt_cny_standard}</b> CNY\n"
        f"└ ≥ $4,000:     1 USDT = <b>{usdt_cny_vip}</b> CNY{source}\n\n"
        "📢 @Highbitchannel\n"
        "🤖 @Highbitagent"
    )


def format_cny_conversion(amount: Decimal, out: Dict[str, str]) -> str:
    """Format CNY to multi-currency conversion result."""
    return (
        f"💱 {amount} CNY ≈\n"
        f"• USD: {out['USD']}\n"
        f"• AMD: {out['AMD']}\n"
        f"• RUB: {out['RUB']}\n"
        f"• USDT: {out['USDT']}"
    )


def format_usd_conversion(amount: Decimal, cny: str) -> str:
    """Format USD to CNY conversion result."""
    return f"💱 ${amount} ≈ {cny} CNY"


def format_amd_conversion(amount: Decimal, cny: str) -> str:
    """Format AMD to CNY conversion result."""
    return f"💱 {amount:,.0f} AMD ≈ {cny} CNY"


# Error messages (bilingual)
MSG_RATES_UNAVAILABLE = "⚠️ Փdelays անdelays. Delaysdelays 1 delays delays.\n⚠️ Exchange rates unavailable. Please try again in 1 minute."
MSG_CONVERSION_UNAVAILABLE = "⚠️ Հdelays delays delays delays. Xdelaysdelay delays.\n⚠️ Conversion unavailable. Please try again later."
MSG_USDT_NOT_SUPPORTED = "❌ USDT delays delays delays delays.\n❌ USDT conversion not supported.\nExample: 3000 (CNY) or 3000$ / $3000 (USD)."
