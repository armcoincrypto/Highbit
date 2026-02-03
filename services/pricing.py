"""
Pricing service for CNY transfers.
Combines HTX P2P rates with CBA official rates and applies tiered discounts.
"""
import logging
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from enum import Enum

from config import (
    MIN_ORDER_CNY,
    DISCOUNT_THRESHOLD_USD,
    DISCOUNT_FIAT_HIGH,
    DISCOUNT_FIAT_LOW,
    DISCOUNT_USDT_HIGH,
    DISCOUNT_USDT_LOW,
)
from services.htx_p2p import get_htx_p2p_client
from services.cba_rates import get_cba_client
from services.settings import get_settings_service

# CBA margin for USD/AMD rate (+0.3%) - same as in utils/messages.py
CBA_AMD_MARGIN = Decimal("0.003")

log = logging.getLogger(__name__)


class PaymentCurrency(Enum):
    """Payment currencies supported."""
    AMD = "AMD"
    USD = "USD"
    RUB = "RUB"
    USDT = "USDT"


class TransferMethod(Enum):
    """Transfer methods to China."""
    ALIPAY = "alipay"
    WECHAT = "wechat"
    BANK = "bank"


@dataclass
class PricingResult:
    """Result of pricing calculation."""
    # Input
    cny_amount: Decimal
    payment_currency: PaymentCurrency
    transfer_method: TransferMethod

    # Base rate
    htx_usdt_cny: Decimal  # HTX P2P rate: 1 USDT = X CNY

    # USD equivalent (for tier selection)
    usd_equivalent: Decimal

    # Discount
    discount_percent: Decimal
    discount_tier: str  # "high" or "low"

    # Final amounts
    usdt_needed: Decimal  # USDT needed to buy the CNY
    amount_due: Decimal  # Final amount in payment currency

    # CBA rates snapshot
    cba_usd_amd: Decimal
    cba_rub_amd: Optional[Decimal]
    cba_cny_amd: Decimal

    # Metadata
    htx_timestamp: float
    cba_timestamp: float
    htx_source: str
    cba_source: str

    def to_dict(self) -> dict:
        """Convert to dictionary for storage/display."""
        return {
            "cny_amount": str(self.cny_amount),
            "payment_currency": self.payment_currency.value,
            "transfer_method": self.transfer_method.value,
            "htx_usdt_cny": str(self.htx_usdt_cny),
            "usd_equivalent": str(self.usd_equivalent),
            "discount_percent": str(self.discount_percent),
            "discount_tier": self.discount_tier,
            "usdt_needed": str(self.usdt_needed),
            "amount_due": str(self.amount_due),
            "cba_usd_amd": str(self.cba_usd_amd),
            "cba_rub_amd": str(self.cba_rub_amd) if self.cba_rub_amd else None,
            "cba_cny_amd": str(self.cba_cny_amd),
            "htx_timestamp": self.htx_timestamp,
            "cba_timestamp": self.cba_timestamp,
            "htx_source": self.htx_source,
            "cba_source": self.cba_source,
        }


class PricingError(Exception):
    """Pricing calculation error."""
    pass


class MinimumOrderError(PricingError):
    """Order below minimum CNY amount."""
    def __init__(self, cny_amount: Decimal, min_amount: int = MIN_ORDER_CNY):
        self.cny_amount = cny_amount
        self.min_amount = min_amount
        super().__init__(f"Minimum order is {min_amount} CNY, got {cny_amount}")


