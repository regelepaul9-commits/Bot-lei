import asyncio
import logging
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- CONFIG ---
TOKEN = '8547474775:AAGQ40_r3l3OyYUL6xMaXi-bugGXozNyFkA'
ADMIN_ID = 7481370573 

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- DATABASE ---
def db_query(query, params=(), fetch=False, fetch_all=False):
    try:
        conn = sqlite3.connect('database.db', timeout=30)
        cursor = conn.cursor()
        cursor.execute(query, params)
        res = None
        if fetch: res = cursor.fetchone()
        if fetch_all: res = cursor.fetchall()
        conn.commit()
        conn.close()
        return res
    except Exception as e:
        print(f"DB Error: {e}")
        return None

# Init tables
db_query('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0, is_reseller INTEGER DEFAULT 0, has_weekend_pass INTEGER DEFAULT 0)')
db_query('CREATE TABLE IF NOT EXISTS keys (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, key_val TEXT)')
db_query('CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, product TEXT, key_val TEXT, date TEXT)')

PRICES = {"f1": 25, "f7": 60, "d1": 20, "d7": 50, "wknd": 15}

def get_bal(uid):
    res = db_query("SELECT balance, has_weekend_pass FROM users WHERE user_id = ?", (uid,), fetch=True)
    if not res:
        db_query("INSERT INTO users (user_id) VALUES (?)", (uid,))
        return 0.0, 0
    return res

# --- KEYBOARDS ---
def main_kb(uid):
    bal, has_pass = get_bal(uid)
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛒 SHOP", callback_data="shop"), types.InlineKeyboardButton(text="👤 PROFIL", callback_data="profile"))
    builder.row(types.InlineKeyboardButton(text="💳 ADAUGĂ BANI", callback_data="add_info"), types.InlineKeyboardButton(text="💼 RESELLER", callback_data="reseller"))
    builder.row(types.InlineKeyboardButton(text="📞 SUPPORT", url="https://t.me/zenoficiall"))
    
    txt = f"🏪 **BLESSED PANELS**\n\n💰 Balanță: `{bal} LEI`\n🆔 ID: `{uid}`"
    if has_pass: txt += "\n🎫 Weekend Pass: ✅ ACTIV"
    return txt, builder.as_markup()

# --- HANDLERS ---
@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    txt, kb = main_kb(m.from_user.id)
    await m.answer(txt, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "home")
async def back_home(call: types.CallbackQuery):
    txt, kb = main_kb(call.from_user.id)
    await call.message.edit_text(txt, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "shop")
async def shop_menu(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🍎 iOS", callback_data="cat_ios"), types.InlineKeyboardButton(text="🤖 Android", callback_data="cat_and"))
    builder.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home"))
    await call.message.edit_text("🌀 **ALEGE PLATFORMA:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "cat_and")
async def and_menu(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Drip 1 Zi - 20 LEI", callback_data="buy_d1"))
    builder.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="shop"))
    await call.message.edit_text("🤖 **ANDROID DRIP:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "profile")
async def profile(call: types.CallbackQuery):
    uid = call.from_user.id
    orders = db_query("SELECT product, key_val FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT 3", (uid,), fetch_all=True)
    history = "\n".join([f"🔹 {o[0]}: `{o[1]}`" for o in orders]) if orders else "Fără achiziții."
    await call.message.edit_text(f"👤 **PROFIL**\n\n📜 **ULTIMELE CHEI:**\n{history}", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home")).as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "buy_d1")
async def buy_d1(call: types.CallbackQuery):
    uid = call.from_user.id
    bal, has_pass = get_bal(uid)
    pret = 20 - (3 if has_pass else 0)
    
    if bal < pret: return await call.answer(f"❌ Ai nevoie de {pret} LEI!", show_alert=True)
    
    key = db_query("SELECT id, key_val FROM keys WHERE type = 'd1' LIMIT 1", fetch=True)
    if not key: return await call.answer("❌ STOC EPUIZAT!", show_alert=True)
    
    db_query("UPDATE users SET balance = balance - ? WHERE user_id = ?", (pret, uid))
    db_query("DELETE FROM keys WHERE id = ?", (key[0],))
    db_query("INSERT INTO orders (user_id, product, key_val, date) VALUES (?, ?, ?, ?)", (uid, "Drip 1 Zi", key[1], datetime.now().strftime("%d/%m")))
    
    await call.message.answer(f"✅ CHEIE: `{key[1]}`")
    txt, kb = main_kb(uid)
    await call.message.edit_text(txt, reply_markup=kb, parse_mode="Markdown")

# --- ADMIN ---
@dp.message(Command("add"))
async def add_bal(m: types.Message):
    if m.from_user.id != ADMIN_ID: return
    p = m.text.split()
    db_query("UPDATE users SET balance = balance + ? WHERE user_id = ?", (float(p[2]), int(p[1])))
    await m.answer("✅ OK")

@dp.message(Command("addkey"))
async def add_key(m: types.Message):
    if m.from_user.id != ADMIN_ID: return
    p = m.text.split()
    db_query("INSERT INTO keys (type, key_val) VALUES (?, ?)", (p[1], p[2]))
    await m.answer(f"✅ Adăugat {p[1]}")

@dp.callback_query(F.data == "add_info")
async def add_info(call: types.CallbackQuery):
    await call.message.edit_text(f"💳 **REÎNCĂRCARE**\nContact: @zenoficiall\nID: `{call.from_user.id}`", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home")).as_markup())

@dp.callback_query(F.data == "reseller")
async def res_info(call: types.CallbackQuery):
    await call.message.edit_text("💼 **RESELLER**\nContact @zenoficiall", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home")).as_markup())

async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
