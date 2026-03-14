import asyncio
import logging
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- CONFIG ---
TOKEN = '8547474775:AAGQ40_r3l3OyYUL6xMaXi-bugGXozNyFkA'
OWNER_ID = 7481370573 

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- DB ENGINE ---
def db_query(query, params=(), fetch=False, fetch_all=False):
    conn = sqlite3.connect('database.db', timeout=30)
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        res = cursor.fetchone() if fetch else (cursor.fetchall() if fetch_all else None)
        conn.commit()
        return res
    finally:
        conn.close()

# Init Tables
db_query('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0, is_admin INTEGER DEFAULT 0, has_weekend_pass INTEGER DEFAULT 0)')
db_query('CREATE TABLE IF NOT EXISTS keys (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, key_val TEXT)')

# --- PREȚURI (EURO) ---
PRICES = {
    "8bp7": 6, "8bp15": 10, "8bp30": 12, # 8 Ball
    "elx7": 3, "elx14": 6, "elx30": 7,   # Elixir
    "zn7": 5, "zn30": 8.5, "zn60": 15,   # Zenin
    "d1": 4, "d7": 10, "d30": 25,        # Drip
    "f1": 5, "f7": 12, "f30": 30         # Fluorite
}

# --- HELPERS ---
def get_user(uid):
    res = db_query("SELECT balance, is_admin, has_weekend_pass FROM users WHERE user_id = ?", (uid,), fetch=True)
    if not res:
        db_query("INSERT INTO users (user_id) VALUES (?)", (uid,))
        return 0.0, 0, 0
    return res

# --- MENIURI ---
def main_kb(uid):
    bal, is_admin, has_pass = get_user(uid)
    status = "👑 OWNER" if uid == OWNER_ID else ("🛠️ ADMIN" if is_admin else "👤 CLIENT")
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛒 SHOP", callback_data="shop"))
    builder.row(types.InlineKeyboardButton(text="👤 PROFIL", callback_data="profile"), types.InlineKeyboardButton(text="💳 REÎNCĂRCARE", callback_data="add_info"))
    builder.row(types.InlineKeyboardButton(text="📞 SUPPORT", url="https://t.me/zenoficiall"))
    return f"🏪 **BLESSED PANELS**\n\n🏆 Grad: `{status}`\n💰 Balanță: `{bal} EUR`", builder.as_markup()

# --- HANDLERS ---
@dp.message(Command("start"))
async def start(m: types.Message):
    txt, kb = main_kb(m.from_user.id)
    await m.answer(txt, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "shop")
async def shop(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🎱 8 Ball Pool", callback_data="cat_8bp"))
    builder.row(types.InlineKeyboardButton(text="🧪 Elixir External", callback_data="cat_elx"))
    builder.row(types.InlineKeyboardButton(text="🐉 Zenin PC/Android", callback_data="cat_zn"))
    builder.row(types.InlineKeyboardButton(text="🤖 Drip", callback_data="cat_d"), types.InlineKeyboardButton(text="🍎 Fluorite", callback_data="cat_f"))
    builder.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home"))
    await call.message.edit_text("🌀 **CATEGORII:**", reply_markup=builder.as_markup())

# Exemplu Categorie (8 Ball)
@dp.callback_query(F.data == "cat_8bp")
async def cat_8bp(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="7z - 6€", callback_data="buy_8bp7"), types.InlineKeyboardButton(text="15z - 10€", callback_data="buy_8bp15"))
    builder.row(types.InlineKeyboardButton(text="30z - 12€", callback_data="buy_8bp30"))
    builder.row(types.InlineKeyboardButton(text="⬅️", callback_data="shop"))
    await call.message.edit_text("🎱 **8 BALL POOL PSHX4**", reply_markup=builder.as_markup())

# --- ADMIN ---
@dp.message(Command("add"))
async def add_bal(m: types.Message):
    _, is_adm, _ = get_user(m.from_user.id)
    if m.from_user.id == OWNER_ID or is_adm:
        p = m.text.split()
        db_query("UPDATE users SET balance = balance + ? WHERE user_id = ?", (float(p[2]), int(p[1])))
        await m.answer("✅ Balanță actualizată!")

@dp.message(Command("addkey"))
async def add_key(m: types.Message):
    _, is_adm, _ = get_user(m.from_user.id)
    if m.from_user.id == OWNER_ID or is_adm:
        p = m.text.split()
        db_query("INSERT INTO keys (type, key_val) VALUES (?, ?)", (p[1], p[2]))
        await m.answer(f"✅ Cheie {p[1]} adăugată!")

@dp.callback_query(F.data == "home")
async def home(call: types.CallbackQuery):
    txt, kb = main_kb(call.from_user.id)
    await call.message.edit_text(txt, reply_markup=kb, parse_mode="Markdown")

async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
