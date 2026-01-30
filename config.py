import os
from decimal import Decimal

# =============================================================================
# Bot Configuration
# =============================================================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHANNEL_ID = os.getenv("CHANNEL_ID", "")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "")  # For transfer request notifications
ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()}
TIMEZONE = os.getenv("TIMEZONE", "Asia/Yerevan")

# =============================================================================
# Pricing Configuration
# =============================================================================
# Minimum order size in CNY
MIN_ORDER_CNY = int(os.getenv("MIN_ORDER_CNY", "5000"))

# Discount thresholds (USD equivalent)
DISCOUNT_THRESHOLD_USD = int(os.getenv("DISCOUNT_THRESHOLD_USD", "4000"))

# Discounts for FIAT payments (AMD/USD/RUB)
DISCOUNT_FIAT_HIGH = Decimal(os.getenv("DISCOUNT_FIAT_HIGH", "-0.010"))  # -1.0% for >= 4000 USD
DISCOUNT_FIAT_LOW = Decimal(os.getenv("DISCOUNT_FIAT_LOW", "-0.015"))   # -1.5% for < 4000 USD

# Discounts for USDT payments
DISCOUNT_USDT_HIGH = Decimal(os.getenv("DISCOUNT_USDT_HIGH", "-0.005"))  # -0.5% for >= 4000 USD
DISCOUNT_USDT_LOW = Decimal(os.getenv("DISCOUNT_USDT_LOW", "-0.010"))    # -1.0% for < 4000 USD

# =============================================================================
# HTX P2P Configuration
# =============================================================================
HTX_P2P_TTL_SECONDS = int(os.getenv("HTX_P2P_TTL_SECONDS", "45"))  # 30-60s recommended
HTX_PREFERRED_METHODS = os.getenv("HTX_PREFERRED_METHODS", "alipay,wechat").lower().split(",")

# =============================================================================
# CBA (Central Bank of Armenia) Configuration
# =============================================================================
CBA_RATES_TTL_SECONDS = int(os.getenv("CBA_RATES_TTL_SECONDS", "900"))  # 15 minutes

# =============================================================================
# Legacy Margins (kept for backward compatibility with /rates command)
# =============================================================================
MARGIN_USD_USDT = Decimal(os.getenv("MARGIN_USD_USDT", "-0.025"))
MARGIN_AMD_RUB = Decimal(os.getenv("MARGIN_AMD_RUB", "0.024"))

# =============================================================================
# Network Configuration
# =============================================================================
RATE_TTL_SECONDS = int(os.getenv("RATE_TTL_SECONDS", "600"))
HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "8"))
HTTP_RETRIES = int(os.getenv("HTTP_RETRIES", "3"))

# =============================================================================
# Database
# =============================================================================
DATABASE_PATH = os.getenv("DATABASE_PATH", "/opt/highbitbot/data/highbit.db")

# =============================================================================
# Logic
# =============================================================================
USDT_PARITY_WITH_USD = os.getenv("USDT_PARITY_WITH_USD", "true").lower() in ("1", "true", "yes", "y")
