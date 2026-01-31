"""
Dynamic settings service for discount management.
Stores discount percentages in database with in-memory caching.
"""
import asyncio
import logging
from decimal import Decimal
from typing import Optional, Dict

from models.database import get_database
from config import (
    DISCOUNT_FIAT_LOW,
    DISCOUNT_FIAT_HIGH,
    DISCOUNT_USDT_LOW,
    DISCOUNT_USDT_HIGH,
)

log = logging.getLogger(__name__)

# Setting keys for discounts
DISCOUNT_KEYS = {
    "usd_low": "discount_usd_low",      # USD < $4000
    "usd_high": "discount_usd_high",    # USD >= $4000
    "amd_low": "discount_amd_low",      # AMD < 1.5M
    "amd_high": "discount_amd_high",    # AMD >= 1.5M
    "usdt_low": "discount_usdt_low",    # USDT < $4000
    "usdt_high": "discount_usdt_high",  # USDT >= $4000
}

# Default values from config (fallback if not in DB)
DEFAULT_DISCOUNTS = {
    "usd_low": DISCOUNT_FIAT_LOW,       # -1.0%
    "usd_high": DISCOUNT_FIAT_HIGH,     # -0.7%
    "amd_low": DISCOUNT_FIAT_LOW,       # -1.0% (same as USD)
    "amd_high": DISCOUNT_FIAT_HIGH,     # -0.7% (same as USD)
    "usdt_low": DISCOUNT_USDT_LOW,      # -1.3%
    "usdt_high": DISCOUNT_USDT_HIGH,    # -0.9%
}


class SettingsService:
    """
    Service for managing dynamic settings.
    Uses in-memory cache with database persistence.
    """
    _instance: Optional["SettingsService"] = None
    _lock = asyncio.Lock()

    def __init__(self):
        self._cache: Dict[str, Decimal] = {}
        self._loaded = False

    @classmethod
    async def get_instance(cls) -> "SettingsService":
        async with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    async def _load_from_db(self):
        """Load all discount settings from database."""
        db = await get_database()
        settings = db.get_all_settings()

        for short_key, db_key in DISCOUNT_KEYS.items():
            if db_key in settings:
                try:
                    self._cache[short_key] = Decimal(settings[db_key])
                except Exception as e:
                    log.warning("Invalid discount value for %s: %s", db_key, e)
                    self._cache[short_key] = DEFAULT_DISCOUNTS[short_key]
            else:
                self._cache[short_key] = DEFAULT_DISCOUNTS[short_key]

        self._loaded = True
        log.info("Loaded discounts from DB: %s", self._cache)

    async def get_discount(self, key: str) -> Decimal:
        """
        Get discount value by key.
        Keys: usd_low, usd_high, amd_low, amd_high, usdt_low, usdt_high
        """
        if not self._loaded:
            await self._load_from_db()

        return self._cache.get(key, DEFAULT_DISCOUNTS.get(key, Decimal("0")))

    async def get_all_discounts(self) -> Dict[str, Decimal]:
        """Get all discount values."""
        if not self._loaded:
            await self._load_from_db()
        return dict(self._cache)

    async def set_discount(self, key: str, value: Decimal, admin_id: int) -> bool:
        """
        Set a discount value.
        Returns True if successful.
        """
        if key not in DISCOUNT_KEYS:
            return False

        db_key = DISCOUNT_KEYS[key]
        db = await get_database()
        db.set_setting(db_key, str(value), admin_id)

        # Update cache
        self._cache[key] = value
        log.info("Discount %s set to %s by admin %d", key, value, admin_id)
        return True

    def clear_cache(self):
        """Clear the settings cache to force reload."""
        self._cache.clear()
        self._loaded = False


async def get_settings_service() -> SettingsService:
    """Get singleton settings service."""
    return await SettingsService.get_instance()


# Convenience functions for common operations
async def get_fiat_discounts() -> tuple[Decimal, Decimal]:
    """Get USD/AMD discounts (low, high)."""
    svc = await get_settings_service()
    return await svc.get_discount("usd_low"), await svc.get_discount("usd_high")


async def get_usdt_discounts() -> tuple[Decimal, Decimal]:
    """Get USDT discounts (low, high)."""
    svc = await get_settings_service()
    return await svc.get_discount("usdt_low"), await svc.get_discount("usdt_high")
