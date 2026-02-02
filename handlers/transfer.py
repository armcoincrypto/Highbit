"""
Transfer request form handler with FSM (Finite State Machine).
Guides user through the CNY transfer request process.
"""
import logging
from decimal import Decimal, InvalidOperation

from aiogram import Router, types, F, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

from config import MIN_ORDER_CNY, ADMIN_CHAT_ID
from services.pricing import (
    calculate_pricing,
    PaymentCurrency,
    TransferMethod,
    MinimumOrderError,
    PricingError,
    format_pricing_summary,
)
from models.database import get_database, RequestStatus

log = logging.getLogger(__name__)
router = Router()


class TransferForm(StatesGroup):
    """States for transfer request form."""
    amount = State()
    method = State()
    currency = State()
    timing = State()
    recipient = State()
    confirm = State()


# Keyboard helpers
def get_method_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Alipay"), KeyboardButton(text="💬 WeChat")],
            [KeyboardButton(text="🏦 China Bank Account")],
            [KeyboardButton(text="❌ Cancel")],
        ],
        resize_keyboard=True,
    )


def get_currency_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💵 USD cash"), KeyboardButton(text="֏ AMD cash")],
            [KeyboardButton(text="₽ RUB card"), KeyboardButton(text="💎 USDT")],
            [KeyboardButton(text="❌ Cancel")],
        ],
        resize_keyboard=True,
    )


def get_timing_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⚡ Now"), KeyboardButton(text="📅 Today later")],
            [KeyboardButton(text="📆 Schedule for another day")],
            [KeyboardButton(text="❌ Cancel")],
        ],
        resize_keyboard=True,
    )


def get_confirm_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Confirm Request", callback_data="transfer_confirm"),
            ],
            [
                InlineKeyboardButton(text="✏️ Edit Amount", callback_data="transfer_edit_amount"),
                InlineKeyboardButton(text="❌ Cancel", callback_data="transfer_cancel"),
            ],
        ]
    )


def get_cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Cancel")]],
        resize_keyboard=True,
    )


# ============================================================================
# Entry point: /transfer or button
# ============================================================================

@router.message(Command("transfer"))
@router.message(F.text.in_(["📤 Transfer to China", "📤 Buy CNY", "transfer"]))
async def cmd_transfer(m: types.Message, state: FSMContext):
    """Start transfer request flow."""
    await state.clear()

    await m.answer(
        "💱 <b>CNY Փdelays Հdelays</b>\n\n"
        f"📌 Նdelays delaysdelays delaysdelays <b>{MIN_ORDER_CNY:,} ¥</b>\n\n"
        "Delaysdelays delaysdelays delays ¥ (CNY):\n\n"
        "<i>Օdelaysdelays, delaysdelays <code>10000</code> delays <code>15000</code></i>",
        reply_markup=get_cancel_keyboard(),
    )
    await state.set_state(TransferForm.amount)


# ============================================================================
# Step 1: Amount
# ============================================================================

@router.message(TransferForm.amount)
async def process_amount(m: types.Message, state: FSMContext):
    if m.text == "❌ Cancel":
        await state.clear()
        return await m.answer("Cancelled.", reply_markup=ReplyKeyboardRemove())

    # Parse amount
    try:
        text = m.text.strip().replace(",", "").replace("¥", "").replace("CNY", "").strip()
        amount = Decimal(text)
    except (InvalidOperation, ValueError):
        return await m.answer(
            "❌ Please enter a valid number.\n"
            "Example: `10000` or `8000`",
            parse_mode="Markdown",
        )

    # Validate minimum
    if amount < MIN_ORDER_CNY:
        return await m.answer(
            f"❌ Նdelays delays delaysdelays delaysdelays <b>{MIN_ORDER_CNY:,} ¥</b> CNY:\n"
            f"Delays delays delays: ¥{amount:,.0f}\n\n"
            "Delaysdelays delaysdelays delays delaysdelays:",
        )

    await state.update_data(cny_amount=amount)

    await m.answer(
        f"✅ Գdelays delaysdelays: ¥{amount:,.0f} CNY\n\n"
        "Delaysdelays delays delaysdelays Delays delaysdelays:",
        reply_markup=get_method_keyboard(),
    )
    await state.set_state(TransferForm.method)


# ============================================================================
# Step 2: Transfer Method
# ============================================================================

