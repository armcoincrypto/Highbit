import os
from decimal import Decimal

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHANNEL_ID = os.getenv("CHANNEL_ID", "")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Yerevan")

# Margins
MARGIN_USD_USDT = Decimal(os.getenv("MARGIN_USD_USDT", "-0.025"))  # –2.5% on USD→CNY
MARGIN_AMD_RUB  = Decimal(os.getenv("MARGIN_AMD_RUB",  "0.024"))

# Net/Cache
RATE_TTL_SECONDS = int(os.getenv("RATE_TTL_SECONDS", "600"))
HTTP_TIMEOUT     = int(os.getenv("HTTP_TIMEOUT", "8"))
HTTP_RETRIES     = int(os.getenv("HTTP_RETRIES", "3"))

# Logic
USDT_PARITY_WITH_USD = os.getenv("USDT_PARITY_WITH_USD", "true").lower() in ("1","true","yes","y")
