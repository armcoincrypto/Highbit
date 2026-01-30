import asyncio
import logging
import signal
from pathlib import Path

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
from handlers import (
    rates as h_rates,
    convert as h_convert,
    inline as h_inline,
    start_help as h_starthelp,
    fallback_numeric as h_fallback,
    admin as h_admin,
)
from middlewares.antiflood import AntiFloodMiddleware
from services.rates import get_rate_client
from utils.messages import format_daily_rates

# Structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
log = logging.getLogger("highbitbot")


async def on_startup(bot: Bot):
    """Initialize bot on startup."""
    log.info("on_startup(): deleting webhook & setting commands")
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands([
        BotCommand(command="start", description="Start / Help"),
        BotCommand(command="help", description="How to use"),
        BotCommand(command="rates", description="Daily rates"),
        BotCommand(command="convert", description="Convert amount"),
    ])


async def on_shutdown():
    """Cleanup on shutdown."""
    log.info("on_shutdown(): closing rate client session")
    rc = await get_rate_client()
    await rc.close()


async def scheduler_task(bot: Bot):
    """Daily scheduled task to post rates to channel."""
    try:
        log.info("scheduler: fetching rates & posting to channel")
        rc = await get_rate_client()
        fiat = await rc.get_fiat()
        usdt_cny = await rc.get_usdt_cny()
        text = format_daily_rates(fiat, usdt_cny)

        if CHANNEL_ID:
            await bot.send_message(chat_id=CHANNEL_ID, text=text)
            log.info("scheduler: posted to channel %s", CHANNEL_ID)
        else:
            log.warning("scheduler: CHANNEL_ID not configured, skipping post")
    except Exception as e:
        log.exception("scheduler failed: %s", e)


async def main():
    log.info("Booting bot...")

    if not BOT_TOKEN:
        log.error("BOT_TOKEN not set! Check your .env file.")
        return

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Shared antiflood middleware instance
    antiflood = AntiFloodMiddleware(0.8)
    dp.message.middleware(antiflood)
    dp.inline_query.middleware(antiflood)

    # Register routers (order matters: specific handlers before fallback)
    dp.include_routers(
        h_starthelp.router,
        h_admin.router,
        h_rates.router,
        h_convert.router,
        h_inline.router,
        h_fallback.router,  # Must be last (catch-all)
    )

    # Startup tasks
    await on_startup(bot)

    # Schedule daily post at 10:00 local time
    # Using job_id prevents duplicate jobs on restart
    sched = AsyncIOScheduler(timezone=timezone(TIMEZONE))
    sched.add_job(
        scheduler_task,
        "cron",
        hour=10,
        minute=0,
        args=(bot,),
        id="daily_rates_post",
        replace_existing=True,
        misfire_grace_time=3600,  # Allow 1 hour grace for missed jobs
    )
    sched.start()
    log.info("Scheduler started: daily post at 10:00 %s", TIMEZONE)

    # Handle graceful shutdown
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(
            sig,
            lambda s=sig: asyncio.create_task(shutdown(s, sched, bot))
        )

    log.info("Polling started")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await on_shutdown()


async def shutdown(sig, scheduler, bot):
    """Handle graceful shutdown on signals."""
    log.info("Received signal %s, shutting down...", sig.name)
    scheduler.shutdown(wait=False)
    await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
