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
    conn = sqlite3.connect('database.db', timeout=30)
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        res = None
        if fetch: res = cursor.fetchone()
        if fetch_all: res = cursor.fetchall()
        conn.commit()
        return res
    except Exception as e:
        logging.error(f"DB Error: {e}")
        return None
    finally:
        conn.close()

# Creare tabele
db_query('''CREATE TABLE IF NOT EXISTS users 
            (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0, 
             is_reseller INTEGER DEFAULT 0, has_weekend_pass INTEGER DEFAULT 0)''')
db_query('CREATE TABLE IF NOT EXISTS keys (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, key_val TEXT)')
db_query('CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, product TEXT, key_val TEXT, date TEXT)')

PRICES = {"f1": 25, "f7": 60, "d1": 20, "d7": 50, "wknd": 15}

def get_user_data(uid):
    res = db_query("SELECT balance, is_reseller, has_weekend_pass FROM users WHERE user_id = ?", (uid,), fetch=True)
    if not res:
        db_query("INSERT INTO users (user_id) VALUES (?)", (uid,))
        return 0.0, 0, 0
    return res

# --- MENIURI ---
def main_kb(uid):
    bal, is_reseller, has_pass = get_user_data(uid)
    
    if uid == ADMIN_ID: status = "👑 OWNER"
    elif is_reseller: status = "⭐ RESELLER"
    else: status = "👤 CLIENT"
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛒 SHOP", callback_data="shop"), types.InlineKeyboardButton(text="👤 PROFIL", callback_data="profile"))
    builder.row(types.InlineKeyboardButton(text="🔥 OFERTE", callback_data="specials"), types.InlineKeyboardButton(text="💼 RESELLER", callback_data="reseller"))
    builder.row(types.InlineKeyboardButton(text="💳 ADAUGĂ BANI", callback_data="add_info"))
    builder.row(types.InlineKeyboardButton(text="📞 SUPPORT", url="https://t.me/zenoficiall"))
    
    txt = f"🏪 **BLESSED PANELS**\n\n🏆 Status: `{status}`\n💰 Balanță: `{bal} LEI`"
    if has_pass: txt += "\n🎫 Weekend Pass: ✅ ACTIV (-5 LEI)"
    txt += f"\n🆔 ID: `{uid}`"
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

@dp.callback_query(F.data == "specials")
async def specials_menu(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🎁 Cumpără Weekend Pass (15 LEI)", callback_data="buy_wknd"))
    builder.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home"))
    await call.message.edit_text("🔥 **OFERTE SPECIALE**\n\n🎫 **Weekend Pass:**\nReducere de **5 LEI** la orice hack!", reply_markup=builder.as_markup())

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

@dp.callback_query(F.data.startswith("buy_"))
async def handle_buy(call: types.CallbackQuery):
    prod = call.data.replace("buy_", "")
    uid = call.from_user.id
    bal, _, has_pass = get_user_data(uid)
    pret = PRICES.get(prod, 999)
    if has_pass and prod != "wknd": pret -= 5

    if bal < pret: return await call.answer(f"❌ Ai nevoie de {pret} LEI!", show_alert=True)

    if prod == "wknd":
        db_query("UPDATE users SET balance = balance - ?, has_weekend_pass = 1 WHERE user_id = ?", (pret, uid))
        await call.message.answer("🎁 Weekend Pass ACTIV!")
    else:
        key = db_query("SELECT id, key_val FROM keys WHERE type = ? LIMIT 1", (prod,), fetch=True)
        if not key: return await call.answer("❌ STOC EPUIZAT!", show_alert=True)
        db_query("UPDATE users SET balance = balance - ?, has_weekend_pass = has_weekend_pass WHERE user_id = ?", (pret, uid))
        db_query("DELETE FROM keys WHERE id = ?", (key[0],))
        db_query("INSERT INTO orders (user_id, product, key_val, date) VALUES (?, ?, ?, ?)", (uid, prod, key[1], datetime.now().strftime("%d/%m")))
        await call.message.answer(f"✅ CHEIE: `{key[1]}`")

    txt, kb = main_kb(uid)
    await call.message.edit_text(txt, reply_markup=kb, parse_mode="Markdown")

# --- ADMIN ---
@dp.message(Command("add"))
async def add_bal(m: types.Message):
    if m.from_user.id == ADMIN_ID:
        p = m.text.split()
        db_query("UPDATE users SET balance = balance + ? WHERE user_id = ?", (float(p[2]), int(p[1])))
        await m.answer("✅ Balanță actualizată!")

@dp.message(Command("addkey"))
async def add_key(m: types.Message):
    if m.from_user.id == ADMIN_ID:
        p = m.text.split()
        db_query("INSERT INTO keys (type, key_val) VALUES (?, ?)", (p[1], p[2]))
        await m.answer("✅ Cheie adăugată!")

@dp.message(Command("setreseller"))
async def set_reseller(m: types.Message):
    if m.from_user.id == ADMIN_ID:
        tid = int(m.text.split()[1])
        db_query("UPDATE users SET is_reseller = 1 WHERE user_id = ?", (tid,))
        await m.answer(f"⭐ User {tid} este acum RESELLER.")

async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