@router.message(TransferForm.method)
async def process_method(m: types.Message, state: FSMContext):
    if m.text == "❌ Cancel":
        await state.clear()
        return await m.answer("Cancelled.", reply_markup=ReplyKeyboardRemove())

    method_map = {
        "📱 Alipay": TransferMethod.ALIPAY,
        "💬 WeChat": TransferMethod.WECHAT,
        "🏦 China Bank Account": TransferMethod.BANK,
    }

    method = method_map.get(m.text)
    if not method:
        return await m.answer("Please choose from the buttons below.")

    await state.update_data(method=method)

    await m.answer(
        f"✅ Մdelays delaysdelays: {m.text}\n\n"
        "Delaysdelays delays delaysdelays Delays:",
        reply_markup=get_currency_keyboard(),
    )
    await state.set_state(TransferForm.currency)


# ============================================================================
# Step 3: Payment Currency
# ============================================================================

@router.message(TransferForm.currency)
async def process_currency(m: types.Message, state: FSMContext):
    if m.text == "❌ Cancel":
        await state.clear()
        return await m.answer("Cancelled.", reply_markup=ReplyKeyboardRemove())

    currency_map = {
        "💵 USD cash": PaymentCurrency.USD,
        "֏ AMD cash": PaymentCurrency.AMD,
        "₽ RUB card": PaymentCurrency.RUB,
        "💎 USDT": PaymentCurrency.USDT,
    }

    currency = currency_map.get(m.text)
    if not currency:
        return await m.answer("Please choose from the buttons below.")

    await state.update_data(pay_currency=currency)

    await m.answer(
        f"✅ Վdelays delaysdelays: {m.text}\n\n"
        "Երdelays delays Delays delays delaysdelays:",
        reply_markup=get_timing_keyboard(),
    )
    await state.set_state(TransferForm.timing)


# ============================================================================
# Step 4: Timing
# ============================================================================

@router.message(TransferForm.timing)
async def process_timing(m: types.Message, state: FSMContext):
    if m.text == "❌ Cancel":
        await state.clear()
        return await m.answer("Cancelled.", reply_markup=ReplyKeyboardRemove())

    timing_map = {
        "⚡ Now": "now",
        "📅 Today later": "today",
        "📆 Schedule for another day": "scheduled",
    }

    timing = timing_map.get(m.text)
    if not timing:
        return await m.answer("Please choose from the buttons below.")

    await state.update_data(timing=timing)

    data = await state.get_data()
    method = data["method"]

    if method == TransferMethod.BANK:
        prompt = (
            "📝 Please provide the recipient's bank details:\n\n"
            "• Bank name\n"
            "• Account number\n"
            "• Account holder name\n\n"
            "You can also send a photo of the bank details."
        )
    else:
        prompt = (
            f"📱 Please send the recipient's {method.value.title()} QR code.\n\n"
            "Upload a clear photo of the QR code.\n"
            "You can also send the payment link."
        )

    await m.answer(prompt, reply_markup=get_cancel_keyboard())
    await state.set_state(TransferForm.recipient)


# ============================================================================
# Step 5: Recipient Details / QR Code
# ============================================================================

@router.message(TransferForm.recipient, F.photo)
async def process_recipient_photo(m: types.Message, state: FSMContext):
    """Handle QR code or bank details photo."""
    photo = m.photo[-1]  # Largest size
    await state.update_data(
        recipient_file_id=photo.file_id,
        recipient_file_type="photo",
        recipient_text=None,
    )
    await show_confirmation(m, state)


@router.message(TransferForm.recipient, F.document)
async def process_recipient_document(m: types.Message, state: FSMContext):
    """Handle document upload."""
    await state.update_data(
        recipient_file_id=m.document.file_id,
        recipient_file_type="document",
        recipient_text=None,
    )
    await show_confirmation(m, state)


@router.message(TransferForm.recipient)
async def process_recipient_text(m: types.Message, state: FSMContext):
    """Handle text bank details."""
    if m.text == "❌ Cancel":
        await state.clear()
        return await m.answer("Cancelled.", reply_markup=ReplyKeyboardRemove())

    if len(m.text) < 10:
        return await m.answer(
            "Please provide complete recipient details or upload a QR code photo."
        )

    await state.update_data(
        recipient_file_id=None,
        recipient_file_type=None,
        recipient_text=m.text,
    )
    await show_confirmation(m, state)


