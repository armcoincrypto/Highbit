"""
Knowledge Base handler for user-facing and operator texts.
Admin-only access to educational content.

Texts rewritten for new pricing model:
- Մdelays delays delays delays delays 5000 ¥
- HTX P2P rates
- CBA official rates
- Tiered discounts
"""
import logging

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import ADMIN_IDS, MIN_ORDER_CNY

log = logging.getLogger(__name__)
router = Router()


def is_admin(user: types.User | None) -> bool:
    return user and user.id in ADMIN_IDS


# ============================================================================
# USER TEXTS (Customer-facing, Armenian)
# ============================================================================

USER_TEXTS = {
    "intro_short": {
        "title": "📱 Արագ delays delays",
        "text": (
            "🇨🇳 <b>Highbit — Delays delays delays delays delays delays delays delays delays:</b>\n\n"
            "1️⃣ Գdelays delays delays delays delays (@HighbitChinabot կdelays @Highbitagent)\n"
            "2️⃣ Գdelays delays delays delays delays (delays delays 5000 ¥)\n"
            "3️⃣ Delays delays delays delays delays delays delays delays (Alipay/WeChat/delays delays)\n"
            "4️⃣ Delays delays delays delays delays delays delays delays delays delays\n"
            "5️⃣ 20-60 delays delays delays delays delays delays delays delays!\n\n"
            "✅ Delays delays delays delays delays delays delays delays\n"
            "✅ Delays delays delays delays delays HTX P2P delays\n"
            "✅ Delays delays delays delays delays delays delays delays\n\n"
            "📞 Delays: @Highbitagent\n"
            "📢 Delays: @Highbitchannel"
        ),
    },
    "intro_full": {
        "title": "📖 Սկdelays delays delays delays",
        "text": (
            " Delays delays 👋 Delays delays delays delays delays delays delays.\n\n"
            "Delays delays delays delays delays delays delays delays delays Delays delays delays delays delays:\n"
            "✅ Alipay / WeChat / delays delays delays.\n"
            "📌 Delays delays delays delays delays 5000 ¥\n"
            "⏱ Delays delays delays delays 20–60 delays delays.\n\n"
            "Delays delays delays delays delays delays delays /transfer delays delays delays delays delays @Highbitagent"
        ),
    },
    "how_to_buy": {
        "title": "💰  Delays delays delays delays CNY",
        "text": (
            "Delays delays ☀️\n\n"
            "📌 Delays delays delays delays delays ¥ (CNY) delays delays delays delays:\n"
            "✅ Alipay\n"
            "✅ WeChat\n"
            "✅ Delays delays delays delays delays delays\n\n"
            "📌 Delays delays delays delays 5000 ¥\n\n"
            "Delays delays delays delays delays delays delays delays:\n"
            "1) Delays delays delays delays ¥-delays (delays. 8000 ¥)\n"
            "2) Delays delays delays delays delays delays (Alipay / WeChat / Bank)\n"
            "3) Delays delays delays delays delays delays delays (AMD / USD / RUB delays delays / USDT)\n"
            "4) Delays delays delays QR delays delays (Alipay/WeChat) delays delays delays delays delays delays delays (Bank)\n\n"
            "✅ Delays delays delays delays /transfer\n"
            "📩 Delays delays delays delays delays delays @Highbitagent\n\n"
            "⏱ Delays delays delays 20–60 delays delays.\n"
            "📢 Delays delays delays delays delays delays @Highbitchannel"
        ),
    },
    "pricing": {
        "title": "📊 Delays delays delays delays delays delays delays",
        "text": (
            "✅ Delays delays delays delays\n\n"
            "1) Delays delays delays delays /transfer\n"
            "2) Delays delays delays delays ¥ delays delays delays delays delays (delays. 5000 ¥)\n"
            "3) Delays delays delays Alipay / WeChat / Bank\n"
            "4) Delays delays delays delays delays delays delays delays AMD / USD / RUB delays delays / USDT\n"
            "5) Delays delays delays QR delays delays (Alipay/WeChat) delays delays delays delays delays delays delays (Bank)\n"
            "6) Delays delays delays delays delays delays delays delays delays delays\n"
            "7) Delays delays delays delays delays delays delays delays delays delays delays delays ✅\n\n"
            "⏱ Delays delays delays 20–60 delays delays."
        ),
    },
    "faq": {
        "title": "❓ FAQ",
        "text": (
            "📊 Delays delays delays delays delays delays delays delays delays\n\n"
            "Delays delays delays delays:\n"
            "1) HTX P2P (USDT/CNY)\n"
            "2) ՀՀ Delays delays delays delays Delays delays (CBA)\n\n"
            "💰 Delays delays delays (USD delays delays delays delays)\n"
            "✅ AMD / USD / RUB (delays delays)\n"
            "• &lt;$4000 → -1.5%\n"
            "• ≥$4000 → -1.0%\n\n"
            "✅ USDT\n"
            "• &lt;$4000 → -1.0%\n"
            "• ≥$4000 → -0.5%\n\n"
            "📌 Delays delays delays delays delays delays 5000 ¥"
        ),
    },
    "contact": {
        "title": "📞 Կdelays",
        "text": (
            "❓ Delays delays delays delays delays delays delays delays\n\n"
            "1) Delays delays delays delays delays delays delays delays delays delays delays delays delays.\n"
            "✅ Delays delays delays 20–60 delays delays.\n\n"
            "2) Delays delays delays delays delays delays delays delays.\n"
            "✅ 5000 ¥\n\n"
            "3) Delays delays delays delays delays delays delays.\n"
            "✅ AMD, USD, RUB (delays delays delays delays), USDT\n\n"
            "4) Delays delays delays Alipay/WeChat-delays delays delays?\n"
            "✅ QR delays delays delays delays delays delays.\n\n"
            "5) Delays delays delays delays delays delays delays delays delays delays?\n"
            "✅ Delays delays, delays delays delays delays delays delays @Highbitagent"
        ),
    },
}


