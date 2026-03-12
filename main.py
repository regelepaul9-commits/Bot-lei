import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# --- CONFIGURARE ---
TOKEN = '8547474775:AAGmcaWK706de3V3YxC8LdTr_lHLZn1Pihk'
ADMIN_ID = 7481370573 

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# --- DATABASE ---
conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0)')
conn.commit()

def get_bal(uid):
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (uid,))
    res = cursor.fetchone()
    if res: return res[0]
    cursor.execute("INSERT INTO users (user_id, balance) VALUES (?, ?)", (uid, 0.0))
    conn.commit()
    return 0.0

def update_bal(uid, amt):
    new_v = get_bal(uid) + amt
    cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_v, uid))
    conn.commit()
    return new_v

PRICES = {"1day": 25.0, "7days": 50.0, "30days": 100.0}

# --- HANDLERE ---
@dp.message_handler(commands=['start'])
async def cmd_start(m: types.Message):
    bal = get_bal(m.from_user.id)
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🛒 Shop Now", callback_data="shop"),
        types.InlineKeyboardButton("🎁 Oferte Speciale", callback_data="offers"),
        types.InlineKeyboardButton("💎 Apply for Reseller", callback_data="apply"),
        types.InlineKeyboardButton("📞 Support", url="https://t.me/zenoficiall")
    )
    await m.answer(f"🏪 **BLESSED PANELS**\n\n🦁 Balanță: `{bal} LEI`\n🆔 ID: `{m.from_user.id}`", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query_handler(text="shop")
async def shop(call: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🍎 iOS (Fluorite)", callback_data="ios"),
        types.InlineKeyboardButton("🤖 Android (Drip)", callback_data="and"),
        types.InlineKeyboardButton("⬅️ Înapoi", callback_data="home")
    )
    await call.message.edit_text("🌀 **ALEGE PLATFORMA:**", reply_markup=kb)

@dp.callback_query_handler(text="ios")
async def ios_menu(call: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=1)
    for k, v in PRICES.items():
        kb.add(types.InlineKeyboardButton(f"🔮 Fluorite {k} - {int(v)} LEI", callback_data=f"b_fluorite_{k}"))
    kb.add(types.InlineKeyboardButton("⬅️ Înapoi", callback_data="shop"))
    await call.message.edit_text("🍎 **PRODUSE iOS:**", reply_markup=kb)

@dp.callback_query_handler(text="and")
async def and_menu(call: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=1)
    for k, v in PRICES.items():
        kb.add(types.InlineKeyboardButton(f"💧 Drip {k} - {int(v)} LEI", callback_data=f"b_drip_{k}"))
    kb.add(types.InlineKeyboardButton("⬅️ Înapoi", callback_data="shop"))
    await call.message.edit_text("🤖 **PRODUSE ANDROID:**", reply_markup=kb)

@dp.callback_query_handler(text="home")
async def back_h(call: types.CallbackQuery):
    await cmd_start(call.message)
    await call.message.delete()

@dp.message_handler(commands=['add'])
async def ad_money(m: types.Message):
    if m.from_user.id == ADMIN_ID:
        try:
            args = m.get_args().split()
            uid, amt = int(args[0]), float(args[1])
            nv = update_bal(uid, amt)
            await m.answer(f"✅ OK! ID `{uid}` are acum `{nv} LEI`.")
        except:
            await m.answer("Folosește: /add [ID] [SUMA]")

if __name__ == '__main__':
    print("Botul a pornit...")
    # Fix pentru Render/Python 3.10+
    loop = asyncio.get_event_loop()
    executor.start_polling(dp, skip_updates=True)
