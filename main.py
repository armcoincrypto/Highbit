import asyncio
from pathlib import Path
import logging
from dotenv import load_dotenv

# Load .env BEFORE importing config
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from aiogram.client.default import DefaultBotProperties
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone

from config import BOT_TOKEN, CHANNEL_ID, TIMEZONE
from handlers import rates as h_rates, convert as h_convert, inline as h_inline, start_help as h_starthelp, fallback_numeric as h_fallback, admin as h_admin, start_help as h_starthelp, fallback_numeric as h_fallback, start_help as h_starthelp, fallback_numeric as h_fallback
from middlewares.antiflood import AntiFloodMiddleware
from services.rates import RateClient
from services.convert import display_snapshot

# Basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("highbitbot")

async def on_startup(bot: Bot):
    log.info("on_startup(): deleting webhook & setting commands")
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands([
        BotCommand(command="start", description="Start / Help"),
        BotCommand(command="help", description="How to use"),
        BotCommand(command="rates", description="Daily rates"),
        BotCommand(command="convert", description="Convert amount"),
    ])

async def scheduler_task(bot: Bot):
    rc = RateClient()
    try:
        log.info("scheduler: fetching rates & posting to channel")
        fiat = await rc.get_fiat()
        usdt_cny = await rc.get_usdt_cny()
        snap = display_snapshot(fiat, usdt_cny)
        text = (
            "📊 Exchange Rates of the Day\n"
            f"🔹 USD → CNY: {snap['USD→CNY']}\n"
            f"🔹 CNY → AMD: {snap['CNY→AMD']}\n"
            f"🔹 CNY → RUB: {snap['CNY→RUB']}\n"
            f"🔹 USDT → CNY: {snap['USDT→CNY']}\n\n"
            "📢 Channel: https://t.me/Highbitchannel\n"
            "Use our bot for any amount: @HighbitChinabot"
        )
        if CHANNEL_ID:
            await bot.send_message(chat_id=CHANNEL_ID, text=text)
    except Exception as e:
        log.exception("scheduler failed: %s", e)

async def main():
    log.info("Booting bot…")
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Middlewares
    dp.message.middleware(AntiFloodMiddleware(0.8))
    dp.inline_query.middleware(AntiFloodMiddleware(0.8))

    # Routers
    dp.include_routers(h_starthelp.router, h_admin.router, h_rates.router, h_convert.router, h_inline.router, h_fallback.router)

    # Startup tasks
    await on_startup(bot)

    # Schedule daily post at 10:00 local time
    sched = AsyncIOScheduler(timezone=timezone(TIMEZONE))
    sched.add_job(scheduler_task, "cron", hour=10, minute=0, args=(bot,))
    sched.start()

    log.info("Polling started")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())
