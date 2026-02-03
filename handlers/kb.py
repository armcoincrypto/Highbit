"""
Knowledge Base handler for user-facing and operator texts.
Admin-only access to educational content.

Pricing model references:
- Minimum transfer: 5000 ¥ (CNY)
- HTX P2P rates (USDT/CNY)
- CBA official rates (AMD/USD/RUB)
- Tiered discounts
"""
from __future__ import annotations

import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import ADMIN_IDS, MIN_ORDER_CNY

log = logging.getLogger(__name__)
router = Router()


def is_admin(user: types.User | None) -> bool:
    return bool(user) and user.id in ADMIN_IDS


# ============================================================================
# USER TEXTS (Customer-facing, Armenian)
# ============================================================================
USER_TEXTS: dict[str, dict[str, str]] = {
    "intro_short": {
        "title": "📱 Արագ ուղեցույց",
        "text": (
            "🇨🇳 <b>Highbit — փոխանցումներ դեպի Չինաստան</b>\n\n"
            "1️⃣ Գրեք մեզ՝ @Highbitagent (կամ բացեք հայտ՝ <code>/transfer</code>)\n"
            f"2️⃣ Գրեք գումարի չափը (մին․ <b>{MIN_ORDER_CNY} ¥</b>)\n"
            "3️⃣ Ընտրեք մեթոդը՝ <b>Alipay / WeChat / Bank</b>\n"
            "4️⃣ Ուղարկեք QR կոդը (Alipay/WeChat) կամ բանկային տվյալները (Bank)\n"
            "5️⃣ Ստացեք հաշվարկը → վճարեք → մենք կատարում ենք փոխանցումը ✅\n\n"
            "⏱ Սովորաբար պատրաստ է <b>20–60 րոպեում</b>\n"
            "📢 Թարմ տեղեկություն՝ @Highbitchannel\n"
            "📞 Օպերատոր՝ @Highbitagent"
        ),
    },
    "intro_full": {
        "title": "📖 Սկսելու ուղեցույց",
        "text": (
            "Ողջույն 👋\n\n"
            "Մենք օգնում ենք ուղարկել <b>¥ (CNY)</b> դեպի Չինաստան՝\n"
            "✅ Alipay\n"
            "✅ WeChat\n"
            "✅ Չինական բանկային հաշիվ\n\n"
            f"📌 <b>Մինիմալ փոխանցում՝ {MIN_ORDER_CNY} ¥</b>\n"
            "⏱ Սովորաբար պատրաստ է 20–60 րոպեում։\n\n"
            "<b>Ինչպես սկսել</b>\n"
            "1) Բացեք հայտ՝ <code>/transfer</code>\n"
            "2) Կամ գրեք օպերատորին՝ @Highbitagent\n\n"
            "📢 Ալիք՝ @Highbitchannel"
        ),
    },
    "how_to_buy": {
        "title": "💰 Ինչպես ուղարկել CNY",
        "text": (
            "<b>Քայլ առ քայլ</b>\n\n"
            "1) Բացեք հայտ՝ <code>/transfer</code>\n"
            f"2) Գրեք՝ քանի ¥ եք ուզում ուղարկել (մին․ <b>{MIN_ORDER_CNY} ¥</b>)\n"
            "3) Ընտրեք մեթոդը՝ Alipay / WeChat / Bank\n"
            "4) Նշեք՝ ինչով եք վճարում՝ AMD / USD / RUB (քարտով) / USDT\n"
            "5) Ուղարկեք QR կոդը (Alipay/WeChat) կամ բանկային տվյալները (Bank)\n"
            "6) Ստացեք հաշվարկը և հաստատեք\n"
            "7) Վճարումից հետո՝ մենք կատարում ենք փոխանցումը ✅\n\n"
            "⏱ Սովորաբար՝ 20–60 րոպե։"
        ),
    },
    "pricing": {
        "title": "📊 Փոխարժեք և հաշվարկ",
        "text": (
            "<b>Ինչպես ենք հաշվում փոխարժեքը</b>\n\n"
            "<b>Աղբյուրներ</b>\n"
            "1) HTX P2P (USDT/CNY)\n"
            "2) ՀՀ Կենտրոնական Բանկ (CBA) — պաշտոնական փոխարժեքներ\n\n"
            "<b>Զեղչեր (USD համարժեքով)</b>\n"
            "✅ AMD / USD / RUB (քարտով)\n"
            "• <$4000 → -1.5%\n"
            "• ≥$4000 → -1.0%\n\n"
            "✅ USDT\n"
            "• <$4000 → -1.0%\n"
            "• ≥$4000 → -0.5%\n\n"
            f"📌 Մինիմալ փոխանցում՝ <b>{MIN_ORDER_CNY} ¥</b>"
        ),
    },
    "faq": {
        "title": "❓ FAQ",
        "text": (
            "<b>Հաճախ տրվող հարցեր</b>\n\n"
            "<b>1) Քանի՞ րոպեում է պատրաստ լինում փոխանցումը</b>\n"
            "✅ Սովորաբար 20–60 րոպեում։\n\n"
            "<b>2) Ո՞րն է մինիմալ գումարը</b>\n"
            f"✅ {MIN_ORDER_CNY} ¥\n\n"
            "<b>3) Ինչով կարող եմ վճարել</b>\n"
            "✅ AMD, USD, RUB (միայն քարտով), USDT\n\n"
            "<b>4) Ի՞նչ է պետք Alipay/WeChat-ի համար</b>\n"
            "✅ QR կոդը պարտադիր է։\n\n"
            "<b>5) Կարո՞ղ եմ մեծ ծավալով անել</b>\n"
            "✅ Այո, գրեք օպերատորին՝ @Highbitagent"
        ),
    },
    "contact": {
        "title": "📞 Կապ",
        "text": (
            "<b>Կապ մեզ հետ</b>\n\n"
            "📩 Օպերատոր՝ @Highbitagent\n"
            "🤖 Բոթ՝ @HighbitChinabot\n"
            "📢 Ալիք՝ @Highbitchannel\n"
            "💼 Համայնք՝ @ChinaArmeniaBusiness\n\n"
            "⏰ Աշխ. ժամեր՝ 10:00–22:00"
        ),
    },
}


