import asyncio
import logging
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- CONFIGURARE ---
TOKEN = '8547474775:AAGQ40_r3l3OyYUL6xMaXi-bugGXozNyFkA'
ADMIN_ID = 7481370573 

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- DATABASE ENGINE ---
def db_query(query, params=(), fetch=False, fetch_all=False):
    conn = sqlite3.connect('database.db', timeout=20)
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        res = None
        if fetch: res = cursor.fetchone()
        if fetch_all: res = cursor.fetchall()
        conn.commit()
        return res
    except Exception as e:
        logging.error(f"Database error: {e}")
        return None
    finally:
        conn.close()

# Inițializare tabele
db_query('''CREATE TABLE IF NOT EXISTS users 
            (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0, 
             is_reseller INTEGER DEFAULT 0, has_weekend_pass INTEGER DEFAULT 0, 
             joined_date TEXT)''')
db_query('CREATE TABLE IF NOT EXISTS keys (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, key_val TEXT)')
db_query('CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, product TEXT, key_val TEXT, date TEXT)')

# Prețuri
PRICES = {"f1": 25, "f7": 60, "d1": 20, "d7": 50, "wknd": 15}

def get_user_info(uid):
    user = db_query("SELECT balance, is_reseller, has_weekend_pass, joined_date FROM users WHERE user_id = ?", (uid,), fetch=True)
    if not user:
        now = datetime.now().strftime("%d/%m/%Y")
        db_query("INSERT INTO users (user_id, joined_date) VALUES (?, ?)", (uid, now))
        return (0.0, 0, 0, now)
    return user

# --- MENIURI ---
def main_menu_keyboard(uid):
    bal, is_reseller, has_pass, _ = get_user_info(uid)
    status = "👑 OWNER" if uid == ADMIN_ID else ("⭐ Reseller" if is_reseller else "👤 Client")
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛒 SHOP", callback_data="shop"), types.InlineKeyboardButton(text="👤 PROFIL", callback_data="profile"))
    builder.row(types.InlineKeyboardButton(text="🔥 OFERTE", callback_data="specials"), types.InlineKeyboardButton(text="💼 RESELLER", callback_data="reseller"))
    builder.row(types.InlineKeyboardButton(text="💳 ADAUGĂ BANI", callback_data="add_info"))
    builder.row(types.InlineKeyboardButton(text="📞 SUPPORT", url="https://t.me/zenoficiall"))
    
    pass_txt = "\n🎫 Weekend Pass: ✅ ACTIV" if has_pass else ""
    text = f"🏪 **BLESSED PANELS**\n\n🦁 Balanță: `{bal} LEI`\n🏆 Status: `{status}`{pass_txt}\n🆔 ID: `{uid}`"
    return text, builder.as_markup()

# --- HANDLERE ---
@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    text, markup = main_menu_keyboard(m.from_user.id)
    await m.answer(text, reply_markup=markup, parse_mode="Markdown")

@dp.callback_query(F.data == "home")
async def back_home(call: types.CallbackQuery):
    text, markup = main_menu_keyboard(call.from_user.id)
    await call.message.edit_text(text, reply_markup=markup, parse_mode="Markdown")

@dp.callback_query(F.data == "shop")
async def shop_menu(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🍎 iOS (Fluorite)", callback_data="cat_ios"))
    builder.row(types.InlineKeyboardButton(text="🤖 Android (Drip)", callback_data="cat_and"))
    builder.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home"))
    await call.message.edit_text("🌀 **ALEGE PLATFORMA:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "cat_ios")
async def ios_menu(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Fluorite 1 Zi - 25 LEI", callback_data="buy_f1"))
    builder.row(types.InlineKeyboardButton(text="Fluorite 7 Zile - 60 LEI", callback_data="buy_f7"))
    builder.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="shop"))
    await call.message.edit_text("🍎 **PRODUSE iOS:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "cat_and")
async def and_menu(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Drip 1 Zi - 20 LEI", callback_data="buy_d1"))
    builder.row(types.InlineKeyboardButton(text="Drip 7 Zile - 50 LEI", callback_data="buy_d7"))
    builder.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="shop"))
    await call.message.edit_text("🤖 **PRODUSE ANDROID:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("buy_"))
async def handle_buy(call: types.CallbackQuery):
    prod = call.data.replace("buy_", "")
    uid = call.from_user.id
    bal, _, has_pass, _ = get_user_info(uid)
    
    pret = PRICES.get(prod, 999)
    if has_pass and prod != "wknd": pret -= 3

    if bal < pret: return await call.answer(f"❌ Ai nevoie de {pret} LEI!", show_alert=True)

    if prod == "wknd":
        if has_pass: return await call.answer("Ai deja Weekend Pass!", show_alert=True)
        db_query("UPDATE users SET balance = balance - ?, has_weekend_pass = 1 WHERE user_id = ?", (pret, uid))
        await call.message.answer("🎁 **Weekend Pass ACTIVAT!**\nAcum ai -3 LEI reducere la orice hack.")
    else:
        key = db_query("SELECT id, key_val FROM keys WHERE type = ? LIMIT 1", (prod,), fetch=True)
        if not key: return await call.answer("❌ STOC EPUIZAT!", show_alert=True)
        
        now = datetime.now().strftime("%d/%m %H:%M")
        db_query("UPDATE users SET balance = balance - ? WHERE user_id = ?", (pret, uid))
        db_query("DELETE FROM keys WHERE id = ?", (key[0],))
        db_query("INSERT INTO orders (user_id, product, key_val, date) VALUES (?, ?, ?, ?)", (uid, prod, key[1], now))
        await call.message.answer(f"✅ **ACHIZIȚIE REUȘITĂ!**\n\n🔑 CHEIE: `{key[1]}`")

    text, markup = main_menu_keyboard(uid)
    await call.message.edit_text(text, reply_markup=markup, parse_mode="Markdown")

@dp.message(Command("add"))
async def add_money(m: types.Message):
    if m.from_user.id != ADMIN_ID: return
    try:
        parts = m.text.split()
        tid, suma = int(parts[1]), float(parts[2])
        db_query("UPDATE users SET balance = balance + ? WHERE user_id = ?", (suma, tid))
        await m.answer(f"✅ Adăugat {suma} LEI lui `{tid}`.")
    except: await m.answer("Sintaxă: `/add ID SUMA`")

async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
