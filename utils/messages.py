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

    Args:
        usdt_cny: USDT/CNY price from HTX P2P
        cba_rates: CBA official rates (AMD-based)
        htx_meta: Metadata from HTX P2P (source, stale flag)

    Returns:
        Formatted rates message
    """
    # Get CBA rates (how many AMD per 1 unit of foreign currency)
    usd_amd = cba_rates.get("USD", Decimal("0"))
    rub_amd = cba_rates.get("RUB", Decimal("0"))
    cny_amd = cba_rates.get("CNY", Decimal("0"))

    # Calculate cross rates
    # USD → CNY: (1 USD in AMD) / (1 CNY in AMD) = how many CNY per 1 USD
    if cny_amd > 0:
        usd_cny = (usd_amd / cny_amd).quantize(Decimal("0.0001"), ROUND_HALF_UP)
        cny_rub = (cny_amd / rub_amd).quantize(Decimal("0.0001"), ROUND_HALF_UP) if rub_amd > 0 else Decimal("0")
    else:
        usd_cny = Decimal("0")
        cny_rub = Decimal("0")

    # Format USDT/CNY
    usdt_cny_fmt = usdt_cny.quantize(Decimal("0.01"), ROUND_HALF_UP)

    # Format CNY/AMD
    cny_amd_fmt = cny_amd.quantize(Decimal("0.01"), ROUND_HALF_UP)

    # Source indicator
    source = ""
    if htx_meta:
        if htx_meta.get("stale"):
            source = " ⚠️"
        elif htx_meta.get("source") == "p2p_army_htx":
            source = " 🟢"

    return (
        "📊 <b>Exchange Rates of the Day</b>\n\n"
        f"🔹 USD → CNY: <b>{usd_cny}</b> (CBA)\n"
        f"🔹 CNY → AMD: <b>{cny_amd_fmt}</b> (CBA)\n"
        f"🔹 CNY → RUB: <b>{cny_rub}</b> (CBA)\n"
        f"🔹 USDT → CNY: <b>{usdt_cny_fmt}</b> (HTX P2P){source}\n\n"
        "📢 Channel: @Highbitchannel\n"
        "🤖 Bot: @HighbitChinabot"
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
