import asyncio
import random
import time
from typing import Dict, Optional, Tuple
from decimal import Decimal
import aiohttp

from config import RATE_TTL_SECONDS, HTTP_TIMEOUT, HTTP_RETRIES

ER_API = "https://open.er-api.com/v6/latest/CNY"                     # base=CNY
EXHOST = "https://api.exchangerate.host/latest?base=CNY"             # backup
COINGECKO_USDT = "https://api.coingecko.com/api/v3/simple/price?ids=tether&vs_currencies=cny"

class RateClient:
    def __init__(self):
        self._fiat_cache: Optional[Tuple[float, Dict[str, Decimal]]] = None
        self._usdt_cny_cache: Optional[Tuple[float, Decimal]] = None
        self._lock = asyncio.Lock()

    async def _fetch_json(self, session: aiohttp.ClientSession, url: str) -> dict:
        last_exc = None
        for attempt in range(1, HTTP_RETRIES + 1):
            try:
                async with session.get(url, timeout=HTTP_TIMEOUT) as r:
                    r.raise_for_status()
                    return await r.json()
            except Exception as e:
                last_exc = e
                await asyncio.sleep(min(1.5 * attempt, 4) + random.uniform(0, 0.4))
        raise last_exc

    def _fresh(self, cached: Optional[Tuple[float, object]]) -> bool:
        if not cached:
            return False
        ts, _ = cached
        return (time.time() - ts) < RATE_TTL_SECONDS

    async def get_fiat(self) -> Dict[str, Decimal]:
        async with self._lock:
            if self._fresh(self._fiat_cache):
                return self._fiat_cache[1]
            async with aiohttp.ClientSession() as s:
                try:
                    j = await self._fetch_json(s, ER_API)
                    rates = j.get("rates", {})
                except Exception:
                    j = await self._fetch_json(s, EXHOST)
                    rates = j.get("rates", {})
            wanted: Dict[str, Decimal] = {}
            for key in ("USD", "AMD", "RUB"):
                v = rates.get(key)
                if v is None:
                    continue
                wanted[key] = Decimal(str(v))
            if not wanted:
                raise RuntimeError("No fiat rates found")
            self._fiat_cache = (time.time(), wanted)
            return wanted

    async def get_usdt_cny(self) -> Decimal:
        async with self._lock:
            if self._fresh(self._usdt_cny_cache):
                return self._usdt_cny_cache[1]
            async with aiohttp.ClientSession() as s:
                j = await self._fetch_json(s, COINGECKO_USDT)
            v = j.get("tether", {}).get("cny")
            if v is None:
                raise RuntimeError("USDT/CNY unavailable")
            val = Decimal(str(v))
            self._usdt_cny_cache = (time.time(), val)
            return val
