from decimal import Decimal
from config import MARGIN_USD_USDT, MARGIN_AMD_RUB, USDT_PARITY_WITH_USD
from utils.formatting import trunc1_str, trunc2_str, to_int_str

def _usd_to_cny_rate_after_margin(fiat: dict) -> Decimal:
    # global USD→CNY = 1 / (USD per CNY)
    base = (Decimal(1) / fiat["USD"])
    # apply margin to USD→CNY
    return base * (Decimal(1) + MARGIN_USD_USDT)

def display_snapshot(fiat: dict, usdt_cny: Decimal):
    usd_to_cny = _usd_to_cny_rate_after_margin(fiat)
    # parity for USDT→CNY (else: use market USDT→CNY with same margin)
    if USDT_PARITY_WITH_USD:
        usdt_to_cny = usd_to_cny
    else:
        usdt_to_cny = usdt_cny * (Decimal(1) + MARGIN_USD_USDT)

    cny_to_amd  = fiat["AMD"] * (Decimal(1) + MARGIN_AMD_RUB)
    cny_to_rub  = fiat["RUB"] * (Decimal(1) + MARGIN_AMD_RUB)

    return {
        "USD→CNY":  trunc2_str(usd_to_cny),
        "CNY→AMD":  trunc2_str(cny_to_amd),
        "CNY→RUB":  trunc2_str(cny_to_rub),
        "USDT→CNY": trunc2_str(usdt_to_cny),
    }

def convert_from_cny(amount_cny: Decimal, fiat: dict, usdt_cny: Decimal):
    # USD = amount / (USD→CNY with margin)
    usd_to_cny = _usd_to_cny_rate_after_margin(fiat)
    usd  = amount_cny / usd_to_cny
    usdt = usd if USDT_PARITY_WITH_USD else amount_cny / (usdt_cny * (Decimal(1) + MARGIN_USD_USDT))
    amd  = fiat["AMD"] * amount_cny * (Decimal(1) + MARGIN_AMD_RUB)
    rub  = fiat["RUB"] * amount_cny * (Decimal(1) + MARGIN_AMD_RUB)

    return {
        "USD":  trunc1_str(usd),
        "AMD":  to_int_str(amd),
        "RUB":  to_int_str(rub),
        "USDT": trunc1_str(usdt),
    }

def convert_usd_to_cny(amount_usd: Decimal, fiat: dict):
    usd_to_cny = _usd_to_cny_rate_after_margin(fiat)
    cny = amount_usd * usd_to_cny
    return to_int_str(cny)
