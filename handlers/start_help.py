from logging import getLogger
from aiogram import Router, types
from aiogram.filters import CommandStart, Command

log = getLogger("h.start")
router = Router()

HELLO = (
"👋 Բարեւ! Բարի գալուստ HighBit փոխարկիչ։\n"
"Օգտագործեք /convert — գումարը փոխարկելու համար (CNY-ից)\n"
"Օգտագործեք /rates — տեսնելու համար այսօրվա կուրսերը\n"
"Օգնության համար՝ /help\n"
"Օպերատոր՝ @Highbitagent\n\n"
"Խնդրում եմ գրեք ցանկալի գումարի չափը CNY–ով և ես կհաշվեմ այն ձեզ համար.\n"
"Please enter the desired amount in CNY and I'll calculate it for you.\n"
"Пожалуйста, введите сумму в CNY, и я её посчитаю."
)

HELP = (
"ℹ️ Օգնություն / Help\n\n"
"/rates — օրվա կուրսերը (kopecks, 2 decimals)\n"
"/convert — ուղարկեք թիվ՝ օրինակ 3000 (CNY) կամ 3000$ (USD)\n"
"Օպերատոր՝ @Highbitagent"
)

@router.message(CommandStart())
async def start(m: types.Message):
    log.info("/start by %s", m.from_user.id if m.from_user else "?")
    await m.answer(HELLO)

@router.message(Command("help"))
async def help_(m: types.Message):
    log.info("/help by %s", m.from_user.id if m.from_user else "?")
    await m.answer(HELP)
