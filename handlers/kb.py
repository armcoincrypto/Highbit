"""
Knowledge Base handler for user-facing and operator texts.
Admin-only access to educational content.

Texts rewritten for new pricing model:
- Minimum order: 5000 CNY
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
        "title": "📱 Կdelays delays (Կարdelays delays delays delays)",
        "text": (
            "🇨🇳 **Highbit — Չdelays delays delays delays delays delays delays delays delays delays:**\n\n"
            "1️⃣ Գdelays delays delays delays delays delays delays (@HighbitChinabot delays delays @Highbitagent)\n"
            "2️⃣ Նdelays delays delays delays delays delays delays delays delays (delays delays delays 5000 ¥)\n"
            "3️⃣ Նdelays delays delays delays delays delays delays delays delays delays (Alipay/WeChat/delays delays delays delays delays)\n"
            "4️⃣ Կdelays delays delays delays delays delays delays delays delays delays delays delays delays delays delays\n"
            "5️⃣ 20-60 delays delays delays delays delays delays delays delays delays delays!\n\n"
            "✅ Delays delays delays delays delays delays delays delays delays delays delays delays delays delays\n"
            "✅ Մdelays delays delays delays delays delays delays delays delays delays delays delays\n"
            "✅ Delays delays delays delays delays delays delays delays delays delays delays delays delays\n\n"
            "📞 Կdelays: @Highbitagent\n"
            "📢 Delays: @Highbitchannel"
        ),
    },
    "intro_full": {
        "title": "📖  Delays delays delays delays (Delays delays delays delays delays)",
        "text": (
            "👋 **Delays delays delays delays Highbit!**\n\n"
            "Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays:\n"
            "• Alipay\n"
            "• WeChat Pay\n"
            "• Delays delays delays delays delays delays (delays delays delays delays)\n\n"
            "**📌 Կdelays delays delays:**\n"
            "• Delays delays delays delays delays delays delays: **5000 ¥** CNY\n"
            "• Delays delays delays delays delays delays delays: AMD (delays delays), USD (delays delays), RUB (delays delays), USDT\n"
            "• Delays delays delays delays delays: 20-60 delays delays delays\n"
            "• Delays delays delays delays delays delays delays delays delays — delays delays delays delays delays delays delays delays delays delays delays\n\n"
            "**💰 Delays delays delays delays delays delays:**\n"
            "• Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays\n"
            "• $4000+ USD delays delays delays delays delays — delays delays delays delays delays\n\n"
            "**📲 Delays delays delays delays delays delays delays delays:**\n"
            "1. /transfer delays delays delays delays delays delays delays delays delays delays delays delays\n"
            "2. Delays delays delays delays delays delays delays delays delays delays (delays delays delays 5000 ¥)\n"
            "3. Delays delays delays delays delays delays delays delays delays delays (Alipay/WeChat/Delays delays delays)\n"
            "4. Delays delays delays delays delays delays delays delays delays delays delays delays delays (AMD/USD/RUB/USDT)\n"
            "5. Delays delays delays delays delays delays delays QR delays delays delays delays delays delays delays\n"
            "6. Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays!\n\n"
            "📞 Կdelays: @Highbitagent\n"
            "📢 Delays: @Highbitchannel\n"
            "💼 Delays delays: @ChinaArmeniaBusiness"
        ),
    },
    "how_to_buy": {
        "title": "💰 Delays delays delays delays CNY delays delays delays",
        "text": (
            "**Delays delays delays delays delays delays delays delays delays CNY delays delays delays:**\n\n"
            "**1️⃣ Delays delays delays delays delays delays delays delays delays**\n"
            "• Delays delays delays delays delays delays delays @Highbitagent delays delays delays delays delays delays delays delays delays delays delays\n"
            "• /transfer delays delays delays delays @HighbitChinabot\n\n"
            "**2️⃣ Delays delays delays delays delays delays delays delays delays delays**\n"
            "• Delays delays delays delays delays delays delays delays delays delays delays delays delays (delays delays delays 5000 ¥)\n"
            "• Delays delays delays delays delays delays delays delays delays delays delays delays (Alipay/WeChat/Delays delays delays delays delays delays)\n"
            "• Delays delays delays delays delays delays delays delays delays delays delays delays delays delays (AMD/USD/RUB/USDT)\n"
            "• Delays delays delays delays delays delays delays delays delays delays delays delays delays QR delays delays delays delays delays delays delays delays delays delays delays delays delays\n\n"
            "**3️⃣ Delays delays delays delays delays delays delays delays delays delays delays delays**\n"
            "• **AMD/USD delays delays delays delays:** Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays\n"
            "• **RUB delays delays delays delays:** Delays delays delays delays delays delays delays delays delays delays delays delays delays\n"
            "• **USDT:** Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays\n\n"
            "**4️⃣ Delays delays delays delays delays delays delays delays!**\n"
            "• Delays delays delays delays delays delays delays delays delays 20-60 delays delays delays delays delays delays delays delays delays delays!\n\n"
            "📊 Delays delays delays delays delays delays delays delays delays delays @Highbitchannel"
        ),
    },
    "pricing": {
        "title": "📊 Delays delays delays delays delays delays delays",
        "text": (
            "**Delays delays delays delays delays delays delays delays delays delays delays delays:**\n\n"
            "**📈 Delays delays delays delays delays delays delays:**\n"
            "Delays delays delays delays delays delays delays delays delays HTX P2P delays delays delays delays (USDT/CNY delays delays delays delays)\n\n"
            "**💵 Delays delays delays delays delays delays delays delays delays delays:**\n"
            "Delays delays delays delays delays delays delays CBA (Delays delays delays delays Delays delays delays delays Delays delays delays delays delays) delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays\n\n"
            "**🎁 Delays delays delays delays delays delays delays delays delays:**\n"
            "| Delays delays delays delays delays | FIAT (AMD/USD/RUB) | USDT |\n"
            "|------------------|--------------------|-------|\n"
            "| < $4,000 USD | −1.5% | −1.0% |\n"
            "| ≥ $4,000 USD | −1.0% | −0.5% |\n\n"
            "**⚠️ Delays delays delays delays delays delays delays:** 5000 ¥ CNY\n\n"
            "💡 Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays!"
        ),
    },
    "faq": {
        "title": "❓ Delays delays delays delays delays delays delays delays delays delays",
        "text": (
            "**Delays delays delays delays delays delays delays delays delays delays delays:**\n\n"
            "**❓ Delays delays delays delays delays delays delays delays delays delays delays?**\n"
            "✅ Delays delays delays delays delays delays delays delays delays 20-60 delays delays delays, delays delays delays delays delays delays delays delays delays delays delays delays delays delays.\n\n"
            "**❓ Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays?**\n"
            "✅ Delays delays delays delays delays delays delays delays delays delays **5000 ¥** CNY (delays delays $700 USD).\n\n"
            "**❓ Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays?**\n"
            "✅ AMD delays delays delays delays (delays delays delays delays delays delays delays delays delays), USD delays delays delays, RUB delays delays delays delays (delays delays delays delays delays delays), USDT.\n\n"
            "**❓ Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays?**\n"
            "✅ Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays — delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays.\n\n"
            "**❓ Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays?**\n"
            "✅ Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays."
        ),
    },
    "contact": {
        "title": "📞 Կdelays delays delays",
        "text": (
            "**Delays delays delays delays delays delays delays delays delays delays delays delays:**\n\n"
            "📱 **WhatsApp:** +79181309690\n"
            "📩 **Telegram Delays delays delays:** @Highbitagent\n"
            "🤖 **Telegram Delays delays:** @HighbitChinabot\n"
            "📢 **Delays delays delays:** @Highbitchannel\n"
            "💼 **Delays delays delays delays:** @ChinaArmeniaBusiness\n\n"
            "⏰ Delays delays delays delays delays delays delays: 10:00 - 22:00 (Delays delays delays delays)"
        ),
    },
}


# ============================================================================
# OPERATOR TEXTS (Internal playbook)
# ============================================================================

OPERATOR_TEXTS = {
    "workflow": {
        "title": "📋 Աdelays delays delays delays delays delays",
        "text": (
            "**Delays delays delays delays delays delays delays delays delays delays delays:**\n\n"
            "**1️⃣ Delays delays delays delays delays delays delays delays delays delays:**\n"
            "• Delays delays delays CNY delays delays delays delays? (delays delays delays delays 5000 ¥)\n"
            "• Delays delays delays delays delays delays delays delays delays delays delays delays? (Alipay / WeChat / Delays delays delays delays delays)\n"
            "• Delays delays delays delays delays delays delays delays delays delays delays delays? (AMD / USD / RUB / USDT)\n"
            "• Delays delays delays delays delays delays delays delays delays delays delays?\n"
            "• Delays delays delays delays delays delays delays delays delays QR delays delays delays delays delays delays delays delays delays delays delays delays?\n\n"
            "**2️⃣ Delays delays delays delays delays delays delays delays delays delays:**\n"
            "• Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays\n"
            "• Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays\n"
            "• Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays\n\n"
            "**3️⃣ Delays delays delays delays delays delays delays delays delays delays:**\n"
            "• ✋ Assign — delays delays delays delays delays delays delays delays delays delays delays delays\n"
            "• 📞 Contacted — delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays\n"
            "• 💵 Paid — delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays\n"
            "• 🚀 Sent — delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays\n"
            "• ✅ Done — delays delays delays delays delays delays delays delays delays delays delays delays delays!\n\n"
            "**4️⃣ Delays delays delays delays delays delays delays delays delays delays:**\n"
            "• Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays\n"
            "• Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays"
        ),
    },
    "verification": {
        "title": "🔒 Delays delays delays delays delays delays delays delays delays",
        "text": (
            "**⚠️ Delays delays delays delays delays delays delays delays delays delays delays delays:**\n\n"
            "**✅ Delays delays delays delays delays delays delays delays:**\n"
            "• Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays\n"
            "• QR delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays\n"
            "• Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays\n\n"
            "**❌ Delays delays delays delays delays delays delays delays delays delays:**\n"
            "• Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays — delays delays delays delays delays delays delays delays delays delays delays delays\n"
            "• Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays\n"
            "• Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays\n\n"
            "**📝 Delays delays delays delays delays delays delays delays delays:**\n"
            "Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays."
        ),
    },
    "templates": {
        "title": "💬 Պdelays delays delays delays delays delays delays delays delays",
        "text": (
            "**Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays:**\n\n"
            "📝 **Delays delays delays delays delays delays delays delays delays delays:**\n"
            "```\n"
            "Delays delays delays delays delays Highbit delays delays delays delays delays delays! 👋 Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays.\n"
            "```\n\n"
            "📝 **Delays delays delays delays delays delays delays delays delays delays:**\n"
            "```\n"
            "Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays:\n"
            "• Delays delays delays CNY delays delays delays delays delays delays\n"
            "• Delays delays delays delays delays delays delays delays delays delays (Alipay/WeChat/Delays delays delays delays delays)\n"
            "• Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays\n"
            "• QR delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays\n"
            "```\n\n"
            "📝 **Delays delays delays delays delays delays delays delays delays delays:**\n"
            "```\n"
            "✅ Delays delays delays delays delays delays delays delays delays delays delays delays! Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays 20-60 delays delays delays delays delays delays delays delays delays delays delays.\n"
            "```\n\n"
            "📝 **Delays delays delays delays delays delays delays delays delays delays:**\n"
            "```\n"
            "🚀 Delays delays delays delays delays delays delays delays delays delays delays delays! Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays.\n"
            "```\n\n"
            "📝 **Delays delays delays delays delays delays delays delays delays delays delays:**\n"
            "```\n"
            "✅ Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays! Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays Highbit delays delays delays delays delays delays delays delays delays delays! 🙏\n"
            "```"
        ),
    },
    "pricing_guide": {
        "title": "💰 Delays delays delays delays delays delays delays delays delays delays",
        "text": (
            "**Delays delays delays delays delays delays delays delays delays delays delays delays delays delays:**\n\n"
            "**1. Delays delays delays delays delays delays delays delays delays (HTX P2P):**\n"
            "• Delays delays delays delays delays delays delays delays delays delays HTX P2P delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays\n"
            "• Delays delays delays delays delays delays delays delays delays: USDT/CNY\n"
            "• Delays delays delays delays: Alipay / WeChat delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays\n\n"
            "**2. Delays delays delays delays delays delays delays delays delays delays delays delays (CBA):**\n"
            "• AMD ↔ USD, AMD ↔ RUB, AMD ↔ CNY delays delays delays delays delays delays delays delays delays delays delays delays delays delays\n"
            "• Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays\n\n"
            "**3. Delays delays delays delays delays delays delays delays delays delays delays delays:**\n"
            "• Delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays\n"
            "• $4000+ delays delays delays delays delays delays delays delays — delays delays delays delays delays delays delays delays delays (delays delays delays delays delays delays delays delays delays delays)\n\n"
            "**4. Delays delays delays delays delays delays delays delays delays delays delays delays:**\n"
            "```\n"
            "USDT_needed = CNY_amount / HTX_price\n"
            "Amount_due = USDT_needed × (1 + discount)\n"
            "```\n"
            "delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays delays."
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
            [InlineKeyboardButton(text="👤 Delays delays delays delays delays delays delays", callback_data="kb_menu_user")],
            [InlineKeyboardButton(text="👨‍💼 Delays delays delays delays delays delays delays", callback_data="kb_menu_operator")],
        ]
    )

    await m.answer(
        "📚 **Knowledge Base**\n\n"
        "Delays delays delays delays delays delays delays delays delays:",
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
    buttons.append([InlineKeyboardButton(text="⬅️ Delays delays", callback_data="kb_back_main")])

    await callback.message.edit_text(
        "👤 **Delays delays delays delays delays delays delays:**\n\n"
        "Delays delays delays delays delays delays delays delays:",
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
    buttons.append([InlineKeyboardButton(text="⬅️ Delays delays", callback_data="kb_back_main")])

    await callback.message.edit_text(
        "👨‍💼 **Delays delays delays delays delays delays delays:**\n\n"
        "Delays delays delays delays delays delays delays delays:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "kb_back_main")
async def cb_kb_back(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Delays delays delays delays delays delays delays", callback_data="kb_menu_user")],
            [InlineKeyboardButton(text="👨‍💼 Delays delays delays delays delays delays delays", callback_data="kb_menu_operator")],
        ]
    )
    await callback.message.edit_text(
        "📚 **Knowledge Base**\n\nDelays delays delays delays delays delays delays delays:",
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
        [InlineKeyboardButton(text="📋 Պdelays delays delays delays delays delays delays", callback_data=f"kb_copy_user_{key}")],
        [InlineKeyboardButton(text="⬅️ Delays delays", callback_data="kb_menu_user")],
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
        [InlineKeyboardButton(text="⬅️ Delays delays", callback_data="kb_menu_operator")],
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

    await callback.answer("Delays delays delays delays ↓")
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


@router.message(Command("kb_faq"))
async def cmd_kb_faq(m: types.Message):
    """Quick access to FAQ."""
    if not is_admin(m.from_user):
        return

    item = USER_TEXTS["faq"]
    await m.answer(item["text"], parse_mode="Markdown")