# ============================================================================
# OPERATOR TEXTS (Internal playbook)
# ============================================================================
OPERATOR_TEXTS: dict[str, dict[str, str]] = {
    "workflow": {
        "title": "📋 Օպերատորի workflow",
        "text": (
            "<b>Օպերատորի սցենար</b>\n\n"
            "Սկզբում հարցրու՝\n"
            f"1) Քանի ¥ է ուզում (մին․ {MIN_ORDER_CNY} ¥)\n"
            "2) Ո՞ր մեթոդով՝ Alipay / WeChat / Bank\n"
            "3) Ինչով է վճարում՝ AMD / USD / RUB քարտով / USDT\n"
            "4) QR կամ բանկային տվյալներ\n"
            "5) Երբ է ուզում անել փոխանցումը\n\n"
            "Հետո՝ հաշվարկ → հաստատում → վճարում → փոխանցում → status update"
        ),
    },
    "verification": {
        "title": "🔒 Անվտանգություն",
        "text": (
            "<b>Անվտանգության կանոններ</b>\n\n"
            "✅ QR/բանկ տվյալները պահիր միայն այս չաթում / բոթի request-ում\n"
            "✅ Չփոխանցել երրորդ կողմի\n"
            "✅ Կասկածելի կամ անսովոր մեծ գործարքների դեպքում՝ escalate ղեկավարին\n"
            "✅ Եթե հաճախորդը շտապեցնում է/չի տրամադրում տվյալները՝ կանգնեցրու գործընթացը"
        ),
    },
    "templates": {
        "title": "💬 Օպերատորի շաբլոններ",
        "text": (
            "<b>Շաբլոններ</b>\n\n"
            "<b>1) Սկիզբ</b>\n"
            f"Ողջույն 👋 Խնդրում եմ գրեք՝ քանի ¥ եք ուզում ուղարկել (մին․ {MIN_ORDER_CNY} ¥) "
            "և մեթոդը՝ Alipay/WeChat/Bank։\n\n"
            "<b>2) QR խնդրել</b>\n"
            "Կուղարկե՞ք QR կոդը կամ բանկային տվյալները՝ հաշվարկ անելու համար։\n\n"
            "<b>3) Վճարում</b>\n"
            "Կարող եք վճարել AMD/USD, RUB (միայն քարտով) կամ USDT։ Ո՞րն է հարմար։\n\n"
            "<b>4) Ժամկետ</b>\n"
            "Սովորաբար 20–60 րոպեում պատրաստ է։"
        ),
    },
    "pricing_guide": {
        "title": "💰 Ներքին գնագոյացման ուղեցույց",
        "text": (
            "<b>Ներքին pricing guide</b>\n\n"
            "Աղբյուրներ՝ HTX P2P (USDT/CNY) + CBA (AMD/USD/RUB)\n\n"
            "<b>Զեղչերի կանոն</b>\n"
            "• AMD/USD/RUB (քարտով): <$4000 → -1.5%, ≥$4000 → -1.0%\n"
            "• USDT: <$4000 → -1.0%, ≥$4000 → -0.5%\n\n"
            "⚠️ Միշտ հաստատիր գումարը, մեթոդը և վճարման արժույթը մինչև հաշվարկ ուղարկելը։"
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
            [InlineKeyboardButton(text="👤 Հաճախորդի տեքստեր", callback_data="kb_menu_user")],
            [InlineKeyboardButton(text="👨‍💼 Օպերատորի տեքստեր", callback_data="kb_menu_operator")],
        ]
    )

    await m.answer(
        "📚 <b>Տեղեկատու (KB)</b>\n\nԸնտրեք բաժինը՝",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


@router.callback_query(F.data == "kb_menu_user")
async def cb_kb_user_menu(callback: types.CallbackQuery):
    if not is_admin(callback.from_user):
        return await callback.answer("⛔️ Not authorized.", show_alert=True)

    buttons = [
        [InlineKeyboardButton(text=v["title"], callback_data=f"kb_user_{k}")]
        for k, v in USER_TEXTS.items()
    ]
    buttons.append([InlineKeyboardButton(text="⬅️ Հետ", callback_data="kb_back_main")])

    await callback.message.edit_text(
        "👤 <b>Հաճախորդի տեքստեր</b>\n\nԸնտրեք նյութը՝",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "kb_menu_operator")
async def cb_kb_operator_menu(callback: types.CallbackQuery):
    if not is_admin(callback.from_user):
        return await callback.answer("⛔️ Not authorized.", show_alert=True)

    buttons = [
        [InlineKeyboardButton(text=v["title"], callback_data=f"kb_operator_{k}")]
        for k, v in OPERATOR_TEXTS.items()
    ]
    buttons.append([InlineKeyboardButton(text="⬅️ Հետ", callback_data="kb_back_main")])

    await callback.message.edit_text(
        "👨‍💼 <b>Օպերատորի տեքստեր</b>\n\nԸնտրեք նյութը՝",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "kb_back_main")
async def cb_kb_back(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Հաճախորդի տեքստեր", callback_data="kb_menu_user")],
            [InlineKeyboardButton(text="👨‍💼 Օպերատորի տեքստեր", callback_data="kb_menu_operator")],
        ]
    )
    await callback.message.edit_text(
        "📚 <b>Տեղեկատու (KB)</b>\n\nԸնտրեք բաժինը՝",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("kb_user_"))
async def cb_kb_user_item(callback: types.CallbackQuery):
    if not is_admin(callback.from_user):
        return await callback.answer("⛔️ Not authorized.", show_alert=True)

    key = callback.data.replace("kb_user_", "", 1)
    item = USER_TEXTS.get(key)
    if not item:
        return await callback.answer("Not found", show_alert=True)

    buttons = [
        [InlineKeyboardButton(text="📋 Copy text", callback_data=f"kb_copy_user_{key}")],
        [InlineKeyboardButton(text="⬅️ Հետ", callback_data="kb_menu_user")],
    ]

    await callback.message.edit_text(
        f"{item['title']}\n\n{item['text']}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("kb_operator_"))
async def cb_kb_operator_item(callback: types.CallbackQuery):
    if not is_admin(callback.from_user):
        return await callback.answer("⛔️ Not authorized.", show_alert=True)

    key = callback.data.replace("kb_operator_", "", 1)
    item = OPERATOR_TEXTS.get(key)
    if not item:
        return await callback.answer("Not found", show_alert=True)

    buttons = [
        [InlineKeyboardButton(text="⬅️ Հետ", callback_data="kb_menu_operator")],
    ]

    await callback.message.edit_text(
        f"{item['title']}\n\n{item['text']}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("kb_copy_user_"))
async def cb_kb_copy(callback: types.CallbackQuery):
    """Send the text as a new message so admin can forward it."""
    if not is_admin(callback.from_user):
        return await callback.answer("⛔️ Not authorized.", show_alert=True)

    key = callback.data.replace("kb_copy_user_", "", 1)
    item = USER_TEXTS.get(key)
    if not item:
        return await callback.answer("Not found", show_alert=True)

    await callback.answer("✅ Sent below")
    await callback.message.answer(item["text"], parse_mode="HTML")


# ============================================================================
# USER COMMANDS (available to everyone)
# ============================================================================
@router.message(Command("guide"))
async def cmd_guide(m: types.Message):
    """Quick guide for users."""
    log.info("/guide by %s", m.from_user.id if m.from_user else "?")
    await m.answer(USER_TEXTS["intro_short"]["text"], parse_mode="HTML")


@router.message(Command("howto"))
async def cmd_howto(m: types.Message):
    """How to send CNY step by step."""
    log.info("/howto by %s", m.from_user.id if m.from_user else "?")
    await m.answer(USER_TEXTS["how_to_buy"]["text"], parse_mode="HTML")


@router.message(Command("faq"))
async def cmd_faq(m: types.Message):
    """Frequently asked questions."""
    log.info("/faq by %s", m.from_user.id if m.from_user else "?")
    await m.answer(USER_TEXTS["faq"]["text"], parse_mode="HTML")


@router.message(Command("contact"))
async def cmd_contact(m: types.Message):
    """Contact information."""
    log.info("/contact by %s", m.from_user.id if m.from_user else "?")
    await m.answer(USER_TEXTS["contact"]["text"], parse_mode="HTML")


@router.message(Command("pricing"))
async def cmd_pricing(m: types.Message):
    """Pricing and discount info."""
    log.info("/pricing by %s", m.from_user.id if m.from_user else "?")
    await m.answer(USER_TEXTS["pricing"]["text"], parse_mode="HTML")


# ============================================================================
# Quick KB commands (admin only - shortcuts)
# ============================================================================
@router.message(Command("kb_intro"))
async def cmd_kb_intro(m: types.Message):
    if not is_admin(m.from_user):
        return
    await m.answer(USER_TEXTS["intro_short"]["text"], parse_mode="HTML")


@router.message(Command("kb_how"))
async def cmd_kb_how(m: types.Message):
    if not is_admin(m.from_user):
        return
    await m.answer(USER_TEXTS["how_to_buy"]["text"], parse_mode="HTML")


@router.message(Command("kb_faq"))
async def cmd_kb_faq(m: types.Message):
    if not is_admin(m.from_user):
        return
    await m.answer(USER_TEXTS["faq"]["text"], parse_mode="HTML")
