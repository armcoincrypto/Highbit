import asyncio
from decimal import Decimal
from services.rates import RateClient
from services.convert import display_snapshot, convert_from_cny, convert_usd_to_cny

async def main():
    rc = RateClient()
    fiat = await rc.get_fiat()
    usdt_cny = await rc.get_usdt_cny()
    snap = display_snapshot(fiat, usdt_cny)
    print("SNAP:", snap)
    out = convert_from_cny(Decimal(3000), fiat, usdt_cny)
    print("CNY 3000 ->", out)
    cny = convert_usd_to_cny(Decimal(300), fiat)
    print("USD 300 -> CNY", cny)

asyncio.run(main())
