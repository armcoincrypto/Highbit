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
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone

from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from config import BOT_TOKEN, CHANNEL_ID, TIMEZONE
from handlers import (
    rates as h_rates,
    convert as h_convert,
    inline as h_inline,
    start_help as h_starthelp,
    fallback_numeric as h_fallback,
    admin as h_admin,
)
from handlers import transfer as h_transfer
from handlers import admin_transfer as h_admin_transfer
from handlers import kb as h_kb
from middlewares.antiflood import AntiFloodMiddleware
from services.rates import get_rate_client
from services.htx_p2p import get_htx_p2p_client
from services.cba_rates import get_cba_client
from utils.messages import format_daily_rates_new
from models.database import get_database

# Flag to track if channel posting is available
_channel_post_enabled = True
_channel_post_error = ""


def get_channel_status() -> tuple[bool, str]:
    """Get current channel posting status. Used by admin commands."""
    return _channel_post_enabled, _channel_post_error

# Structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
log = logging.getLogger("highbitbot")


async def validate_channel_posting(bot: Bot) -> tuple[bool, str]:
    """
    Validate that the bot can post to the configured channel.
    Returns (success, error_message).
    """
    global _channel_post_enabled, _channel_post_error

    if not CHANNEL_ID:
        msg = "CHANNEL_ID not configured - daily posts disabled"
        log.warning(msg)
        _channel_post_enabled = False
        _channel_post_error = msg
        return False, msg

    try:
        # Try to get chat info to verify bot has access
        chat = await bot.get_chat(CHANNEL_ID)
        log.info("Channel validated: %s (ID: %s)", chat.title or chat.username, chat.id)

        # For channels, bot must be admin to post
        if chat.type == "channel":
            try:
                member = await bot.get_chat_member(chat.id, bot.id)
                if member.status not in ("administrator", "creator"):
                    msg = (
                        f"Bot is not admin in channel {chat.title or CHANNEL_ID}. "
                        "Add bot as admin with 'Post Messages' permission."
                    )
                    log.error(msg)
                    _channel_post_enabled = False
                    _channel_post_error = msg
                    return False, msg
            except Exception as e:
                log.warning("Could not verify admin status: %s (posting may still work)", e)

        _channel_post_enabled = True
        _channel_post_error = ""
        return True, ""

    except TelegramForbiddenError:
        msg = (
            f"Bot cannot access channel {CHANNEL_ID}. "
            "Either: 1) Bot is not a member, 2) Channel ID is wrong, or 3) Bot was kicked. "
            "Add bot to channel as admin with 'Post Messages' permission."
        )
        log.error(msg)
        _channel_post_enabled = False
        _channel_post_error = msg
        return False, msg

    except TelegramBadRequest as e:
        msg = f"Invalid CHANNEL_ID '{CHANNEL_ID}': {e}. Use format -100... for channels."
        log.error(msg)
        _channel_post_enabled = False
        _channel_post_error = msg
        return False, msg

    except Exception as e:
        msg = f"Channel validation error: {e}"
        log.error(msg)
        _channel_post_enabled = False
        _channel_post_error = msg
        return False, msg


async def on_startup(bot: Bot):
    """Initialize bot on startup."""
    log.info("on_startup(): initializing services")

    # Initialize database
    await get_database()
    log.info("Database initialized")

    # Delete webhook and set commands
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands([
        BotCommand(command="start", description="Start / Help"),
        BotCommand(command="help", description="How to use"),
        BotCommand(command="transfer", description="📤 Transfer to China (Buy CNY)"),
        BotCommand(command="rates", description="Daily rates"),
        BotCommand(command="convert", description="Convert amount"),
        BotCommand(command="my_requests", description="My transfer requests"),
    ])
    log.info("Bot commands set")

    # Validate channel posting (non-blocking - bot continues even if invalid)
    await validate_channel_posting(bot)


async def on_shutdown():
    """Cleanup on shutdown."""
    log.info("on_shutdown(): closing services")

    # Close rate clients
    try:
        rc = await get_rate_client()
        await rc.close()
    except Exception as e:
        log.warning("Failed to close rate client: %s", e)

    try:
        htx = await get_htx_p2p_client()
        await htx.close()
    except Exception as e:
        log.warning("Failed to close HTX client: %s", e)

    try:
        cba = await get_cba_client()
        await cba.close()
    except Exception as e:
        log.warning("Failed to close CBA client: %s", e)


async def scheduler_task(bot: Bot):
    """Daily scheduled task to post rates to channel."""
    global _channel_post_enabled, _channel_post_error

    # Skip if channel posting is disabled
    if not _channel_post_enabled:
        log.warning("scheduler: channel posting disabled (%s), skipping", _channel_post_error)
        return

    if not CHANNEL_ID:
        log.warning("scheduler: CHANNEL_ID not configured, skipping post")
        return

    try:
        log.info("scheduler: fetching rates & posting to channel")

        # Use new services
        htx = await get_htx_p2p_client()
        cba = await get_cba_client()

        usdt_cny, htx_meta = await htx.get_usdt_cny_price()
        cba_rates, cba_meta = await cba.get_rates()

        text = format_daily_rates_new(usdt_cny, cba_rates, htx_meta)

        await bot.send_message(chat_id=CHANNEL_ID, text=text)
        log.info("scheduler: posted to channel %s", CHANNEL_ID)

    except TelegramForbiddenError:
        log.error("scheduler: bot not member of channel %s - disabling future posts", CHANNEL_ID)
        _channel_post_enabled = False
        _channel_post_error = "Bot was removed from channel or lacks permissions"

    except Exception as e:
        log.exception("scheduler failed: %s", e)


async def main():
    log.info("Booting Highbit CNY Transfer Bot...")

    if not BOT_TOKEN:
        log.error("BOT_TOKEN not set! Check your .env file.")
        return

    # Create bot with FSM storage
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Shared antiflood middleware instance
    antiflood = AntiFloodMiddleware(0.8)
    dp.message.middleware(antiflood)
    dp.inline_query.middleware(antiflood)

    # Register routers (order matters!)
    dp.include_routers(
        # FSM handlers first (transfer form)
        h_transfer.router,
        # Then command handlers
        h_starthelp.router,
        h_admin.router,
        h_admin_transfer.router,
        h_kb.router,
        h_rates.router,
        h_convert.router,
        h_inline.router,
        # Fallback must be last (catch-all for numbers)
        h_fallback.router,
    )

    # Startup tasks
    await on_startup(bot)

    # Scheduler for daily posts (DISABLED - enable when needed)
    sched = AsyncIOScheduler(timezone=timezone(TIMEZONE))
    # Uncomment to enable daily channel posting:
    # sched.add_job(
    #     scheduler_task,
    #     "cron",
    #     hour=11,
    #     minute=0,
    #     args=(bot,),
    #     id="daily_rates_post",
    #     replace_existing=True,
    #     misfire_grace_time=3600,
    # )
    sched.start()
    log.info("Scheduler initialized (daily posts DISABLED)")

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
