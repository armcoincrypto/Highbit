"""
Knowledge Base handler for user-facing and operator texts.
Admin-only access to educational content.
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
        "title": "📱 Ծdelays delays delays delays delays (delays delays)",
        "text": (
            "🇨🇳 **Highbit — Չdelays delays delays delays delays delays:**\n\n"
            "1️⃣ Գdelays delays delays delays delays delays (@HighbitChinabot)\n"
            "2️⃣ Նdelays delays delays delays delays delays delays delays delays\n"
            "3️⃣ Վdelays delays delays delays delays delays (AMD/USD/RUB/USDT)\n"
            "4️⃣ Մdelays delays delays delays delays delays delays delays delays delays\n"
            "5️⃣ Delays delays delays 20-60 delays delays delays delays delays delays\n\n"
            "✅ Delays delays delays delays delays\n"
            "✅ Delays delays delays delays delays delays delays\n"
            "✅ Delays delays delays delays delays delays delays delays\n\n"
            "📞 Օdelays delays delays: @Highbitagent"
        ),
    },
    "intro_full": {
        "title": "📖 Delays delays delays delays delays delays (delays delays delays)",
        "text": (
            "🇨🇳 **Highbit — Delays delays delays delays delays delays delays delays**\n\n"
            "Delays delays delays delays delays delays delays delays delays delays delays:\n"
            "• Alipay\n"
            "• WeChat Pay\n"
            "• Delays delays delays delays delays delays delays\n\n"
            "**Delays delays delays delays delays:**\n"
            f"• Delays delays delays delays: ¥{MIN_ORDER_CNY:,} CNY\n"
            "• Delays delays delays delays delays delays: AMD, USD, RUB, USDT\n"
            "• Delays delays delays delays delays delays delays delays delays\n"
            "• Delays delays delays delays delays: 20-60 delays delays\n\n"
            "**Delays delays delays delays delays delays:**\n"
            "• Delays delays delays delays delays delays delays delays delays delays delays\n"
            "• Delays delays delays delays delays delays delays delays delays delays delays\n"
            "• Delays delays delays delays delays delays delays delays delays delays delays delays\n\n"
            "**Delays delays delays delays:**\n"
            "1. /transfer — delays delays delays delays delays delays\n"
            "2. Delays delays delays delays delays delays delays CNY delays delays\n"
            "3. Delays delays delays delays delays (Alipay/WeChat/Bank)\n"
            "4. Delays delays delays delays delays delays (AMD/USD/RUB/USDT)\n"
            "5. Delays delays delays delays delays delays QR delays delays delays\n"
            "6. Delays delays delays delays delays delays delays delays delays delays delays\n\n"
            "📞 Delays delays delays: @Highbitagent\n"
            "📢 Delays delays delays: @Highbitchannel"
        ),
    },
    "how_to_buy": {
        "title": "💰 Delays delays delays delays delays delays CNY delays delays delays",
        "text": (
            "**Delays delays delays delays delays delays CNY delays delays delays:**\n\n"
            "1️⃣ **Delays delays delays delays delays delays delays delays**\n"
            "   Delays delays delays /transfer delays delays delays @HighbitChinabot\n\n"
            "2️⃣ **Delays delays delays delays delays delays delays delays delays**\n"
            "   • Delays delays CNY delays delays delays\n"
            "   • Delays delays delays delays delays (Alipay/WeChat/Bank)\n"
            "   • Delays delays delays delays delays delays delays delays (AMD/USD/RUB/USDT)\n"
            "   • Delays delays delays delays delays delays QR delays delays delays\n\n"
            "3️⃣ **Delays delays delays delays delays delays delays delays**\n"
            "   • AMD/USD delays delays delays — delays delays delays delays delays delays delays delays delays\n"
            "   • RUB delays delays delays — delays delays delays delays delays delays delays\n"
            "   • USDT — delays delays delays delays delays delays delays delays\n\n"
            "4️⃣ **Delays delays delays delays delays delays delays delays**\n"
            "   20-60 delays delays delays delays delays delays delays delays delays delays delays\n\n"
            "✅ Delays delays delays delays delays delays\n"
            "✅ Delays delays delays delays delays delays delays delays delays delays"
        ),
    },
    "pricing": {
        "title": "📊 Delays delays delays delays delays delays delays delays delays",
        "text": (
            "**Delays delays delays delays delays delays delays delays delays:**\n\n"
            "Delays delays delays delays delays delays delays delays HTX P2P delays delays delays delays delays delays\n\n"
            "**Delays delays delays:**\n"
            "• $4,000+ USD delays delays delays delays: −1.0% (FIAT) delays delays −0.5% (USDT)\n"
            "• $4,000 delays delays delays delays delays: −1.5% (FIAT) delays delays −1.0% (USDT)\n\n"
            f"**Delays delays delays delays delays:** ¥{MIN_ORDER_CNY:,} CNY\n\n"
            "**Delays delays delays delays:**\n"
            "• HTX P2P — USDT/CNY delays delays delays delays (delays delays delays delays delays delays delays)\n"
            "• CBA — Delays delays delays delays delays delays delays delays delays delays (AMD delays delays delays delays delays delays)\n\n"
            "Delays delays delays delays delays delays delays delays delays delays delays delays delays delays."
        ),
    },
    "faq": {
        "title": "❓ Delays delays delays delays delays delays delays delays",
        "text": (
            "**❓ Delays delays delays delays delays delays delays delays:**\n\n"
            "**Q: Delays delays delays delays delays delays delays delays delays?**\n"
            "A: 20-60 delays delays, delays delays delays delays delays delays delays delays delays delays.\n\n"
            "**Q: Delays delays delays delays delays delays delays delays delays delays?**\n"
            f"A: Delays delays delays delays delays ¥{MIN_ORDER_CNY:,} CNY delays (≈ $700 USD).\n\n"
            "**Q: Delays delays delays delays delays delays delays delays delays delays?**\n"
            "A: AMD delays delays (delays delays delays), USD delays delays, RUB delays delays (delays delays delays delays), USDT.\n\n"
            "**Q: Delays delays delays delays delays delays delays delays delays delays?**\n"
            "A: Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays.\n\n"
            "**Q: Delays delays delays delays delays delays delays delays delays delays?**\n"
            "A: Delays, delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays."
        ),
    },
}


# ============================================================================
# OPERATOR TEXTS (Internal playbook)
# ============================================================================

OPERATOR_TEXTS = {
    "workflow": {
        "title": "📋 Օdelays delays delays delays delays delays delays",
        "text": (
            "**Օdelays delays delays delays delays delays delays — delays delays delays delays delays delays:**\n\n"
            "**1️⃣ Delays delays delays delays delays delays delays:**\n"
            "   • Delays delays delays: delays delays delays CNY delays delays delays?\n"
            "   • Delays delays delays delays delays delays: delays delays delays delays? (Delays delays, delays delays, delays delays delays delays delays)\n"
            "   • Delays delays delays delays delays delays delays: AMD, USD, RUB, USDT?\n"
            "   • Delays delays delays delays: Alipay, WeChat, delays delays delays delays delays delays?\n"
            "   • Delays delays delays delays delays delays: QR delays delays delays delays delays delays delays delays delays\n\n"
            "**2️⃣ Delays delays delays delays delays delays:**\n"
            "   • /request <id> — delays delays delays delays delays delays delays delays delays delays\n"
            "   • Delays delays delays delays delays delays delays delays delays delays delays delays delays delays\n"
            "   • Delays delays delays delays delays delays delays delays delays delays delays delays delays delays\n\n"
            "**3️⃣ Delays delays delays delays delays delays:**\n"
            "   • Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays\n"
            "   • Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays\n"
            "   • Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays\n\n"
            "**4️⃣ Delays delays delays delays delays delays:**\n"
            "   • Delays delays delays delays delays delays delays delays delays delays delays delays\n"
            "   • Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays\n"
            "   • Delays delays delays delays delays delays delays delays delays delays delays delays delays"
        ),
    },
    "verification": {
        "title": "🔒 Delays delays delays delays delays delays delays delays",
        "text": (
            "**Delays delays delays delays delays delays delays delays delays delays delays:**\n\n"
            "✅ **Delays delays delays delays delays delays:**\n"
            "   • Delays delays delays delays delays delays delays delays delays delays delays\n"
            "   • Delays delays delays delays delays delays delays delays delays delays delays delays\n"
            "   • Delays delays delays delays delays delays delays delays delays delays delays delays\n\n"
            "⚠️ **Delays delays delays delays delays delays:**\n"
            "   • Delays delays delays delays delays delays delays delays delays delays delays delays delays delays\n"
            "   • QR delays delays delays delays delays delays delays delays delays delays delays\n"
            "   • Delays delays delays delays delays delays delays delays delays delays delays delays delays\n\n"
            "❌ **Delays delays delays delays delays delays delays:**\n"
            "   • Delays delays delays delays delays delays delays delays delays delays delays delays delays\n"
            "   • Delays delays delays delays delays delays delays delays delays delays delays delays delays\n"
            "   • Delays delays delays delays delays delays delays delays delays delays delays delays delays delays"
        ),
    },
    "templates": {
        "title": "💬 Delays delays delays delays delays delays delays delays delays delays",
        "text": (
            "**Delays delays delays delays delays delays delays delays delays delays delays delays:**\n\n"
            "📝 **Delays delays delays delays delays delays:**\n"
            "```\n"
            "Delays delays delays Highbit delays delays! Delays delays delays delays delays delays delays delays delays delays.\n"
            "```\n\n"
            "📝 **Delays delays delays delays delays delays delays:**\n"
            "```\n"
            "Delays delays delays delays delays delays delays delays delays delays delays delays delays:\n"
            "• Delays delays CNY delays delays delays\n"
            "• Delays delays delays delays delays (Alipay/WeChat/Bank)\n"
            "• Delays delays delays delays delays delays delays delays\n"
            "• Delays delays delays delays delays delays delays\n"
            "```\n\n"
            "📝 **Delays delays delays delays delays delays:**\n"
            "```\n"
            "✅ Delays delays delays delays delays delays delays! Delays delays delays delays delays delays delays 20-60 delays delays delays delays.\n"
            "```\n\n"
            "📝 **Delays delays delays delays delays delays delays:**\n"
            "```\n"
            "🚀 Delays delays delays delays delays delays delays delays! Delays delays delays delays delays delays delays delays delays delays delays delays delays.\n"
            "```"
        ),
    },
    "pricing_explained": {
        "title": "💰 Delays delays delays delays delays delays — delays delays delays delays delays",
        "text": (
            "**Delays delays delays delays delays delays delays delays delays delays delays delays:**\n\n"
            "**1. Delays delays delays delays delays:**\n"
            "   • Delays delays delays delays delays HTX P2P USDT/CNY delays delays delays delays delays\n"
            "   • Delays delays delays delays delays delays delays delays delays delays delays delays delays\n\n"
            "**2. Delays delays delays delays delays:**\n"
            "   • Delays delays delays delays delays CBA (Delays delays delays delays delays) delays delays delays delays\n"
            "   • CNY → USD delays delays delays delays delays delays delays delays delays delays delays delays\n\n"
            "**3. Delays delays delays delays delays delays:**\n"
            "   • USD $4,000+ delays delays delays: −1.0% (FIAT), −0.5% (USDT)\n"
            "   • USD $4,000 delays delays delays delays: −1.5% (FIAT), −1.0% (USDT)\n\n"
            "**4. Delays delays delays delays delays:**\n"
            "   • USDT: delays delays delays delays delays delays USDT delays delays\n"
            "   • USD: delays delays delays delays delays (USDT ≈ USD)\n"
            "   • AMD: delays delays CBA USD/AMD delays delays delays delays delays delays\n"
            "   • RUB: delays delays CBA delays delays delays delays delays delays delays delays"
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
            [InlineKeyboardButton(text="👤 User Texts", callback_data="kb_menu_user")],
            [InlineKeyboardButton(text="👨‍💼 Operator Guide", callback_data="kb_menu_operator")],
        ]
    )

    await m.answer(
        "📚 **Knowledge Base**\n\n"
        "Choose a category:",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "kb_menu_user")
async def cb_kb_user_menu(callback: types.CallbackQuery):
    if not is_admin(callback.from_user):
        return await callback.answer("⛔️ Not authorized.", show_alert=True)

    buttons = [
        [InlineKeyboardButton(text=v["title"], callback_data=f"kb_user_{k}")]
        for k, v in USER_TEXTS.items()
    ]
    buttons.append([InlineKeyboardButton(text="⬅️ Back", callback_data="kb_back_main")])

    await callback.message.edit_text(
        "👤 **User Texts**\n\nSelect a topic to view:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "kb_menu_operator")
async def cb_kb_operator_menu(callback: types.CallbackQuery):
    if not is_admin(callback.from_user):
        return await callback.answer("⛔️ Not authorized.", show_alert=True)

    buttons = [
        [InlineKeyboardButton(text=v["title"], callback_data=f"kb_operator_{k}")]
        for k, v in OPERATOR_TEXTS.items()
    ]
    buttons.append([InlineKeyboardButton(text="⬅️ Back", callback_data="kb_back_main")])

    await callback.message.edit_text(
        "👨‍💼 **Operator Guide**\n\nSelect a topic to view:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "kb_back_main")
async def cb_kb_back(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 User Texts", callback_data="kb_menu_user")],
            [InlineKeyboardButton(text="👨‍💼 Operator Guide", callback_data="kb_menu_operator")],
        ]
    )
    await callback.message.edit_text(
        "📚 **Knowledge Base**\n\nChoose a category:",
        reply_markup=keyboard,
        parse_mode="Markdown",
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
        [InlineKeyboardButton(text="📋 Copy to send", callback_data=f"kb_copy_user_{key}")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="kb_menu_user")],
    ]

    await callback.message.edit_text(
        f"{item['title']}\n\n{item['text']}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown",
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
        [InlineKeyboardButton(text="⬅️ Back", callback_data="kb_menu_operator")],
    ]

    await callback.message.edit_text(
        f"{item['title']}\n\n{item['text']}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown",
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

    await callback.answer("Sent as new message ↓")
    await callback.message.answer(item["text"], parse_mode="Markdown")


# ============================================================================
# Quick KB commands
# ============================================================================

@router.message(Command("kb_intro"))
async def cmd_kb_intro(m: types.Message):
    """Quick access to intro text."""
    if not is_admin(m.from_user):
        return

    item = USER_TEXTS["intro_short"]
    await m.answer(item["text"], parse_mode="Markdown")


@router.message(Command("kb_how"))
async def cmd_kb_how(m: types.Message):
    """Quick access to how-to text."""
    if not is_admin(m.from_user):
        return

    item = USER_TEXTS["how_to_buy"]
    await m.answer(item["text"], parse_mode="Markdown")
