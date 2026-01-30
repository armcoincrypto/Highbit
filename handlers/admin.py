import logging
import os
from datetime import datetime, time, timedelta

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from pytz import timezone

from services.htx_p2p import get_htx_p2p_client
from services.cba_rates import get_cba_client
from utils.messages import format_daily_rates_new
from config import TIMEZONE, CHANNEL_ID

log = logging.getLogger(__name__)
router = Router()

_ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()}


def _is_admin(user: types.User | None) -> bool:
    return bool(user and user.id in _ADMIN_IDS)


def _next_10_o_clock(tzname: str):
    tz = timezone(tzname)
    now = datetime.now(tz)
    today_10 = tz.localize(datetime.combine(now.date(), time(10, 0)))
    if now < today_10:
        return today_10
    return today_10 + timedelta(days=1)


@router.message(Command("when"))
async def when(m: types.Message):
    if not _is_admin(m.from_user):
        return await m.answer("⛔️ Not authorized.")

    tz = timezone(TIMEZONE)
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z")
    nrt = _next_10_o_clock(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S %Z")

    # Get channel status
    from main import get_channel_status
    enabled, error = get_channel_status()
    status = "✅ Enabled" if enabled else f"❌ Disabled: {error}"

    await m.answer(
        f"⏰ Timezone: {TIMEZONE}\n"
        f"🕒 Now: {now}\n"
        f"📮 Next daily post: {nrt}\n"
        f"📢 Channel status: {status}"
    )


@router.message(Command("post_now"))
async def post_now(m: types.Message):
    if not _is_admin(m.from_user):
        return await m.answer("⛔️ Not authorized.")

    try:
        # Use new services
        htx = await get_htx_p2p_client()
        cba = await get_cba_client()

        usdt_cny, htx_meta = await htx.get_usdt_cny_price()
        cba_rates, cba_meta = await cba.get_rates()

        text = format_daily_rates_new(usdt_cny, cba_rates, htx_meta)

        if CHANNEL_ID:
            await m.bot.send_message(chat_id=CHANNEL_ID, text=text)
            await m.answer("✅ Posted to channel.")
        else:
            await m.answer("⚠️ CHANNEL_ID not configured.")

    except TelegramForbiddenError:
        await m.answer(
            "❌ <b>Cannot post to channel</b>\n\n"
            "Bot is not a member or lacks permissions.\n"
            "• Add bot to the channel\n"
            "• Make it admin with 'Post Messages' permission"
        )
    except Exception as e:
        log.exception("post_now failed: %s", e)
        await m.answer(f"⚠️ Failed to post: {e}")


@router.message(Command("post_target_test"))
async def post_target_test(m: types.Message):
    """
    Admin command to test channel posting configuration.
    Sends a small test message to verify bot can post.
    """
    if not _is_admin(m.from_user):
        return await m.answer("⛔️ Not authorized.")

    if not CHANNEL_ID:
        await m.answer(
            "❌ <b>CHANNEL_ID not configured</b>\n\n"
            "Set CHANNEL_ID in your .env file:\n"
            "<code>CHANNEL_ID=-100123456789</code>\n\n"
            "To find your channel ID:\n"
            "1. Forward any message from channel to @userinfobot\n"
            "2. Or add bot to channel and check logs"
        )
        return

    try:
        # Test 1: Try to get chat info
        chat = await m.bot.get_chat(CHANNEL_ID)
        chat_info = f"✅ Channel found: {chat.title or chat.username} (ID: {chat.id})"

        # Test 2: Check admin status for channels
        admin_info = ""
        if chat.type == "channel":
            try:
                member = await m.bot.get_chat_member(chat.id, m.bot.id)
                if member.status == "administrator":
                    admin_info = "✅ Bot is admin"
                elif member.status == "creator":
                    admin_info = "✅ Bot is creator (owner)"
                else:
                    admin_info = f"⚠️ Bot status: {member.status} (needs admin)"
            except Exception as e:
                admin_info = f"⚠️ Could not check admin status: {e}"

        # Test 3: Try sending a test message
        try:
            test_msg = await m.bot.send_message(
                chat_id=CHANNEL_ID,
                text="🔧 <b>Channel Test</b>\n\nBot posting works correctly!\nThis is a test message from /post_target_test"
            )
            send_info = "✅ Test message sent successfully!"

            # Delete test message after 5 seconds
            import asyncio
            asyncio.create_task(delete_after_delay(test_msg, 5))

        except TelegramForbiddenError:
            send_info = (
                "❌ <b>Cannot send messages</b>\n"
                "Bot needs 'Post Messages' permission as admin"
            )
        except TelegramBadRequest as e:
            send_info = f"❌ Send failed: {e}"

        # Report results
        await m.answer(
            f"📊 <b>Channel Post Test Results</b>\n\n"
            f"Target: <code>{CHANNEL_ID}</code>\n\n"
            f"{chat_info}\n"
            f"{admin_info}\n"
            f"{send_info}"
        )

    except TelegramForbiddenError:
        await m.answer(
            f"❌ <b>Bot cannot access channel</b>\n\n"
            f"Target: <code>{CHANNEL_ID}</code>\n\n"
            f"Possible causes:\n"
            f"• Bot is not a member of the channel\n"
            f"• Bot was kicked from the channel\n"
            f"• Channel ID is incorrect\n\n"
            f"<b>Solution:</b>\n"
            f"1. Add the bot to your channel\n"
            f"2. Make it admin with 'Post Messages' permission"
        )

    except TelegramBadRequest as e:
        await m.answer(
            f"❌ <b>Invalid Channel ID</b>\n\n"
            f"Target: <code>{CHANNEL_ID}</code>\n"
            f"Error: {e}\n\n"
            f"<b>Correct format:</b>\n"
            f"• Channel ID: <code>-100123456789</code> (starts with -100)\n"
            f"• Or username: <code>@channelname</code>"
        )

    except Exception as e:
        log.exception("post_target_test failed: %s", e)
        await m.answer(f"❌ Test failed with error: {e}")


async def delete_after_delay(msg: types.Message, delay: int):
    """Delete message after delay (background task)."""
    import asyncio
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass  # Ignore if already deleted


@router.message(Command("clear_cache"))
async def clear_cache(m: types.Message):
    """Admin command to clear rate cache."""
    if not _is_admin(m.from_user):
        return await m.answer("⛔️ Not authorized.")

    # Clear all caches
    from services.rates import get_rate_client
    rc = await get_rate_client()
    rc.clear_cache()

    htx = await get_htx_p2p_client()
    htx.clear_cache()

    cba = await get_cba_client()
    cba.clear_cache()

    await m.answer("✅ All rate caches cleared (legacy, HTX P2P, CBA).")


@router.message(Command("channel_status"))
async def channel_status(m: types.Message):
    """Check current channel posting status."""
    if not _is_admin(m.from_user):
        return await m.answer("⛔️ Not authorized.")

    from main import get_channel_status
    enabled, error = get_channel_status()

    if enabled:
        status = f"✅ <b>Channel posting is ENABLED</b>\n\nTarget: <code>{CHANNEL_ID}</code>"
    else:
        status = (
            f"❌ <b>Channel posting is DISABLED</b>\n\n"
            f"Target: <code>{CHANNEL_ID or 'Not configured'}</code>\n"
            f"Reason: {error}\n\n"
            f"Use /post_target_test to diagnose"
        )

    await m.answer(status)
