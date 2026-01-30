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
    Shows "OUR RATES" with discount applied (customer-facing).

    Args:
        usdt_cny: USDT/CNY price from HTX P2P (market rate)
        cba_rates: CBA official rates (AMD-based)
        htx_meta: Metadata from HTX P2P (source, stale flag)

    Returns:
        Formatted rates message with discounted rates
    """
    from config import DISCOUNT_USDT_LOW, DISCOUNT_FIAT_LOW

    # Get CBA rates (how many AMD per 1 unit of foreign currency)
    usd_amd = cba_rates.get("USD", Decimal("0"))
    rub_amd = cba_rates.get("RUB", Decimal("0"))
    cny_amd = cba_rates.get("CNY", Decimal("0"))

    # Calculate cross rates from CBA
    if cny_amd > 0:
        usd_cny_market = usd_amd / cny_amd
        cny_rub_market = cny_amd / rub_amd if rub_amd > 0 else Decimal("0")
    else:
        usd_cny_market = Decimal("0")
        cny_rub_market = Decimal("0")

    # Apply discount to show "OUR RATE" (customer pays less = gets more CNY per unit)
    # Discount is negative (e.g., -0.015 = -1.5%), so (1 + discount) < 1
    # Our rate = market / (1 + discount) → higher rate for customer
    fiat_multiplier = Decimal("1") / (Decimal("1") + DISCOUNT_FIAT_LOW)
    usdt_multiplier = Decimal("1") / (Decimal("1") + DISCOUNT_USDT_LOW)

    # Our rates (what customer gets)
    our_usd_cny = (usd_cny_market * fiat_multiplier).quantize(Decimal("0.0001"), ROUND_HALF_UP)
    our_cny_rub = (cny_rub_market * fiat_multiplier).quantize(Decimal("0.0001"), ROUND_HALF_UP)
    our_usdt_cny = (usdt_cny * usdt_multiplier).quantize(Decimal("0.01"), ROUND_HALF_UP)

    # CNY/AMD (how much AMD per 1 CNY - apply inverse)
    our_cny_amd = (cny_amd / fiat_multiplier).quantize(Decimal("0.01"), ROUND_HALF_UP)

    # Source indicator
    source = ""
    if htx_meta:
        if htx_meta.get("stale"):
            source = " ⚠️"

    # Calculate discount % for display
    usdt_discount_pct = abs(DISCOUNT_USDT_LOW * 100)
    fiat_discount_pct = abs(DISCOUNT_FIAT_LOW * 100)

    return (
        "📊 <b>Highbit — Our Rates</b>\n\n"
        f"🔹 1 USD = <b>{our_usd_cny}</b> CNY\n"
        f"🔹 1 CNY = <b>{our_cny_amd}</b> AMD\n"
        f"🔹 1 CNY = <b>{our_cny_rub}</b> RUB\n"
        f"🔹 1 USDT = <b>{our_usdt_cny}</b> CNY{source}\n\n"
        f"💰 <i>Discounts: FIAT -{fiat_discount_pct:.1f}%, USDT -{usdt_discount_pct:.1f}%</i>\n"
        f"📋 Min order: 5000 CNY\n\n"
        "📢 @Highbitchannel\n"
        "🤖 @HighbitChinabot"
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
