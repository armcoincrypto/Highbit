import logging

from aiogram import Router, types

from utils.parse import parse_amount
from services.rates import get_rate_client
from services.convert import convert_from_cny, convert_usd_to_cny

log = logging.getLogger(__name__)
router = Router()


@router.inline_query()
async def inline_handler(iq: types.InlineQuery):
    q = (iq.query or "").strip()
    log.info("inline query from %s: %r", iq.from_user.id if iq.from_user else "?", q)
    kind, amt = parse_amount(q) if q else (None, None)

    results = []

    if kind == "REJECT_USDT":
        results.append(types.InlineQueryResultArticle(
            id="rej",
            title="USDT input not supported",
            description="Use: 3000 (CNY) or $300 / 300$ (USD)",
            input_message_content=types.InputTextMessageContent(
                message_text="❌ USDT as input is not supported. Try 3000 (CNY) or $300 (USD)."
            ),
        ))
        return await iq.answer(results=results, cache_time=5, is_personal=True)

    try:
        rc = await get_rate_client()
        fiat = await rc.get_fiat()
        usdt_cny = await rc.get_usdt_cny()

        if kind == "CNY":
            out = convert_from_cny(amt, fiat, usdt_cny)
            title = f"{amt} CNY → USD/AMD/RUB/USDT"
            desc = f"USD {out['USD']} · AMD {out['AMD']} · RUB {out['RUB']} · USDT {out['USDT']}"
            results.append(types.InlineQueryResultArticle(
                id="cny",
                title=title,
                description=desc,
                input_message_content=types.InputTextMessageContent(
                    message_text=f"💱 {title}\n{desc}"
                ),
            ))
        elif kind == "USD":
            cny = convert_usd_to_cny(amt, fiat)
            title = f"${amt} USD → CNY"
            desc = f"CNY {cny}"
            results.append(types.InlineQueryResultArticle(
                id="usd",
                title=title,
                description=desc,
                input_message_content=types.InputTextMessageContent(
                    message_text=f"💱 {title}\n{desc}"
                ),
            ))
        else:
            results.append(types.InlineQueryResultArticle(
                id="hint",
                title="Type: 3000  or  $300  or  300$  or  300 USD",
                description="CNY→USD/AMD/RUB/USDT or USD→CNY",
                input_message_content=types.InputTextMessageContent(
                    message_text="Tip: 3000 (CNY) · $300 / 300$ (USD) · 300 USD"
                ),
            ))
    except Exception as e:
        log.exception("inline failed: %s", e)
        results.append(types.InlineQueryResultArticle(
            id="err",
            title="Service unavailable",
            description="Please try again shortly.",
            input_message_content=types.InputTextMessageContent(
                message_text="⚠️ Service temporarily unavailable. Please try again."
            ),
        ))

    await iq.answer(results=results, cache_time=5, is_personal=True)
