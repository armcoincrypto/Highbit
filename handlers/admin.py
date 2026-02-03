import logging
import os
from decimal import Decimal
from datetime import datetime, time, timedelta

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from pytz import timezone

from services.htx_p2p import get_htx_p2p_client
from services.cba_rates import get_cba_client
from services.settings import get_settings_service
from utils.messages import format_daily_rates_new
from config import TIMEZONE, CHANNEL_ID

log = logging.getLogger(__name__)
router = Router()

_ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()}


def _is_admin(user: types.User | None) -> bool:
    return bool(user and user.id in _ADMIN_IDS)


# =============================================================================
# Admin Help Command
# =============================================================================

ADMIN_HELP = """
🔐 <b>Admin Commands</b>

<b>📊 Rate Management:</b>
/setrate — Set/view manual USDT/CNY rate
  • <code>/setrate</code> — Show current rate
  • <code>/setrate 7.25</code> — Set rate to 7.25
  • <code>/setrate 0</code> — Clear (use API)

/discounts — Manage discount percentages
/clear_cache — Clear all rate caches

<b>📢 Channel Management:</b>
/post_now — Post rates to channel now
/when — Show next scheduled post time
/channel_status — Check channel config

<b>📋 Request Management:</b>
/requests — View pending requests
/request_ID — View specific request

<b>📚 Knowledge Base (KB):</b>
/kb — Open KB menu (texts &amp; templates)
/kb_intro — Quick: send intro guide
/kb_how — Quick: send how-to guide
/kb_faq — Quick: send FAQ

<b>⚙️ How rates work:</b>
Base rate × (1 + discount) = final rate
Example: 7.25 × 0.99 = 7.18 CNY/USD
"""


@router.message(Command("admin"))
async def admin_help(m: types.Message):
    """Show admin commands and instructions."""
    if not _is_admin(m.from_user):
        return await m.answer("⛔️ Not authorized.")

    await m.answer(ADMIN_HELP)


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
        settings = await get_settings_service()

        usdt_cny, htx_meta = await htx.get_usdt_cny_price()
        cba_rates, cba_meta = await cba.get_rates()
        discounts = await settings.get_all_discounts()

        text = format_daily_rates_new(usdt_cny, cba_rates, htx_meta, discounts)

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


# =============================================================================
# Manual Rate Setting
# =============================================================================

@router.message(Command("setrate"))
async def set_rate(m: types.Message):
    """
    Admin command to set manual USDT/CNY rate.
    Usage: /setrate 7.25  (sets rate to 7.25 CNY per USDT)
    Usage: /setrate 0     (clears manual rate, use API)
    Usage: /setrate       (shows current rate)
    """
    if not _is_admin(m.from_user):
        return await m.answer("⛔️ Not authorized.")

    args = m.text.split(maxsplit=1)
    svc = await get_settings_service()

    # No argument - show current rate
    if len(args) < 2:
        manual_rate = await svc.get_manual_rate()
        htx = await get_htx_p2p_client()

        try:
            api_rate, meta = await htx.get_usdt_cny_price()
            api_source = meta.get("source", "unknown")
        except Exception:
            api_rate = None
            api_source = "unavailable"

        if manual_rate:
            status = f"📊 <b>USDT/CNY Rate</b>\n\n"
            status += f"✅ Manual rate: <b>{manual_rate}</b> CNY/USDT\n"
            status += f"📡 API rate: {api_rate or 'N/A'} ({api_source})"
        else:
            status = f"📊 <b>USDT/CNY Rate</b>\n\n"
            status += f"📡 Using API rate: <b>{api_rate or 'N/A'}</b> CNY/USDT\n"
            status += f"Source: {api_source}\n\n"
            status += "<i>No manual rate set</i>"

        status += "\n\n<b>Usage:</b>\n"
        status += "<code>/setrate 7.25</code> - Set rate to 7.25\n"
        status += "<code>/setrate 0</code> - Clear manual rate"

        return await m.answer(status)

    # Parse rate value
    try:
        rate_str = args[1].strip()
        rate = Decimal(rate_str)

        if rate < 0:
            return await m.answer("❌ Rate cannot be negative.")

        if rate == 0:
            # Clear manual rate
            await svc.set_manual_rate(None, m.from_user.id)
            await m.answer(
                "✅ Manual rate cleared.\n\n"
                "Bot will now use API rate (CoinGecko/P2P)."
            )
        elif rate < 5 or rate > 10:
            # Sanity check for USDT/CNY (typically 6.5-8.0)
            return await m.answer(
                f"⚠️ Rate {rate} seems unusual for USDT/CNY.\n\n"
                f"Expected range: 5.0 - 10.0\n"
                f"If you're sure, please confirm."
            )
        else:
            await svc.set_manual_rate(rate, m.from_user.id)
            await m.answer(
                f"✅ Manual rate set: <b>{rate}</b> CNY/USDT\n\n"
                f"This rate will be used for all calculations.\n"
                f"Use <code>/setrate 0</code> to clear."
            )

    except Exception as e:
        log.warning("Invalid rate input: %s", e)
        await m.answer(
            "❌ Invalid rate format.\n\n"
            "Usage:\n"
            "<code>/setrate 7.25</code> - Set rate\n"
            "<code>/setrate 0</code> - Clear rate"
        )


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