# ============================================================================
# OPERATOR TEXTS (Internal playbook)
# ============================================================================

OPERATOR_TEXTS = {
    "workflow": {
        "title": "📋 Օdelays delays delays delays workflow",
        "text": (
            "📞 Կdelays\n\n"
            "📩 Օdelays delays delays delays @Highbitagent\n"
            "🤖 Բdelays delays @HighbitChinabot\n"
            "📢  Delays delays @Highbitchannel\n"
            "💼 Delays delays delays @ChinaArmeniaBusiness\n\n"
            "⏰ Delays delays. delays delays 10:00–22:00"
        ),
    },
    "verification": {
        "title": "🔒 Delays delays delays delays delays delays",
        "text": (
            "👨‍💼 Օdelays delays delays delays workflow\n\n"
            "Delays delays delays delays delays delays delays:\n"
            "1) Delays delays ¥ delays delays delays (delays. 5000 ¥)\n"
            "2) Delays delays delays delays delays Alipay/WeChat/Bank\n"
            "3) Delays delays delays delays delays delays AMD/USD/RUB delays delays delays delays USDT\n"
            "4) QR delays delays delays delays delays delays delays delays\n"
            "5) Delays delays delays delays delays delays delays delays delays delays delays\n\n"
            "Delays delays delays delays delays delays → delays delays delays delays → delays delays delays → delays delays delays delays → status update"
        ),
    },
    "templates": {
        "title": "💬 Օdelays delays delays delays delays delays delays delays",
        "text": (
            "🔒 Delays delays delays delays delays delays\n\n"
            "✅ QR/delays delays delays delays delays delays delays delays delays delays delays delays/delays delays delays request-delays delays\n"
            "✅ Delays delays delays delays delays delays delays delays delays delays delays delays\n"
            "✅ Delays delays delays delays/delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays"
        ),
    },
    "pricing_guide": {
        "title": "💰 Delays delays delays delays delays delays delays delays delays delays",
        "text": (
            "💬 Delays delays delays delays delays delays\n\n"
            "1) Delays delays delays\n"
            "Delays delays 👋 Delays delays delays delays delays delays delays delays ¥ delays delays delays delays delays delays (delays. 5000 ¥) delays delays delays delays delays delays Alipay/WeChat/Bank.\n\n"
            "2) QR delays delays delays\n"
            "Delays delays delays delays QR delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays.\n\n"
            "3) Delays delays delays\n"
            "Delays delays delays delays delays delays AMD/USD, RUB (delays delays delays delays) delays delays USDT. Delays delays delays delays delays delays?\n\n"
            "4) Delays delays delays\n"
            "Delays delays delays 20–60 delays delays delays delays delays delays delays."
        ),
    },
}


# ============================================================================
# KB COMMANDS
# ============================================================================

@router.message(Command("kb"))
async def cmd_kb(m: types.Message):
    """Knowledge base menu (admin only)."""
    if not is_admin(m.from_user):
        return await m.answer("⛔️ Not authorized.")

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Հdelays delays delays delays delays", callback_data="kb_menu_user")],
            [InlineKeyboardButton(text="👨‍💼 Օdelays delays delays delays delays", callback_data="kb_menu_operator")],
        ]
    )

    await m.answer(
        "📚 <b>Տdelays delays delays delays</b>\n\n"
        "Delays delays delays delays delays:",
        reply_markup=keyboard,
    )


