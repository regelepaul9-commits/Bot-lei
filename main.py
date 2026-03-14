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
        if fetch: return cursor.fetchone()
        if fetch_all: return cursor.fetchall()
        conn.commit()
    finally:
        conn.close()

# Creare tabele
db_query('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0, is_admin INTEGER DEFAULT 0, has_weekend_pass INTEGER DEFAULT 0)')
db_query('CREATE TABLE IF NOT EXISTS keys (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, key_val TEXT)')

# --- PREȚURI EURO ---
PRICES = {
    "d1": 4, "d7": 10, "d30": 25, "f1": 5, "f7": 12, "f30": 30,
    "8bp7": 6, "8bp15": 10, "8bp30": 12, "elx7": 3, "elx14": 6, "elx30": 7,
    "zn7": 5, "zn30": 8.5, "zn60": 15, "wknd": 5
}

def get_u(uid):
    res = db_query("SELECT balance, is_admin, has_weekend_pass FROM users WHERE user_id = ?", (uid,), fetch=True)
    if not res:
        db_query("INSERT INTO users (user_id) VALUES (?)", (uid,))
        return 0.0, 0, 0
    return res

# --- INTERFAȚA ---
def main_kb(uid):
    bal, is_adm, has_p = get_u(uid)
    stat = "👑 OWNER" if uid == OWNER_ID else ("🛠️ ADMIN" if is_adm else "👤 CLIENT")
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛒 SHOP", callback_data="shop"), types.InlineKeyboardButton(text="👤 PROFIL", callback_data="prof"))
    builder.row(types.InlineKeyboardButton(text="💳 REÎNCĂRCARE", callback_data="reinc"), types.InlineKeyboardButton(text="📞 SUPPORT", url="https://t.me/zenoficiall"))
    txt = f"🏪 **BLESSED PANELS**\n\n🏆 Grad: `{stat}`\n💰 Balanță: `{bal} EUR`"
    if has_p: txt += "\n🎫 Weekend Pass: ✅ ACTIV"
    return txt, builder.as_markup()

# --- HANDLERS ---
@dp.message(Command("start"))
async def start(m: types.Message):
    t, k = main_kb(m.from_user.id)
    await m.answer(t, reply_markup=k, parse_mode="Markdown")

@dp.callback_query(F.data == "shop")
async def shop(c: types.CallbackQuery):
    b = InlineKeyboardBuilder()
    b.row(types.InlineKeyboardButton(text="🎱 8 Ball", callback_data="cat_8"), types.InlineKeyboardButton(text="🧪 Elixir", callback_data="cat_e"))
    b.row(types.InlineKeyboardButton(text="🐉 Zenin", callback_data="cat_z"))
    b.row(types.InlineKeyboardButton(text="🤖 Drip", callback_data="cat_d"), types.InlineKeyboardButton(text="🍎 Fluorite", callback_data="cat_f"))
    b.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home"))
    await c.message.edit_text("🌀 **CATEGORII:**", reply_markup=b.as_markup())

@dp.callback_query(F.data == "cat_8")
async def cat8(c: types.CallbackQuery):
    b = InlineKeyboardBuilder()
    b.row(types.InlineKeyboardButton(text="7z-6€", callback_data="buy_8bp7"), types.InlineKeyboardButton(text="30z-12€", callback_data="buy_8bp30"))
    b.row(types.InlineKeyboardButton(text="⬅️", callback_data="shop"))
    await c.message.edit_text("🎱 **8 BALL POOL PSHX4**", reply_markup=b.as_markup())

@dp.callback_query(F.data == "home")
async def home(c: types.CallbackQuery):
    t, k = main_kb(c.from_user.id)
    await c.message.edit_text(t, reply_markup=k, parse_mode="Markdown")

# --- ADMIN ---
@dp.message(Command("add"))
async def add(m: types.Message):
    if m.from_user.id == OWNER_ID or get_u(m.from_user.id)[1]:
        try:
            p = m.text.split()
            db_query("UPDATE users SET balance = balance + ? WHERE user_id = ?", (float(p[2]), int(p[1])))
            await m.answer(f"✅ Adăugat {p[2]}€ lui {p[1]}")
        except: await m.answer("`/add ID SUMA`")

@dp.message(Command("addkey"))
async def addk(m: types.Message):
    if m.from_user.id == OWNER_ID or get_u(m.from_user.id)[1]:
        try:
            p = m.text.split()
            db_query("INSERT INTO keys (type, key_val) VALUES (?, ?)", (p[1], p[2]))
            await m.answer(f"✅ Cheie {p[1]} adăugată!")
        except: await m.answer("`/addkey tip cheie` (ex: 8bp7, zn30, d7)")

async def main():
    logging.basicConfig(level=logging.INFO)
    # FORȚĂM ȘTERGEREA SESIUNILOR VECHI
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
