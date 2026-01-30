"""
HTX (Huobi) P2P USDT/CNY rate fetcher.
Fetches the highest price from P2P ads for USDT/CNY.
"""
import asyncio
import logging
import time
from decimal import Decimal
from typing import Optional, Tuple, List

import aiohttp

from config import HTX_P2P_TTL_SECONDS, HTX_PREFERRED_METHODS, HTTP_TIMEOUT, HTTP_RETRIES

log = logging.getLogger(__name__)

# HTX P2P API endpoint
HTX_P2P_API = "https://www.htx.com/-/x/otc/v1/data/trade-market"

# Backup: Binance P2P (similar structure)
BINANCE_P2P_API = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"


class HTXP2PClient:
    """
    Singleton client for HTX P2P USDT/CNY rates.
    Fetches highest sell price (user buys USDT with CNY).
    """
    _instance: Optional["HTXP2PClient"] = None
    _lock = asyncio.Lock()

    def __init__(self):
        self._cache: Optional[Tuple[float, Decimal, dict]] = None  # (timestamp, price, metadata)
        self._cache_lock = asyncio.Lock()
        self._session: Optional[aiohttp.ClientSession] = None
        self._last_good_price: Optional[Decimal] = None

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

    async def _fetch_htx_p2p(self) -> Tuple[Optional[Decimal], List[dict]]:
        """Fetch from HTX P2P API."""
        session = await self._get_session()

        # HTX P2P request payload
        payload = {
            "coinId": 2,  # USDT
            "currency": 1,  # CNY
            "tradeType": "sell",  # We want to buy USDT (seller sells)
            "currPage": 1,
            "payMethod": 0,  # All methods
            "acceptOrder": 0,
            "country": "",
            "blockType": "general",
            "online": 1,
            "range": 0,
            "amount": ""
        }

        try:
            async with session.post(HTX_P2P_API, json=payload) as r:
                if r.status != 200:
                    log.warning("HTX P2P API returned %d", r.status)
                    return None, []

                data = await r.json()
                if data.get("code") != 200:
                    log.warning("HTX P2P API error: %s", data.get("message"))
                    return None, []

                ads = data.get("data", [])
                if not ads:
                    log.warning("No HTX P2P ads returned")
                    return None, []

                # Find highest price, preferring Alipay/WeChat
                prices = []
                for ad in ads:
                    price = Decimal(str(ad.get("price", 0)))
                    methods = [m.get("name", "").lower() for m in ad.get("payMethods", [])]

                    # Check if ad has preferred payment methods
                    has_preferred = any(
                        pref in method for method in methods for pref in HTX_PREFERRED_METHODS
                    )

                    prices.append({
                        "price": price,
                        "methods": methods,
                        "preferred": has_preferred,
                        "merchant": ad.get("userName", "unknown")
                    })

                if not prices:
                    return None, []

                # Sort: preferred methods first, then by price descending
                prices.sort(key=lambda x: (x["preferred"], x["price"]), reverse=True)

                highest = prices[0]
                log.info("HTX P2P highest price: %s CNY/USDT (merchant: %s, methods: %s)",
                         highest["price"], highest["merchant"], highest["methods"])

                return highest["price"], prices[:5]

        except asyncio.TimeoutError:
            log.warning("HTX P2P API timeout")
        except aiohttp.ClientError as e:
            log.warning("HTX P2P API client error: %s", e)
        except Exception as e:
            log.exception("HTX P2P API unexpected error: %s", e)

        return None, []

    async def _fetch_binance_p2p_fallback(self) -> Optional[Decimal]:
        """Fallback to Binance P2P if HTX fails."""
        session = await self._get_session()

        payload = {
            "fiat": "CNY",
            "page": 1,
            "rows": 10,
            "tradeType": "BUY",  # We buy USDT
            "asset": "USDT",
            "countries": [],
            "proMerchantAds": False,
            "publisherType": None,
            "payTypes": []
        }

        try:
            headers = {"Content-Type": "application/json"}
            async with session.post(BINANCE_P2P_API, json=payload, headers=headers) as r:
                if r.status != 200:
                    log.warning("Binance P2P fallback returned %d", r.status)
                    return None

                data = await r.json()
                ads = data.get("data", [])
                if not ads:
                    return None

                # Get highest price
                prices = [Decimal(ad["adv"]["price"]) for ad in ads if ad.get("adv", {}).get("price")]
                if prices:
                    highest = max(prices)
                    log.info("Binance P2P fallback price: %s CNY/USDT", highest)
                    return highest

        except Exception as e:
            log.warning("Binance P2P fallback error: %s", e)

        return None

    async def get_usdt_cny_price(self) -> Tuple[Decimal, dict]:
        """
        Get USDT/CNY price (highest from P2P).
        Returns (price, metadata).
        """
        async with self._cache_lock:
            if self._is_fresh():
                _, price, metadata = self._cache
                return price, metadata

            # Try HTX P2P first
            price, ads = await self._fetch_htx_p2p()

            if price is None:
                # Try Binance fallback
                price = await self._fetch_binance_p2p_fallback()

            if price is None:
                # Use last known good price
                if self._last_good_price:
                    log.warning("Using last known good P2P price: %s", self._last_good_price)
                    return self._last_good_price, {
                        "source": "cache_fallback",
                        "timestamp": time.time(),
                        "stale": True
                    }
                raise RuntimeError("P2P price unavailable and no fallback")

            # Update cache and last good price
            metadata = {
                "source": "htx_p2p" if ads else "binance_p2p",
                "timestamp": time.time(),
                "stale": False,
                "top_ads": ads[:3] if ads else []
            }
            self._cache = (time.time(), price, metadata)
            self._last_good_price = price

            return price, metadata

    def clear_cache(self):
        self._cache = None


async def get_htx_p2p_client() -> HTXP2PClient:
    """Get singleton HTX P2P client."""
    return await HTXP2PClient.get_instance()
