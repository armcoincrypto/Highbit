"""
Admin handlers for managing transfer requests.
"""
import logging

from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import ADMIN_IDS
from models.database import get_database, RequestStatus

log = logging.getLogger(__name__)
router = Router()


def is_admin(user: types.User | None) -> bool:
    """Check if user is admin."""
    return user and user.id in ADMIN_IDS


# ============================================================================
# Admin Commands
# ============================================================================

@router.message(Command("requests"))
async def cmd_requests(m: types.Message):
    """Show all active requests (admin only)."""
    if not is_admin(m.from_user):
        return await m.answer("⛔️ Not authorized.")

    db = await get_database()
    requests = db.get_active_requests(limit=20)

    if not requests:
        return await m.answer("No active requests.")

    text = "📋 <b>Active Requests:</b>\n\n"
    for req in requests:
        status_emoji = {
            RequestStatus.NEW: "🆕",
            RequestStatus.ASSIGNED: "👋",
            RequestStatus.CONTACTED: "📞",
            RequestStatus.PAYMENT_RECEIVED: "💵",
            RequestStatus.SENT: "🚀",
        }.get(req.status, "❓")

        user_link = f"@{req.username}" if req.username else f"ID:{req.user_id}"
        text += (
            f"{status_emoji} #{req.id}: ¥{req.cny_amount:,.0f} → {req.pay_currency}\n"
            f"   {user_link} | {req.status.value}\n\n"
        )

    await m.answer(text)


@router.message(Command("stats"))
async def cmd_stats(m: types.Message):
    """Show transfer statistics (admin only)."""
    if not is_admin(m.from_user):
        return await m.answer("⛔️ Not authorized.")

    db = await get_database()
    stats = db.get_stats()

    await m.answer(
        f"📊 <b>Transfer Statistics</b>\n\n"
        f"Total requests: {stats['total_requests']}\n"
        f"Completed: {stats['completed']}\n"
        f"Active: {stats['active']}\n"
        f"Total CNY volume: ¥{stats['total_cny_volume']:,.0f}",
    )


@router.message(Command("request"))
async def cmd_request_detail(m: types.Message):
    """Show request details. Usage: /request 123"""
    if not is_admin(m.from_user):
        return await m.answer("⛔️ Not authorized.")

    args = m.text.split()
    if len(args) < 2:
        return await m.answer("Usage: /request <id>")

    try:
        request_id = int(args[1])
    except ValueError:
        return await m.answer("Invalid request ID.")

    db = await get_database()
    req = db.get_request(request_id)

    if not req:
        return await m.answer(f"Request #{request_id} not found.")

    files = db.get_request_files(request_id)
    history = db.get_status_history(request_id)

    user_link = f"@{req.username}" if req.username else f"ID:{req.user_id}"

    text = (
        f"📋 <b>Request #{req.id}</b>\n\n"
        f"👤 User: {user_link}\n"
        f"💰 CNY: ¥{req.cny_amount:,.0f}\n"
        f"💵 USD equiv: ${req.usd_equiv:,.2f}\n"
        f"📱 Method: {req.method}\n"
        f"💳 Pay: {req.pay_currency}\n"
        f"💵 Amount due: {req.amount_due}\n"
        f"📉 Discount: {req.discount_pct}%\n"
        f"📊 HTX rate: {req.htx_price}\n"
        f"📌 Status: {req.status.value}\n"
        f"👨‍💼 Assigned: {req.assigned_admin_id or 'None'}\n"
        f"📅 Created: {req.created_at.strftime('%Y-%m-%d %H:%M')}\n"
    )

    if req.notes:
        text += f"\n📝 Notes: {req.notes}\n"

    if history:
        text += "\n📜 <b>History:</b>\n"
        for h in history[-5:]:
            text += f"  • {h.old_status} → {h.new_status} ({h.changed_at.strftime('%H:%M')})\n"

    keyboard = get_status_keyboard(request_id, req.status)

    await m.answer(text, reply_markup=keyboard)

    # Send attached files
    for f in files:
        try:
            if f.file_type == "photo":
                await m.answer_photo(f.file_id, caption=f"📎 File for #{request_id}")
            else:
                await m.answer_document(f.file_id, caption=f"📎 File for #{request_id}")
        except Exception as e:
            log.warning("Failed to send file %s: %s", f.file_id, e)


