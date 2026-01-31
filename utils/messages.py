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
    htx_meta: Optional[dict] = None
) -> str:
    """
    Format daily rates using new CBA + HTX P2P services.
    Shows "OUR RATES" with both discount tiers.

    Args:
        usdt_cny: USDT/CNY price from HTX P2P (market rate)
        cba_rates: CBA official rates (AMD-based)
        htx_meta: Metadata from HTX P2P (source, stale flag)

    Returns:
        Formatted rates message with both discount tiers
    """
    from config import (
        DISCOUNT_USDT_LOW, DISCOUNT_USDT_HIGH,
        DISCOUNT_FIAT_LOW, DISCOUNT_FIAT_HIGH
    )

    # Get CBA rate: how many AMD per 1 USD
    usd_amd = cba_rates.get("USD", Decimal("380"))

    # Multipliers for both tiers
    # LOW = standard rate (< $4000), HIGH = VIP rate (>= $4000)
    low_mult = Decimal("1") + DISCOUNT_USDT_LOW   # e.g., 0.987 for -1.3%
    high_mult = Decimal("1") + DISCOUNT_USDT_HIGH  # e.g., 0.991 for -0.9%

    # USDT/CNY rates for both tiers (discounted)
    usdt_cny_standard = (usdt_cny * low_mult).quantize(Decimal("0.01"), ROUND_HALF_UP)
    usdt_cny_vip = (usdt_cny * high_mult).quantize(Decimal("0.01"), ROUND_HALF_UP)

    # AMD/CNY rate = USD_AMD / USDT_CNY
    # Example: 380 / 6.85 = 55.47 AMD per 1 CNY
    cny_amd_standard = (usd_amd / usdt_cny_standard).quantize(Decimal("0.01"), ROUND_HALF_UP)
    cny_amd_vip = (usd_amd / usdt_cny_vip).quantize(Decimal("0.01"), ROUND_HALF_UP)

    # Source indicator
    source = ""
    if htx_meta:
        if htx_meta.get("stale"):
            source = " ⚠️"

    return (
        "📊 <b>Highbit — Our Rates</b>\n\n"
        f"🔹 1 USDT = <b>{usdt_cny_standard}</b> CNY\n"
        f"🔹 1 USDT = <b>{usdt_cny_vip}</b> CNY  💎 $4000+\n\n"
        f"🔹 1 CNY = <b>{cny_amd_standard}</b> AMD\n"
        f"🔹 1 CNY = <b>{cny_amd_vip}</b> AMD  💎 $4000+{source}\n\n"
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


# Error messages
MSG_RATES_UNAVAILABLE = "⚠️ Rates temporarily unavailable. Try again in a minute."
MSG_CONVERSION_UNAVAILABLE = "⚠️ Conversion temporarily unavailable, please try again."
MSG_USDT_NOT_SUPPORTED = "❌ USDT as input is not supported.\nUse: 3000 (CNY) or 3000$ / $3000 (USD)."
