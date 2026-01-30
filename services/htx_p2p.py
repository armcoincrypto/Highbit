"""
HTX (Huobi) P2P USDT/CNY rate fetcher.
Primary: P2P.Army API (normalized P2P data)
Fallback: Direct HTX/Binance P2P APIs
"""
import asyncio
import logging
import random
import time
from decimal import Decimal
from typing import Optional, Tuple, List

import aiohttp

from config import (
    HTX_P2P_TTL_SECONDS,
    HTX_PREFERRED_METHODS,
    HTTP_TIMEOUT,
    HTTP_RETRIES,
    P2P_ARMY_API_KEY,
)

log = logging.getLogger(__name__)

# P2P.Army API (preferred - normalized data)
P2P_ARMY_API = "https://p2p.army/api/v1/ads"

# Direct P2P APIs (fallback)
HTX_P2P_API = "https://www.htx.com/-/x/otc/v1/data/trade-market"
BINANCE_P2P_API = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"


class HTXP2PClient:
    """
    Singleton client for HTX P2P USDT/CNY rates.
    Fetches highest sell price (CNY per 1 USDT).
    """
    _instance: Optional["HTXP2PClient"] = None
    _lock = asyncio.Lock()

    def __init__(self):
        self._cache: Optional[Tuple[float, Decimal, dict]] = None
        self._cache_lock = asyncio.Lock()
        self._session: Optional[aiohttp.ClientSession] = None
        self._last_good_price: Optional[Decimal] = None
        self._last_good_metadata: Optional[dict] = None

    @classmethod
    async def get_instance(cls) -> "HTXP2PClient":
        async with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    def _is_fresh(self) -> bool:
        if not self._cache:
            return False
        ts, _, _ = self._cache
        return (time.time() - ts) < HTX_P2P_TTL_SECONDS

    async def _fetch_with_retry(self, coro_factory, description: str):
        """Execute with retry and exponential backoff."""
        last_exc = None
        for attempt in range(1, HTTP_RETRIES + 1):
            try:
                return await coro_factory()
            except asyncio.TimeoutError as e:
                last_exc = e
                log.warning("%s timeout (attempt %d/%d)", description, attempt, HTTP_RETRIES)
            except aiohttp.ClientError as e:
                last_exc = e
                log.warning("%s client error (attempt %d/%d): %s", description, attempt, HTTP_RETRIES, e)

            if attempt < HTTP_RETRIES:
                wait = min(1.5 ** attempt, 4) + random.uniform(0, 0.5)
                await asyncio.sleep(wait)

        raise last_exc or RuntimeError(f"{description} failed after {HTTP_RETRIES} attempts")

    async def _fetch_p2p_army(self) -> Tuple[Optional[Decimal], List[dict], str]:
        """
        Fetch from P2P.Army API (preferred source).
        Returns (price, ads_list, source_name).
        """
        if not P2P_ARMY_API_KEY:
            log.debug("P2P_ARMY_API_KEY not configured, skipping P2P.Army")
            return None, [], ""

        session = await self._get_session()

        params = {
            "market": "huobi",  # HTX/Huobi
            "fiat": "CNY",
            "crypto": "USDT",
            "side": "sell",  # Sellers selling USDT (we buy)
            "limit": 20,
        }
        headers = {
            "Authorization": f"Bearer {P2P_ARMY_API_KEY}",
            "Accept": "application/json",
        }

        try:
            async def fetch():
                async with session.get(P2P_ARMY_API, params=params, headers=headers) as r:
                    if r.status == 401:
                        log.error("P2P.Army API: Invalid API key")
                        return None, [], ""
                    if r.status == 429:
                        log.warning("P2P.Army API: Rate limited")
                        return None, [], ""
                    if r.status != 200:
                        log.warning("P2P.Army API returned %d", r.status)
                        return None, [], ""

                    data = await r.json()
                    ads = data.get("data", data.get("ads", []))

                    if not ads:
                        log.warning("P2P.Army returned no ads")
                        return None, [], ""

                    # Extract prices
                    prices = []
                    for ad in ads:
                        try:
                            price = Decimal(str(ad.get("price", 0)))
                            if price <= 0:
                                continue

                            methods = ad.get("payment_methods", ad.get("payMethods", []))
                            if isinstance(methods, list):
                                methods = [str(m).lower() for m in methods]
                            else:
                                methods = []

                            has_preferred = any(
                                pref in method
                                for method in methods
                                for pref in HTX_PREFERRED_METHODS
                            )

                            prices.append({
                                "price": price,
                                "methods": methods,
                                "preferred": has_preferred,
                                "merchant": ad.get("merchant", ad.get("userName", "unknown")),
                            })
                        except (ValueError, TypeError) as e:
                            log.debug("Skip invalid ad: %s", e)

                    if not prices:
                        return None, [], ""

                    # Sort by price descending (highest first)
                    prices.sort(key=lambda x: x["price"], reverse=True)

                    # Use 3rd position (index 2) for competitive rate
                    # Fall back to last available if fewer than 3 ads
                    position = min(2, len(prices) - 1)
                    selected = prices[position]

                    log.info("P2P.Army HTX price: %.2f CNY/USDT (position %d, merchant: %s)",
                             selected["price"], position + 1, selected["merchant"])

                    return selected["price"], prices[:5], "p2p_army_htx"

            return await self._fetch_with_retry(fetch, "P2P.Army")

        except Exception as e:
            log.warning("P2P.Army fetch failed: %s", e)
            return None, [], ""

    async def _fetch_htx_direct(self) -> Tuple[Optional[Decimal], List[dict], str]:
        """Fetch directly from HTX P2P API (fallback)."""
        session = await self._get_session()

        payload = {
            "coinId": 2,  # USDT
            "currency": 1,  # CNY
            "tradeType": "sell",
            "currPage": 1,
            "payMethod": 0,
            "acceptOrder": 0,
            "country": "",
            "blockType": "general",
            "online": 1,
            "range": 0,
            "amount": ""
        }

        try:
            async def fetch():
                async with session.post(HTX_P2P_API, json=payload) as r:
                    if r.status != 200:
                        log.warning("HTX P2P API returned %d", r.status)
                        return None, [], ""

                    data = await r.json()
                    if data.get("code") != 200:
                        log.warning("HTX P2P API error: %s", data.get("message"))
                        return None, [], ""

                    ads = data.get("data", [])
                    if not ads:
                        return None, [], ""

                    prices = []
                    for ad in ads:
                        try:
                            price = Decimal(str(ad.get("price", 0)))
                            methods = [m.get("name", "").lower() for m in ad.get("payMethods", [])]
                            has_preferred = any(
                                pref in method
                                for method in methods
                                for pref in HTX_PREFERRED_METHODS
                            )
                            prices.append({
                                "price": price,
                                "methods": methods,
                                "preferred": has_preferred,
                                "merchant": ad.get("userName", "unknown")
                            })
                        except (ValueError, TypeError):
                            continue

                    if not prices:
                        return None, [], ""

                    # Sort by price descending
                    prices.sort(key=lambda x: x["price"], reverse=True)

                    # Use 3rd position for competitive rate
                    position = min(2, len(prices) - 1)
                    selected = prices[position]

                    log.info("HTX Direct price: %.2f CNY/USDT (position %d)",
                             selected["price"], position + 1)
                    return selected["price"], prices[:5], "htx_direct"

            return await self._fetch_with_retry(fetch, "HTX Direct")

        except Exception as e:
            log.warning("HTX Direct fetch failed: %s", e)
            return None, [], ""

    async def _fetch_binance_fallback(self) -> Tuple[Optional[Decimal], str]:
        """Final fallback to Binance P2P."""
        session = await self._get_session()

        payload = {
            "fiat": "CNY",
            "page": 1,
            "rows": 10,
            "tradeType": "BUY",
            "asset": "USDT",
            "countries": [],
            "proMerchantAds": False,
            "publisherType": None,
            "payTypes": []
        }

        try:
            async def fetch():
                headers = {"Content-Type": "application/json"}
                async with session.post(BINANCE_P2P_API, json=payload, headers=headers) as r:
                    if r.status != 200:
                        return None, ""

                    data = await r.json()
                    ads = data.get("data", [])
                    if not ads:
                        return None, ""

                    prices = []
                    for ad in ads:
                        try:
                            price = Decimal(ad["adv"]["price"])
                            prices.append(price)
                        except (KeyError, ValueError, TypeError):
                            continue

                    if prices:
                        highest = max(prices)
                        log.info("Binance fallback price: %.2f CNY/USDT", highest)
                        return highest, "binance_fallback"

                    return None, ""

            return await self._fetch_with_retry(fetch, "Binance Fallback")

        except Exception as e:
            log.warning("Binance fallback failed: %s", e)
            return None, ""

    async def get_usdt_cny_price(self) -> Tuple[Decimal, dict]:
        """
        Get USDT/CNY price (highest from P2P).
        Returns (price, metadata).

        Priority:
        1. P2P.Army API (if API key configured)
        2. HTX Direct P2P API
        3. Binance P2P (final fallback)
        4. Last cached value (emergency)
        """
        async with self._cache_lock:
            if self._is_fresh():
                _, price, metadata = self._cache
                return price, metadata

            price = None
            ads = []
            source = ""

            # 1. Try P2P.Army (preferred)
            if P2P_ARMY_API_KEY:
                price, ads, source = await self._fetch_p2p_army()

            # 2. Try HTX Direct
            if price is None:
                price, ads, source = await self._fetch_htx_direct()

            # 3. Try Binance fallback
            if price is None:
                price, source = await self._fetch_binance_fallback()
                ads = []

            # 4. Use last known good price
            if price is None:
                if self._last_good_price:
                    log.warning("All P2P sources failed, using cached price: %s", self._last_good_price)
                    return self._last_good_price, {
                        **(self._last_good_metadata or {}),
                        "stale": True,
                        "cache_reason": "all_sources_failed",
                    }
                raise RuntimeError("P2P price unavailable: all sources failed and no cache")

            # Update cache
            metadata = {
                "source": source,
                "timestamp": time.time(),
                "stale": False,
                "top_ads": ads[:3] if ads else [],
            }
            self._cache = (time.time(), price, metadata)
            self._last_good_price = price
            self._last_good_metadata = metadata

            return price, metadata

    def clear_cache(self):
        """Clear cached price."""
        self._cache = None


async def get_htx_p2p_client() -> HTXP2PClient:
    """Get singleton HTX P2P client."""
    return await HTXP2PClient.get_instance()
