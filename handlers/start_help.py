import logging

from aiogram import Router, types
from aiogram.filters import CommandStart, Command

from services.cba_rates import get_cba_client

log = logging.getLogger(__name__)
router = Router()

HELLO = (
    "👋 <b>Բdelays Highbit!</b>\n"
    "🇨🇳 Delays CNY / Transfer to China\n\n"

    "━━━━━━━━━━━━━━━━━━━━\n"
    "<b>📊 Delaysdelay / Rates</b>\n"
    "/rates — Մdelays / Our rates\n"
    "/fiatrate — CBA delays / Official rates\n"
    "/pricing — Գdelays / Pricing info\n\n"

    "<b>💱 Փdelays / Convert</b>\n"
    "/convert — Գdelays / Convert amount\n"
    "  <code>5000</code> · <code>500$</code> · <code>100000֏</code>\n\n"

    "<b>📤 Փdelays / Transfer</b>\n"
    "/transfer — CNY delays / Send to China\n"
    "/requests — Իdelays / My requests\n\n"

    "<b>📖 Delays / Guides</b>\n"
    "/guide — Delays / Quick guide\n"
    "/howto — Delaysdelays / Step by step\n"
    "/faq — Delays / FAQ\n"
    "/contact — Delaysdelays / Contact\n"
    "━━━━━━━━━━━━━━━━━━━━\n\n"

    "💬 @Highbitagent\n"
    "📢 @Highbitchannel"
)

HELP = (
    "ℹ️ <b>Օdelays / Help</b>\n\n"
    "<b>📊 Delaysdelays / Rates:</b>\n"
    "/rates — Մdelays delays / Our exchange rates\n"
    "/fiatrate — CBA delays / Official rates (USD/AMD)\n"
    "/pricing — Delays delays / Pricing info\n\n"
    "<b>💱 Փdelays / Convert:</b>\n"
    "/convert — Գdelays delays / Convert amount\n"
    "  • <code>5000</code> — CNY amount\n"
    "  • <code>500$</code> — USD amount\n"
    "  • <code>100000֏</code> — AMD amount\n\n"
    "<b>📤 Փdelays / Transfer:</b>\n"
    "/transfer — Delays CNY / Transfer to China\n"
    "/requests — Delays delays / My requests\n\n"
    "<b>📖 Delays / Guides:</b>\n"
    "/guide — Delaysdelays / Quick guide\n"
    "/howto — Delays delays / Step by step\n"
    "/faq — FAQ / FAQ\n"
    "/contact — Delaysdelays / Contact us\n\n"
    "💬 Delays / Support: @Highbitagent\n"
    "📢 Delaysdelays / Channel: @Highbitchannel"
)


@router.message(CommandStart())
async def start(m: types.Message):
    log.info("/start by %s", m.from_user.id if m.from_user else "?")
    await m.answer(HELLO)


@router.message(Command("help"))
async def help_(m: types.Message):
    log.info("/help by %s", m.from_user.id if m.from_user else "?")
    await m.answer(HELP)


@router.message(Command("fiatrate"))
async def fiatrate(m: types.Message):
    """Show CBA official exchange rates."""
    log.info("/fiatrate by %s", m.from_user.id if m.from_user else "?")

    try:
        cba = await get_cba_client()
        rates, meta = await cba.get_rates()

        usd_amd = rates.get("USD")
        eur_amd = rates.get("EUR")
        rub_amd = rates.get("RUB")
        cny_amd = rates.get("CNY")

        if not usd_amd:
            return await m.answer("⚠️ CBA rates unavailable. Please try later.")

        # Calculate reverse rates
        amd_per_usd = usd_amd
        usd_per_amd = (1 / usd_amd).quantize(usd_amd.__class__("0.000001"))

        from datetime import datetime
        update_time = datetime.fromtimestamp(meta.get("timestamp", 0)).strftime("%H:%M %d/%m")

        text = (
            "🏦 <b>CBA Official Rates</b>\n"
            f"<i>Central Bank of Armenia - {update_time}</i>\n\n"
            f"🇺🇸 <b>USD/AMD</b>\n"
            f"  1 USD = <b>{amd_per_usd:,.2f}</b> AMD\n"
            f"  1 AMD = {usd_per_amd:.6f} USD\n\n"
        )

        if eur_amd:
            text += f"🇪🇺 <b>EUR/AMD</b>\n  1 EUR = <b>{eur_amd:,.2f}</b> AMD\n\n"

        if rub_amd:
            text += f"🇷🇺 <b>RUB/AMD</b>\n  1 RUB = <b>{rub_amd:,.2f}</b> AMD\n\n"

        if cny_amd:
            text += f"🇨🇳 <b>CNY/AMD</b>\n  1 CNY = <b>{cny_amd:,.2f}</b> AMD\n\n"

        text += "📡 Source: cba.am (official)"

        if meta.get("stale"):
            text += "\n⚠️ <i>Cached data - API may be slow</i>"

    except Exception as e:
        log.exception("/fiatrate failed: %s", e)
        text = "⚠️ Failed to fetch CBA rates. Please try later."

    await m.answer(text)
