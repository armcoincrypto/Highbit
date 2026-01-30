import asyncio
import logging
import random
import time
from typing import Dict, Optional, Tuple
from decimal import Decimal

import aiohttp

from config import RATE_TTL_SECONDS, HTTP_TIMEOUT, HTTP_RETRIES

log = logging.getLogger(__name__)

# Primary API (free, no key required)
ER_API = "https://open.er-api.com/v6/latest/CNY"
# Backup API (free tier of exchangerate-api)
ER_API_BACKUP = "https://v6.exchangerate-api.com/v6/open/latest/CNY"
# USDT price from CoinGecko
COINGECKO_USDT = "https://api.coingecko.com/api/v3/simple/price?ids=tether&vs_currencies=cny"


class RateClient:
    """
    Singleton rate client with caching and session reuse.
    Use get_instance() to get the shared instance.
    """
    _instance: Optional["RateClient"] = None
    _lock = asyncio.Lock()

    def __init__(self):
        self._fiat_cache: Optional[Tuple[float, Dict[str, Decimal]]] = None
        self._usdt_cny_cache: Optional[Tuple[float, Decimal]] = None
        self._cache_lock = asyncio.Lock()
        self._session: Optional[aiohttp.ClientSession] = None

    @classmethod
    async def get_instance(cls) -> "RateClient":
        """Get or create the singleton instance."""
        async with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create a reusable aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        """Close the session. Call on shutdown."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def _fetch_json(self, url: str) -> dict:
        """Fetch JSON with retries and exponential backoff."""
        session = await self._get_session()
        last_exc = None

        for attempt in range(1, HTTP_RETRIES + 1):
            try:
                async with session.get(url) as r:
                    if r.status == 429:
                        wait = min(2 ** attempt, 8) + random.uniform(0, 0.5)
                        log.warning("Rate limited (429), backing off %.1fs", wait)
                        await asyncio.sleep(wait)
                        continue
                    if r.status >= 500:
                        wait = min(1.5 * attempt, 4) + random.uniform(0, 0.4)
                        log.warning("Server error %d, retrying in %.1fs", r.status, wait)
                        await asyncio.sleep(wait)
                        continue
                    r.raise_for_status()
                    return await r.json()
            except asyncio.TimeoutError as e:
                last_exc = e
                log.warning("Timeout on attempt %d/%d for %s", attempt, HTTP_RETRIES, url)
            except aiohttp.ClientError as e:
                last_exc = e
                log.warning("Client error on attempt %d/%d: %s", attempt, HTTP_RETRIES, e)

            if attempt < HTTP_RETRIES:
                wait = min(1.5 * attempt, 4) + random.uniform(0, 0.4)
                await asyncio.sleep(wait)

        raise last_exc or RuntimeError(f"Failed to fetch {url}")

    def _is_fresh(self, cached: Optional[Tuple[float, object]]) -> bool:
        """Check if cache entry is still valid."""
        if not cached:
            return False
        ts, _ = cached
        return (time.time() - ts) < RATE_TTL_SECONDS

    async def get_fiat(self) -> Dict[str, Decimal]:
        """Get fiat rates (CNY base) with caching."""
        async with self._cache_lock:
            if self._is_fresh(self._fiat_cache):
                return self._fiat_cache[1]

            # Try primary API
            try:
                j = await self._fetch_json(ER_API)
                rates = j.get("rates", {})
            except Exception as e:
                log.warning("Primary API failed: %s, trying backup", e)
                try:
                    j = await self._fetch_json(ER_API_BACKUP)
                    rates = j.get("conversion_rates", j.get("rates", {}))
                except Exception as e2:
                    log.error("Backup API also failed: %s", e2)
                    raise RuntimeError("All rate APIs unavailable") from e2

            wanted: Dict[str, Decimal] = {}
            for key in ("USD", "AMD", "RUB"):
                v = rates.get(key)
                if v is not None:
                    wanted[key] = Decimal(str(v))

            if not wanted:
                raise RuntimeError("No fiat rates found in API response")

            self._fiat_cache = (time.time(), wanted)
            log.info("Fetched fiat rates: %s", wanted)
            return wanted

    async def get_usdt_cny(self) -> Decimal:
        """Get USDT/CNY rate with caching."""
        async with self._cache_lock:
            if self._is_fresh(self._usdt_cny_cache):
                return self._usdt_cny_cache[1]

            j = await self._fetch_json(COINGECKO_USDT)
            v = j.get("tether", {}).get("cny")
            if v is None:
                raise RuntimeError("USDT/CNY unavailable from CoinGecko")

            val = Decimal(str(v))
            self._usdt_cny_cache = (time.time(), val)
            log.info("Fetched USDT/CNY: %s", val)
            return val

    def clear_cache(self):
        """Clear all cached rates (for testing/admin)."""
        self._fiat_cache = None
        self._usdt_cny_cache = None


async def get_rate_client() -> RateClient:
    """Get the singleton RateClient instance."""
    return await RateClient.get_instance()