def get_status_keyboard(request_id: int, current_status: RequestStatus) -> InlineKeyboardMarkup:
    """Get status change keyboard based on current status."""
    buttons = []

    if current_status == RequestStatus.NEW:
        buttons.append([
            InlineKeyboardButton(text="✋ Assign to me", callback_data=f"admin_assign_{request_id}"),
        ])
    if current_status in (RequestStatus.NEW, RequestStatus.ASSIGNED):
        buttons.append([
            InlineKeyboardButton(text="📞 Contacted", callback_data=f"admin_contacted_{request_id}"),
        ])
    if current_status in (RequestStatus.ASSIGNED, RequestStatus.CONTACTED):
        buttons.append([
            InlineKeyboardButton(text="💵 Payment received", callback_data=f"admin_paid_{request_id}"),
        ])
    if current_status == RequestStatus.PAYMENT_RECEIVED:
        buttons.append([
            InlineKeyboardButton(text="🚀 Sent", callback_data=f"admin_sent_{request_id}"),
        ])
    if current_status == RequestStatus.SENT:
        buttons.append([
            InlineKeyboardButton(text="✅ Completed", callback_data=f"admin_done_{request_id}"),
        ])
    if current_status not in (RequestStatus.COMPLETED, RequestStatus.CANCELLED):
        buttons.append([
            InlineKeyboardButton(text="❌ Cancel", callback_data=f"admin_cancel_{request_id}"),
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None


# ============================================================================
# Status Change Callbacks
# ============================================================================

@router.callback_query(F.data.startswith("admin_assign_"))
async def cb_assign(callback: types.CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user):
        return await callback.answer("⛔️ Not authorized.", show_alert=True)

    request_id = int(callback.data.split("_")[-1])
    db = await get_database()

    if db.update_request_status(request_id, RequestStatus.ASSIGNED, callback.from_user.id):
        await callback.answer("✅ Assigned to you!")
        await update_status_message(callback, request_id, "ASSIGNED", callback.from_user.id)
        await notify_user_status(bot, request_id, "assigned", "An operator has been assigned to your request.")
    else:
        await callback.answer("❌ Failed to assign", show_alert=True)


@router.callback_query(F.data.startswith("admin_contacted_"))
async def cb_contacted(callback: types.CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user):
        return await callback.answer("⛔️ Not authorized.", show_alert=True)

    request_id = int(callback.data.split("_")[-1])
    db = await get_database()

    if db.update_request_status(request_id, RequestStatus.CONTACTED, callback.from_user.id):
        await callback.answer("✅ Marked as contacted!")
        await update_status_message(callback, request_id, "CONTACTED", callback.from_user.id)
    else:
        await callback.answer("❌ Failed", show_alert=True)


@router.callback_query(F.data.startswith("admin_paid_"))
async def cb_paid(callback: types.CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user):
        return await callback.answer("⛔️ Not authorized.", show_alert=True)

    request_id = int(callback.data.split("_")[-1])
    db = await get_database()

    if db.update_request_status(request_id, RequestStatus.PAYMENT_RECEIVED, callback.from_user.id):
        await callback.answer("✅ Payment received!")
        await update_status_message(callback, request_id, "PAYMENT_RECEIVED", callback.from_user.id)
        await notify_user_status(bot, request_id, "payment_received", "Payment received! Processing your transfer...")
    else:
        await callback.answer("❌ Failed", show_alert=True)


@router.callback_query(F.data.startswith("admin_sent_"))
async def cb_sent(callback: types.CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user):
        return await callback.answer("⛔️ Not authorized.", show_alert=True)

    request_id = int(callback.data.split("_")[-1])
    db = await get_database()

    if db.update_request_status(request_id, RequestStatus.SENT, callback.from_user.id):
        await callback.answer("✅ Marked as sent!")
        await update_status_message(callback, request_id, "SENT", callback.from_user.id)
        await notify_user_status(bot, request_id, "sent", "🚀 Your CNY transfer has been sent! It should arrive within minutes.")
    else:
        await callback.answer("❌ Failed", show_alert=True)


@router.callback_query(F.data.startswith("admin_done_"))
async def cb_done(callback: types.CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user):
        return await callback.answer("⛔️ Not authorized.", show_alert=True)

    request_id = int(callback.data.split("_")[-1])
    db = await get_database()

    if db.update_request_status(request_id, RequestStatus.COMPLETED, callback.from_user.id):
        await callback.answer("✅ Completed!")
        await update_status_message(callback, request_id, "COMPLETED", callback.from_user.id)
        await notify_user_status(bot, request_id, "completed", "✅ Your transfer is complete! Thank you for using Highbit.")
    else:
        await callback.answer("❌ Failed", show_alert=True)


@router.callback_query(F.data.startswith("admin_cancel_"))
async def cb_cancel(callback: types.CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user):
        return await callback.answer("⛔️ Not authorized.", show_alert=True)

    request_id = int(callback.data.split("_")[-1])
    db = await get_database()

    if db.update_request_status(request_id, RequestStatus.CANCELLED, callback.from_user.id):
        await callback.answer("❌ Cancelled!")
        await update_status_message(callback, request_id, "CANCELLED", callback.from_user.id)
        await notify_user_status(bot, request_id, "cancelled", "❌ Your transfer request has been cancelled. Contact @Highbitagent for details.")
    else:
        await callback.answer("❌ Failed", show_alert=True)


async def update_status_message(callback: types.CallbackQuery, request_id: int, status: str, admin_id: int):
    """Update the admin message with new status."""
    try:
        text = callback.message.text or callback.message.caption or ""
        # Update status line
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if "Status:" in line or "📌" in line:
                lines[i] = f"📌 Status: {status} (by {admin_id})"
                break

        db = await get_database()
        req = db.get_request(request_id)
        keyboard = get_status_keyboard(request_id, req.status) if req else None

        await callback.message.edit_text(
            "\n".join(lines),
            reply_markup=keyboard,
        )
    except Exception as e:
        log.warning("Failed to update message: %s", e)


async def notify_user_status(bot: Bot, request_id: int, status: str, message: str):
    """Notify user about status change."""
    try:
        db = await get_database()
        req = db.get_request(request_id)
        if req:
            await bot.send_message(
                chat_id=req.user_id,
                text=f"📋 Request #{request_id}\n\n{message}",
            )
    except Exception as e:
        log.warning("Failed to notify user: %s", e)