async def show_confirmation(m: types.Message, state: FSMContext):
    """Show order summary and ask for confirmation."""
    data = await state.get_data()

    try:
        pricing = await calculate_pricing(
            cny_amount=data["cny_amount"],
            payment_currency=data["pay_currency"],
            transfer_method=data["method"],
        )
        await state.update_data(pricing=pricing.to_dict())

        summary = format_pricing_summary(pricing, lang="en")

        timing_text = {
            "now": "⚡ As soon as possible",
            "today": "📅 Today (will contact for time)",
            "scheduled": "📆 Scheduled (will contact for date/time)",
        }.get(data.get("timing", "now"), "Now")

        method_text = {
            TransferMethod.ALIPAY: "📱 Alipay",
            TransferMethod.WECHAT: "💬 WeChat",
            TransferMethod.BANK: "🏦 Bank Transfer",
        }.get(data["method"], "Unknown")

        full_summary = (
            f"{summary}\n\n"
            f"📅 When: {timing_text}\n"
            f"📤 Method: {method_text}\n"
            f"📎 Recipient details: {'Photo uploaded ✓' if data.get('recipient_file_id') else 'Text provided ✓'}\n\n"
            f"⏱ Estimated completion: 20-60 minutes after payment\n\n"
            "Please confirm your request:"
        )

        await m.answer(
            full_summary,
            reply_markup=get_confirm_keyboard(),
            parse_mode="Markdown",
        )
        await state.set_state(TransferForm.confirm)

    except MinimumOrderError as e:
        await m.answer(f"❌ {e}", reply_markup=ReplyKeyboardRemove())
        await state.clear()
    except PricingError as e:
        log.exception("Pricing error: %s", e)
        await m.answer(
            "⚠️ Unable to calculate pricing. Please try again later.",
            reply_markup=ReplyKeyboardRemove(),
        )
        await state.clear()


# ============================================================================
# Step 6: Confirmation
# ============================================================================

