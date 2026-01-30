import re
from decimal import Decimal

NUM = r"([0-9]+(?:\.[0-9]+)?)"

def parse_amount(text: str):
    """
    Returns:
      ("CNY", Decimal)      for plain numbers like "3000"
      ("USD", Decimal)      for "$300", "300 usd", "USD 300", "3000$"
      ("REJECT_USDT", None) if user mentions usdt/tether as input
      (None, None)          otherwise
    """
    t = (text or "").strip().lower()

    # reject usdt input
    if re.search(r"\busdt\b|\btether\b", t):
        return ("REJECT_USDT", None)

    # "$300" or "$ 300"
    m = re.fullmatch(r"\$\s*" + NUM, t)
    if m:
        return ("USD", Decimal(m.group(1)))

    # "300$" or "300 $"
    m = re.fullmatch(NUM + r"\s*\$", t)
    if m:
        return ("USD", Decimal(m.group(1)))

    # "300 usd"
    m = re.fullmatch(NUM + r"\s*(usd|usd\.|dollar|dollars)", t)
    if m:
        return ("USD", Decimal(m.group(1)))

    # "usd 300"
    m = re.fullmatch(r"(usd|usd\.|dollar|dollars)\s*" + NUM, t)
    if m:
        return ("USD", Decimal(m.group(2)))

    # pure number => CNY
    if re.fullmatch(NUM, t):
        return ("CNY", Decimal(t))

    return (None, None)