async def calculate_pricing(
    cny_amount: Decimal,
    payment_currency: PaymentCurrency,
    transfer_method: TransferMethod,
) -> PricingResult:
    """
    Calculate pricing for a CNY transfer.

    Args:
        cny_amount: Amount of CNY to transfer (must be >= MIN_ORDER_CNY)
        payment_currency: Currency user will pay with
        transfer_method: Transfer method (Alipay/WeChat/Bank)

    Returns:
        PricingResult with all calculation details

    Raises:
        MinimumOrderError: If cny_amount < MIN_ORDER_CNY
        PricingError: If pricing calculation fails
    """
    # Validate minimum order
    if cny_amount < MIN_ORDER_CNY:
        raise MinimumOrderError(cny_amount)

    # Fetch rates
    htx_client = await get_htx_p2p_client()
    cba_client = await get_cba_client()
    settings = await get_settings_service()

    htx_price, htx_meta = await htx_client.get_usdt_cny_price()
    cba_rates, cba_meta = await cba_client.get_rates()

    # Get required CBA rates (with margin applied to USD/AMD)
    cba_usd_amd_raw = cba_rates.get("USD")
    cba_cny_amd = cba_rates.get("CNY")
    cba_rub_amd = cba_rates.get("RUB")

    if not cba_usd_amd_raw or not cba_cny_amd:
        raise PricingError("Required CBA rates (USD, CNY) not available")

    # Apply +0.3% margin to USD/AMD rate (same as /rates display)
    cba_usd_amd = (cba_usd_amd_raw * (Decimal("1") + CBA_AMD_MARGIN)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    # Calculate USD equivalent using CBA cross rate
    # CNY to USD = (CNY in AMD) / (USD in AMD)
    cny_to_usd_rate = cba_cny_amd / cba_usd_amd
    usd_equivalent = cny_amount * cny_to_usd_rate

    # Determine discount tier
    is_high_tier = usd_equivalent >= DISCOUNT_THRESHOLD_USD
    is_usdt = payment_currency == PaymentCurrency.USDT

    # Get dynamic discounts from settings (same as /rates)
    discounts = await settings.get_all_discounts()

    if is_usdt:
        discount = discounts.get("usdt_high" if is_high_tier else "usdt_low",
                                  DISCOUNT_USDT_HIGH if is_high_tier else DISCOUNT_USDT_LOW)
    else:
        discount = discounts.get("usd_high" if is_high_tier else "usd_low",
                                  DISCOUNT_FIAT_HIGH if is_high_tier else DISCOUNT_FIAT_LOW)

    discount_tier = "high" if is_high_tier else "low"

    # Calculate USDT needed (base amount before discount)
    # usdt_needed = cny_amount / htx_price (how many USDT to get that CNY)
    usdt_base = cny_amount / htx_price

    # Apply discount (negative discount means user pays less)
    # Final USDT = base * (1 + discount)  where discount is negative
    usdt_needed = usdt_base * (Decimal(1) + discount)

    # Calculate amount due in payment currency
    if payment_currency == PaymentCurrency.USDT:
        amount_due = usdt_needed
    elif payment_currency == PaymentCurrency.USD:
        # USDT ≈ USD (1:1 parity assumption)
        amount_due = usdt_needed
    elif payment_currency == PaymentCurrency.AMD:
        # Convert USDT (≈USD) to AMD
        amount_due = usdt_needed * cba_usd_amd
    elif payment_currency == PaymentCurrency.RUB:
        if not cba_rub_amd:
            raise PricingError("RUB rate not available from CBA")
        # Convert USDT (≈USD) to RUB via AMD
        # USD to RUB = (USD in AMD) / (RUB in AMD)
        usd_to_rub = cba_usd_amd / cba_rub_amd
        amount_due = usdt_needed * usd_to_rub
    else:
        raise PricingError(f"Unknown payment currency: {payment_currency}")

    # Round appropriately
    if payment_currency == PaymentCurrency.USDT:
        amount_due = amount_due.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        usdt_needed = usdt_needed.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    elif payment_currency == PaymentCurrency.USD:
        amount_due = amount_due.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    elif payment_currency == PaymentCurrency.AMD:
        amount_due = amount_due.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    elif payment_currency == PaymentCurrency.RUB:
        amount_due = amount_due.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    usd_equivalent = usd_equivalent.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return PricingResult(
        cny_amount=cny_amount,
        payment_currency=payment_currency,
        transfer_method=transfer_method,
        htx_usdt_cny=htx_price,
        usd_equivalent=usd_equivalent,
        discount_percent=discount * 100,  # Convert to percentage
        discount_tier=discount_tier,
        usdt_needed=usdt_needed.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        amount_due=amount_due,
        cba_usd_amd=cba_usd_amd,
        cba_rub_amd=cba_rub_amd,
        cba_cny_amd=cba_cny_amd,
        htx_timestamp=htx_meta.get("timestamp", 0),
        cba_timestamp=cba_meta.get("timestamp", 0),
        htx_source=htx_meta.get("source", "unknown"),
        cba_source=cba_meta.get("source", "unknown"),
    )


def format_pricing_summary(result: PricingResult, lang: str = "hy") -> str:
    """
    Format pricing result for display.

    Args:
        result: PricingResult object
        lang: Language code ("hy" for Armenian, "en" for English, "ru" for Russian)
    """
    currency_symbols = {
        PaymentCurrency.AMD: "֏",
        PaymentCurrency.USD: "$",
        PaymentCurrency.RUB: "₽",
        PaymentCurrency.USDT: "USDT",
    }

    method_names = {
        TransferMethod.ALIPAY: "Alipay",
        TransferMethod.WECHAT: "WeChat",
        TransferMethod.BANK: "Բdelays Delays",
    }

    symbol = currency_symbols.get(result.payment_currency, result.payment_currency.value)
    method = method_names.get(result.transfer_method, result.transfer_method.value)

    # Format amount due
    if result.payment_currency in (PaymentCurrency.AMD, PaymentCurrency.RUB):
        amount_str = f"{result.amount_due:,.0f}"
    else:
        amount_str = f"{result.amount_due:,.2f}"

    from datetime import datetime

    htx_time = datetime.fromtimestamp(result.htx_timestamp).strftime("%H:%M:%S")
    cba_time = datetime.fromtimestamp(result.cba_timestamp).strftime("%H:%M:%S")

    if lang == "en":
        return (
            f"💰 **Transfer Summary**\n\n"
            f"📤 CNY Amount: ¥{result.cny_amount:,.0f}\n"
            f"📱 Method: {method}\n"
            f"💳 Pay with: {result.payment_currency.value}\n\n"
            f"📊 **Calculation:**\n"
            f"• Base rate (HTX P2P): 1 USDT = {result.htx_usdt_cny:.2f} CNY\n"
            f"• USD equivalent: ${result.usd_equivalent:,.2f}\n"
            f"• Discount tier: {result.discount_tier} ({result.discount_percent:+.1f}%)\n\n"
            f"💵 **Amount Due: {symbol} {amount_str}**\n\n"
            f"⏱ Rates updated: HTX {htx_time}, CBA {cba_time}"
        )
    else:
        # Armenian (default)
        return (
            f"💰 **Փdelays Delays**\n\n"
            f"📤 CNY Գdelays: ¥{result.cny_amount:,.0f}\n"
            f"📱 Մdelays: {method}\n"
            f"💳 Վdelays delaysdelays: {result.payment_currency.value}\n\n"
            f"📊 **Հdelays:**\n"
            f"• Բdelays delays (HTX P2P): 1 USDT = {result.htx_usdt_cny:.2f} CNY\n"
            f"• USD Համdelays: ${result.usd_equivalent:,.2f}\n"
            f"• Զdelays delays: {result.discount_tier} ({result.discount_percent:+.1f}%)\n\n"
            f"💵 **Delays Վdelays: {symbol} {amount_str}**\n\n"
            f"⏱ Delays delaysdelays: HTX {htx_time}, CBA {cba_time}"
        )


def format_pricing_short(result: PricingResult) -> str:
    """Format a short one-line pricing summary."""
    currency_symbols = {
        PaymentCurrency.AMD: "֏",
        PaymentCurrency.USD: "$",
        PaymentCurrency.RUB: "₽",
        PaymentCurrency.USDT: "USDT ",
    }

    symbol = currency_symbols.get(result.payment_currency, "")

    if result.payment_currency in (PaymentCurrency.AMD, PaymentCurrency.RUB):
        amount_str = f"{result.amount_due:,.0f}"
    else:
        amount_str = f"{result.amount_due:,.2f}"

    return f"¥{result.cny_amount:,.0f} → {symbol}{amount_str} ({result.discount_percent:+.1f}%)"