@router.callback_query(F.data == "kb_menu_user")
async def cb_kb_user_menu(callback: types.CallbackQuery):
    if not is_admin(callback.from_user):
        return await callback.answer("⛔️ Not authorized.", show_alert=True)

    buttons = [
        [InlineKeyboardButton(text=v["title"], callback_data=f"kb_user_{k}")]
        for k, v in USER_TEXTS.items()
    ]
    buttons.append([InlineKeyboardButton(text="⬅️ Հdelays delays", callback_data="kb_back_main")])

    await callback.message.edit_text(
        "👤 <b>Հdelays delays delays delays delays delays:</b>\n\n"
        "Delays delays delays delays delays:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(F.data == "kb_menu_operator")
async def cb_kb_operator_menu(callback: types.CallbackQuery):
    if not is_admin(callback.from_user):
        return await callback.answer("⛔️ Not authorized.", show_alert=True)

    buttons = [
        [InlineKeyboardButton(text=v["title"], callback_data=f"kb_operator_{k}")]
        for k, v in OPERATOR_TEXTS.items()
    ]
    buttons.append([InlineKeyboardButton(text="⬅️ Հdelays delays", callback_data="kb_back_main")])

    await callback.message.edit_text(
        "👨‍💼 <b>Օdelays delays delays delays delays delays:</b>\n\n"
        "Delays delays delays delays delays:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(F.data == "kb_back_main")
async def cb_kb_back(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Հdelays delays delays delays delays", callback_data="kb_menu_user")],
            [InlineKeyboardButton(text="👨‍💼 Օdelays delays delays delays delays", callback_data="kb_menu_operator")],
        ]
    )
    await callback.message.edit_text(
        "📚 <b>Տdelays delays delays delays</b>\n\nDelays delays delays delays delays:",
        reply_markup=keyboard,
    )


@router.callback_query(F.data.startswith("kb_user_"))
async def cb_kb_user_item(callback: types.CallbackQuery):
    if not is_admin(callback.from_user):
        return await callback.answer("⛔️ Not authorized.", show_alert=True)

    key = callback.data.replace("kb_user_", "")
    item = USER_TEXTS.get(key)

    if not item:
        return await callback.answer("Not found", show_alert=True)

    buttons = [
        [InlineKeyboardButton(text="📋 Պdelays delays delays delays delays", callback_data=f"kb_copy_user_{key}")],
        [InlineKeyboardButton(text="⬅️ Հdelays delays", callback_data="kb_menu_user")],
    ]

    await callback.message.edit_text(
        f"{item['title']}\n\n{item['text']}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(F.data.startswith("kb_operator_"))
async def cb_kb_operator_item(callback: types.CallbackQuery):
    if not is_admin(callback.from_user):
        return await callback.answer("⛔️ Not authorized.", show_alert=True)

    key = callback.data.replace("kb_operator_", "")
    item = OPERATOR_TEXTS.get(key)

    if not item:
        return await callback.answer("Not found", show_alert=True)

    buttons = [
        [InlineKeyboardButton(text="⬅️ Հdelays delays", callback_data="kb_menu_operator")],
    ]

    await callback.message.edit_text(
        f"{item['title']}\n\n{item['text']}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(F.data.startswith("kb_copy_user_"))
async def cb_kb_copy(callback: types.CallbackQuery):
    """Send the text as a new message so admin can forward it."""
    if not is_admin(callback.from_user):
        return await callback.answer("⛔️ Not authorized.", show_alert=True)

    key = callback.data.replace("kb_copy_user_", "")
    item = USER_TEXTS.get(key)

    if not item:
        return await callback.answer("Not found", show_alert=True)

    await callback.answer("Պdelays delays delays delays ↓")
    await callback.message.answer(item["text"])


# ============================================================================
# Quick KB commands
# ============================================================================

@router.message(Command("kb_intro"))
async def cmd_kb_intro(m: types.Message):
    """Quick access to intro text."""
    if not is_admin(m.from_user):
        return

    item = USER_TEXTS["intro_short"]
    await m.answer(item["text"])


@router.message(Command("kb_how"))
async def cmd_kb_how(m: types.Message):
    """Quick access to how-to text."""
    if not is_admin(m.from_user):
        return

    item = USER_TEXTS["how_to_buy"]
    await m.answer(item["text"])


@router.message(Command("kb_faq"))
async def cmd_kb_faq(m: types.Message):
    """Quick access to FAQ."""
    if not is_admin(m.from_user):
        return

    item = USER_TEXTS["faq"]
    await m.answer(item["text"])