# =============================================================================
# Discount Management
# =============================================================================

class DiscountStates(StatesGroup):
    """FSM states for discount editing."""
    waiting_for_value = State()


# Labels for display
DISCOUNT_LABELS = {
    "usd_low": ("🇺🇸 USD", "< $4,000"),
    "usd_high": ("🇺🇸 USD", "≥ $4,000"),
    "amd_low": ("🇦🇲 AMD", "< 1.5M"),
    "amd_high": ("🇦🇲 AMD", "≥ 1.5M"),
    "usdt_low": ("📲 USDT", "< $4,000"),
    "usdt_high": ("📲 USDT", "≥ $4,000"),
}


def _format_discount_pct(value: Decimal) -> str:
    """Format discount as percentage string."""
    pct = value * 100
    return f"{pct:+.1f}%"


async def _build_discounts_keyboard() -> InlineKeyboardMarkup:
    """Build inline keyboard for discount selection."""
    svc = await get_settings_service()
    discounts = await svc.get_all_discounts()

    buttons = []
    for key, (currency, threshold) in DISCOUNT_LABELS.items():
        value = discounts.get(key, Decimal("0"))
        pct = _format_discount_pct(value)
        buttons.append([
            InlineKeyboardButton(
                text=f"{currency} {threshold}: {pct}",
                callback_data=f"disc_edit:{key}"
            )
        ])

    # Add refresh button
    buttons.append([
        InlineKeyboardButton(text="🔄 Refresh", callback_data="disc_refresh")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def _build_discounts_message() -> str:
    """Build discounts display message."""
    svc = await get_settings_service()
    discounts = await svc.get_all_discounts()

    lines = ["⚙️ <b>Discount Settings</b>\n"]

    current_currency = None
    for key, (currency, threshold) in DISCOUNT_LABELS.items():
        value = discounts.get(key, Decimal("0"))
        pct = _format_discount_pct(value)

        if currency != current_currency:
            if current_currency:
                lines.append("")
            lines.append(f"<b>{currency}</b>")
            current_currency = currency

        # Escape < for HTML
        threshold_escaped = threshold.replace("<", "&lt;")
        lines.append(f"  {threshold_escaped}: <code>{pct}</code>")

    lines.append("\n<i>Tap a button to edit</i>")

    return "\n".join(lines)


@router.message(Command("discounts"))
async def show_discounts(m: types.Message):
    """Show current discount settings with edit buttons."""
    if not _is_admin(m.from_user):
        return await m.answer("⛔️ Not authorized.")

    text = await _build_discounts_message()
    keyboard = await _build_discounts_keyboard()

    await m.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "disc_refresh")
async def refresh_discounts(callback: CallbackQuery):
    """Refresh discounts display."""
    if not _is_admin(callback.from_user):
        return await callback.answer("⛔️ Not authorized.", show_alert=True)

    text = await _build_discounts_message()
    keyboard = await _build_discounts_keyboard()

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer("Refreshed")


@router.callback_query(F.data.startswith("disc_edit:"))
async def start_edit_discount(callback: CallbackQuery, state: FSMContext):
    """Start editing a discount value."""
    if not _is_admin(callback.from_user):
        return await callback.answer("⛔️ Not authorized.", show_alert=True)

    key = callback.data.split(":")[1]
    if key not in DISCOUNT_LABELS:
        return await callback.answer("Invalid discount key", show_alert=True)

    currency, threshold = DISCOUNT_LABELS[key]
    svc = await get_settings_service()
    current = await svc.get_discount(key)
    current_pct = _format_discount_pct(current)

    # Store key in FSM
    await state.set_state(DiscountStates.waiting_for_value)
    await state.update_data(discount_key=key, message_id=callback.message.message_id)

    # Show quick preset buttons - more options
    presets = ["-0.5", "-0.7", "-0.9", "-1.0", "-1.2", "-1.3", "-1.5", "-1.7", "-2.0", "-2.5", "-3.0"]
    preset_buttons = []
    row = []
    for p in presets:
        row.append(InlineKeyboardButton(text=f"{p}%", callback_data=f"disc_set:{key}:{p}"))
        if len(row) == 4:
            preset_buttons.append(row)
            row = []
    if row:
        preset_buttons.append(row)

    preset_buttons.append([
        InlineKeyboardButton(text="❌ Cancel", callback_data="disc_cancel")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=preset_buttons)

    # Escape < for HTML
    threshold_escaped = threshold.replace("<", "&lt;")
    await callback.message.edit_text(
        f"✏️ <b>Edit {currency} {threshold_escaped}</b>\n\n"
        f"Current: <code>{current_pct}</code>\n\n"
        f"Choose a preset or type a value:\n"
        f"<i>Example: -1.5 for -1.5%</i>",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("disc_set:"))
async def set_discount_preset(callback: CallbackQuery, state: FSMContext):
    """Set discount from preset button."""
    if not _is_admin(callback.from_user):
        return await callback.answer("⛔️ Not authorized.", show_alert=True)

    parts = callback.data.split(":")
    key = parts[1]
    pct_str = parts[2]

    try:
        # Convert percentage to decimal (e.g., -1.0 -> -0.01)
        pct = Decimal(pct_str)
        value = pct / Decimal("100")

        svc = await get_settings_service()
        success = await svc.set_discount(key, value, callback.from_user.id)

        if success:
            await state.clear()

            currency, threshold = DISCOUNT_LABELS[key]
            await callback.answer(f"✅ {currency} {threshold} set to {pct_str}%")

            # Show updated discounts
            text = await _build_discounts_message()
            keyboard = await _build_discounts_keyboard()
            await callback.message.edit_text(text, reply_markup=keyboard)
        else:
            await callback.answer("Failed to save", show_alert=True)

    except Exception as e:
        log.exception("Failed to set discount: %s", e)
        await callback.answer(f"Error: {e}", show_alert=True)


@router.callback_query(F.data == "disc_cancel")
async def cancel_discount_edit(callback: CallbackQuery, state: FSMContext):
    """Cancel discount editing."""
    await state.clear()

    text = await _build_discounts_message()
    keyboard = await _build_discounts_keyboard()

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer("Cancelled")


@router.message(DiscountStates.waiting_for_value)
async def receive_discount_value(m: types.Message, state: FSMContext):
    """Receive custom discount value from user."""
    if not _is_admin(m.from_user):
        await state.clear()
        return

    data = await state.get_data()
    key = data.get("discount_key")

    if not key:
        await state.clear()
        return await m.answer("Session expired. Use /discounts again.")

    try:
        # Parse value (accept formats: -1.7, -1.7%, 1.7%, -0.017)
        text = m.text.strip()
        # Remove % and common variants
        text = text.replace("%", "").replace("％", "").replace("٪", "")
        # Remove spaces
        text = text.replace(" ", "")
        # Handle if user forgot minus sign for discount
        pct = Decimal(text)

        # If value looks like a percentage (> 1 or < -1), convert to decimal
        if pct > Decimal("1") or pct < Decimal("-1"):
            value = pct / Decimal("100")
        else:
            value = pct

        # For discounts, value should typically be negative
        # If user entered positive, assume they meant negative discount
        if value > 0:
            # Ask for confirmation or just negate
            value = -value

        # Validate range (-10% to +10%)
        if value < Decimal("-0.1") or value > Decimal("0.1"):
            return await m.answer(
                "⚠️ Value out of range.\n"
                "Enter between -10% and +10%\n"
                "Example: -1.5 for -1.5%"
            )

        svc = await get_settings_service()
        success = await svc.set_discount(key, value, m.from_user.id)

        if success:
            await state.clear()
            currency, threshold = DISCOUNT_LABELS[key]
            pct_display = _format_discount_pct(value)

            await m.answer(f"✅ {currency} {threshold} set to {pct_display}")

            # Send updated discounts
            text = await _build_discounts_message()
            keyboard = await _build_discounts_keyboard()
            await m.answer(text, reply_markup=keyboard)
        else:
            await m.answer("❌ Failed to save. Use /discounts again.")

    except Exception as e:
        log.warning("Invalid discount input: %s", e)
        await m.answer(
            "⚠️ Invalid value.\n"
            "Enter a number like: -1.5 or -0.015\n"
            "Example: -1.5 for -1.5%"
        )