@router.callback_query(TransferForm.confirm, F.data == "transfer_confirm")
async def confirm_transfer(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    """Confirm and create the transfer request."""
    await callback.answer("Processing...")

    data = await state.get_data()
    pricing_data = data.get("pricing", {})

    try:
        db = await get_database()

        # Create request
        request_id = db.create_request(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            cny_amount=Decimal(pricing_data["cny_amount"]),
            usd_equiv=Decimal(pricing_data["usd_equivalent"]),
            method=pricing_data["transfer_method"],
            pay_currency=pricing_data["payment_currency"],
            amount_due=Decimal(pricing_data["amount_due"]),
            discount_pct=Decimal(pricing_data["discount_percent"]),
            htx_price=Decimal(pricing_data["htx_usdt_cny"]),
            cba_rates={
                "USD_AMD": pricing_data["cba_usd_amd"],
                "CNY_AMD": pricing_data["cba_cny_amd"],
                "RUB_AMD": pricing_data.get("cba_rub_amd"),
            },
            scheduled_time=data.get("timing", "now"),
        )

        # Add file if uploaded
        if data.get("recipient_file_id"):
            db.add_file(
                request_id=request_id,
                file_id=data["recipient_file_id"],
                file_type=data.get("recipient_file_type", "photo"),
            )

        # Notify admin
        await notify_admin_new_request(bot, request_id, data, pricing_data, callback.from_user)

        # Confirm to user
        await callback.message.edit_text(
            f"✅ **Request #{request_id} Created!**\n\n"
            f"Our operator will contact you shortly.\n"
            f"Contact: @Highbitagent\n\n"
            f"You can check status with /my_requests",
            parse_mode="Markdown",
        )

    except Exception as e:
        log.exception("Failed to create request: %s", e)
        await callback.message.edit_text(
            "⚠️ Failed to create request. Please try again or contact @Highbitagent"
        )

    await state.clear()


@router.callback_query(TransferForm.confirm, F.data == "transfer_edit_amount")
async def edit_amount(callback: types.CallbackQuery, state: FSMContext):
    """Go back to edit amount."""
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer(
        "Enter new CNY amount:",
        reply_markup=get_cancel_keyboard(),
    )
    await state.set_state(TransferForm.amount)


@router.callback_query(TransferForm.confirm, F.data == "transfer_cancel")
async def cancel_transfer(callback: types.CallbackQuery, state: FSMContext):
    """Cancel the transfer request."""
    await callback.answer("Cancelled")
    await callback.message.edit_text("❌ Request cancelled.")
    await state.clear()


# ============================================================================
# Admin Notification
# ============================================================================

async def notify_admin_new_request(
    bot: Bot,
    request_id: int,
    data: dict,
    pricing_data: dict,
    user: types.User,
):
    """Send notification to admin chat about new request."""
    if not ADMIN_CHAT_ID:
        log.warning("ADMIN_CHAT_ID not configured, skipping notification")
        return

    method_text = {
        "alipay": "📱 Alipay",
        "wechat": "💬 WeChat",
        "bank": "🏦 Bank",
    }.get(pricing_data.get("transfer_method", ""), "Unknown")

    user_link = f"@{user.username}" if user.username else f"ID: {user.id}"

    message = (
        f"🆕 **New Transfer Request #{request_id}**\n\n"
        f"👤 User: {user_link}\n"
        f"💰 Amount: ¥{pricing_data['cny_amount']} CNY\n"
        f"💵 USD equivalent: ${pricing_data['usd_equivalent']}\n"
        f"📱 Method: {method_text}\n"
        f"💳 Pay: {pricing_data['payment_currency']}\n"
        f"💵 Amount due: {pricing_data['amount_due']}\n"
        f"📉 Discount: {pricing_data['discount_percent']}%\n"
        f"📊 HTX rate: {pricing_data['htx_usdt_cny']} CNY/USDT\n"
        f"⏰ Timing: {data.get('timing', 'now')}\n"
        f"📌 Status: NEW"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✋ Assign to me", callback_data=f"admin_assign_{request_id}"),
            ],
            [
                InlineKeyboardButton(text="📞 Contacted", callback_data=f"admin_contacted_{request_id}"),
                InlineKeyboardButton(text="💵 Paid", callback_data=f"admin_paid_{request_id}"),
            ],
            [
                InlineKeyboardButton(text="🚀 Sent", callback_data=f"admin_sent_{request_id}"),
                InlineKeyboardButton(text="✅ Done", callback_data=f"admin_done_{request_id}"),
            ],
            [
                InlineKeyboardButton(text="❌ Cancel", callback_data=f"admin_cancel_{request_id}"),
            ],
        ]
    )

    try:
        await bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=message,
            reply_markup=keyboard,
            parse_mode="Markdown",
        )

        # Forward QR code if uploaded
        if data.get("recipient_file_id"):
            if data.get("recipient_file_type") == "document":
                await bot.send_document(ADMIN_CHAT_ID, data["recipient_file_id"])
            else:
                await bot.send_photo(ADMIN_CHAT_ID, data["recipient_file_id"])

    except Exception as e:
        log.exception("Failed to notify admin: %s", e)


# ============================================================================
# User Commands
# ============================================================================

@router.message(Command("my_requests"))
async def cmd_my_requests(m: types.Message):
    """Show user's recent requests."""
    db = await get_database()
    requests = db.get_user_requests(m.from_user.id, limit=5)

    if not requests:
        return await m.answer("You don't have any transfer requests yet.\n\nUse /transfer to create one.")

    text = "📋 **Your Recent Requests:**\n\n"
    for req in requests:
        status_emoji = {
            RequestStatus.NEW: "🆕",
            RequestStatus.ASSIGNED: "👋",
            RequestStatus.CONTACTED: "📞",
            RequestStatus.PAYMENT_RECEIVED: "💵",
            RequestStatus.SENT: "🚀",
            RequestStatus.COMPLETED: "✅",
            RequestStatus.CANCELLED: "❌",
        }.get(req.status, "❓")

        text += (
            f"{status_emoji} #{req.id}: ¥{req.cny_amount:,.0f} CNY → {req.pay_currency}\n"
            f"   Status: {req.status.value} | {req.created_at.strftime('%m/%d %H:%M')}\n\n"
        )

    await m.answer(text, parse_mode="Markdown")


# ============================================================================
# Cancel Handler
# ============================================================================

@router.message(StateFilter("*"), F.text == "❌ Cancel")
async def cancel_handler(m: types.Message, state: FSMContext):
    """Cancel any state."""
    current_state = await state.get_state()
    if current_state:
        await state.clear()
        await m.answer("Cancelled.", reply_markup=ReplyKeyboardRemove())
