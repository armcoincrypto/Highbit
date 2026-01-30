"""
Central Bank of Armenia (CBA) official exchange rates fetcher.
Uses CBA public API for official AMD-based rates.
"""
import asyncio
import logging
import time
import xml.etree.ElementTree as ET
from decimal import Decimal
from typing import Optional, Tuple, Dict

import aiohttp

from config import CBA_RATES_TTL_SECONDS, HTTP_TIMEOUT

log = logging.getLogger(__name__)

# CBA API endpoints
CBA_SOAP_URL = "https://api.cba.am/exchangerates.asmx"
CBA_REST_URL = "https://api.cba.am/ExchangeRatesToday"

# Alternative: CBA website XML feed
CBA_XML_URL = "https://api.cba.am/ExchangeRatesLatest.xml"


class CBAClient:
    """
    Singleton client for CBA official exchange rates.
    All rates are AMD-based (how many AMD for 1 unit of foreign currency).
    """
    _instance: Optional["CBAClient"] = None
    _lock = asyncio.Lock()

    def __init__(self):
        self._cache: Optional[Tuple[float, Dict[str, Decimal], dict]] = None
        self._cache_lock = asyncio.Lock()
        self._session: Optional[aiohttp.ClientSession] = None
        self._last_good_rates: Optional[Dict[str, Decimal]] = None

    @classmethod
    async def get_instance(cls) -> "CBAClient":
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
        return (time.time() - ts) < CBA_RATES_TTL_SECONDS

    async def _fetch_cba_xml(self) -> Optional[Dict[str, Decimal]]:
        """Fetch rates from CBA XML feed."""
        session = await self._get_session()

        try:
            async with session.get(CBA_XML_URL) as r:
                if r.status != 200:
                    log.warning("CBA XML API returned %d", r.status)
                    return None

                text = await r.text()
                root = ET.fromstring(text)

                rates = {}
                # Parse XML structure
                for currency in root.findall(".//Currency"):
                    iso = currency.find("ISO")
                    rate = currency.find("Rate")
                    amount = currency.find("Amount")

                    if iso is not None and rate is not None:
                        iso_code = iso.text.strip()
                        rate_val = Decimal(rate.text.strip())
                        # Amount indicates how many units (e.g., 100 JPY)
                        amt = int(amount.text.strip()) if amount is not None and amount.text else 1

                        # Normalize to 1 unit
                        rates[iso_code] = rate_val / amt

                log.info("CBA rates fetched: %d currencies", len(rates))
                return rates

        except asyncio.TimeoutError:
            log.warning("CBA API timeout")
        except ET.ParseError as e:
            log.warning("CBA XML parse error: %s", e)
        except aiohttp.ClientError as e:
            log.warning("CBA API client error: %s", e)
        except Exception as e:
            log.exception("CBA API unexpected error: %s", e)

        return None

    async def _fetch_cba_soap(self) -> Optional[Dict[str, Decimal]]:
        """Fallback: fetch from CBA SOAP API."""
        session = await self._get_session()

        soap_request = """<?xml version="1.0" encoding="utf-8"?>
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Body>
                <ExchangeRatesLatest xmlns="http://www.cba.am/" />
            </soap:Body>
        </soap:Envelope>"""

        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": "http://www.cba.am/ExchangeRatesLatest"
        }

        try:
            async with session.post(CBA_SOAP_URL, data=soap_request, headers=headers) as r:
                if r.status != 200:
                    log.warning("CBA SOAP API returned %d", r.status)
                    return None

                text = await r.text()
                # Parse SOAP response (simplified)
                root = ET.fromstring(text)

                rates = {}
                ns = {"soap": "http://schemas.xmlsoap.org/soap/envelope/", "cba": "http://www.cba.am/"}

                for rate_elem in root.findall(".//cba:ExchangeRate", ns):
                    iso = rate_elem.find("cba:ISO", ns)
                    rate = rate_elem.find("cba:Rate", ns)
                    if iso is not None and rate is not None:
                        rates[iso.text] = Decimal(rate.text)

                if rates:
                    log.info("CBA SOAP rates fetched: %d currencies", len(rates))
                    return rates

        except Exception as e:
            log.warning("CBA SOAP fallback error: %s", e)

        return None

    async def get_rates(self) -> Tuple[Dict[str, Decimal], dict]:
        """
        Get CBA official rates (AMD-based).
        Returns (rates_dict, metadata).

        rates_dict format: {"USD": Decimal("386.50"), "CNY": Decimal("53.20"), ...}
        Meaning: 1 USD = 386.50 AMD, 1 CNY = 53.20 AMD, etc.
        """
        async with self._cache_lock:
            if self._is_fresh():
                _, rates, metadata = self._cache
                return rates, metadata

            # Try XML feed first
            rates = await self._fetch_cba_xml()

            if rates is None:
                # Try SOAP fallback
                rates = await self._fetch_cba_soap()

            if rates is None:
                # Use last known good rates
                if self._last_good_rates:
                    log.warning("Using last known good CBA rates")
                    return self._last_good_rates, {
                        "source": "cba_cache_fallback",
                        "timestamp": time.time(),
                        "stale": True
                    }
                raise RuntimeError("CBA rates unavailable and no fallback")

            # Update cache
            metadata = {
                "source": "cba_official",
                "timestamp": time.time(),
                "stale": False
            }
            self._cache = (time.time(), rates, metadata)
            self._last_good_rates = rates.copy()

            return rates, metadata

    async def get_cross_rate(self, from_currency: str, to_currency: str) -> Decimal:
        """
        Get cross rate between two currencies using AMD as base.
        Example: get_cross_rate("CNY", "USD") returns how many USD per 1 CNY.
        """
        rates, _ = await self.get_rates()

        if from_currency == "AMD":
            # 1 AMD to X = 1 / (X per AMD)
            return Decimal(1) / rates[to_currency]
        elif to_currency == "AMD":
            # X to 1 AMD = X per AMD
            return rates[from_currency]
        else:
            # Cross rate: from_AMD / to_AMD
            # Example: CNY_to_USD = (1 CNY in AMD) / (1 USD in AMD)
            from_amd = rates.get(from_currency)
            to_amd = rates.get(to_currency)

            if from_amd is None:
                raise ValueError(f"Currency {from_currency} not found in CBA rates")
            if to_amd is None:
                raise ValueError(f"Currency {to_currency} not found in CBA rates")

            return from_amd / to_amd

    async def cny_to_usd(self, cny_amount: Decimal) -> Decimal:
        """Convert CNY to USD using official CBA rates."""
        rate = await self.get_cross_rate("CNY", "USD")
        return cny_amount * rate

    async def usd_to_amd(self, usd_amount: Decimal) -> Decimal:
        """Convert USD to AMD."""
        rates, _ = await self.get_rates()
        return usd_amount * rates["USD"]

    async def usd_to_rub(self, usd_amount: Decimal) -> Decimal:
        """Convert USD to RUB."""
        rate = await self.get_cross_rate("USD", "RUB")
        return usd_amount * rate

    def clear_cache(self):
        self._cache = None


async def get_cba_client() -> CBAClient:
    """Get singleton CBA client."""
    return await CBAClient.get_instance()
