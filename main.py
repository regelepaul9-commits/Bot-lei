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
    conn = sqlite3.connect('database.db', timeout=30)
    conn.execute("PRAGMA journal_mode=WAL") # Mod special pentru viteză/stabilitate
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

# Creare Tabele
db_query('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0, is_reseller INTEGER DEFAULT 0, has_weekend_pass INTEGER DEFAULT 0, joined_date TEXT)')
db_query('CREATE TABLE IF NOT EXISTS keys (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, key_val TEXT)')
db_query('CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, product TEXT, key_val TEXT, date TEXT)')

PRICES = {"f1": 25, "f7": 60, "d1": 20, "d7": 50, "wknd": 15}

def get_user_info(uid):
    user = db_query("SELECT balance, is_reseller, has_weekend_pass, joined_date FROM users WHERE user_id = ?", (uid,), fetch=True)
    if not user:
        now = datetime.now().strftime("%d/%m/%Y")
        db_query("INSERT INTO users (user_id, joined_date) VALUES (?, ?)", (uid, now))
        return (0.0, 0, 0, now)
    return user

# --- MENIURI ---
def main_menu(uid):
    bal, is_reseller, has_pass, _ = get_user_info(uid)
    status = "👑 OWNER" if uid == ADMIN_ID else ("⭐ Reseller" if is_reseller else "👤 Client")
    pass_txt = "\n🎫 Weekend Pass: ✅ ACTIV (-3 LEI)" if has_pass else ""
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛒 SHOP", callback_data="shop"), types.InlineKeyboardButton(text="👤 PROFIL", callback_data="profile"))
    builder.row(types.InlineKeyboardButton(text="🔥 OFERTE", callback_data="specials"), types.InlineKeyboardButton(text="💼 RESELLER", callback_data="reseller"))
    builder.row(types.InlineKeyboardButton(text="💳 ADAUGĂ BANI", callback_data="add_info"))
    builder.row(types.InlineKeyboardButton(text="📞 SUPPORT", url="https://t.me/zenoficiall"))
    
    text = f"🏪 **BLESSED PANELS**\n\n🦁 Balanță: `{bal} LEI`\n🏆 Status: `{status}`{pass_txt}\n🆔 ID: `{uid}`"
    return text, builder.as_markup()

# --- HANDLERE ---
@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    await m.answer(*main_menu(m.from_user.id), parse_mode="Markdown")

@dp.callback_query(F.data == "home")
async def back_home(call: types.CallbackQuery):
    await call.message.edit_text(*main_menu(call.from_user.id), parse_mode="Markdown")

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

@dp.callback_query(F.data == "specials")
async def specials_menu(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🎁 Weekend Pass - 15 LEI", callback_data="buy_wknd"))
    builder.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home"))
    await call.message.edit_text("🔥 **OFERTE SPECIALE:**\nWeekend Pass: -3 LEI reducere la orice hack!", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "profile")
async def profile_menu(call: types.CallbackQuery):
    bal, _, has_pass, joined = get_user_info(call.from_user.id)
    orders = db_query("SELECT product, key_val, date FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT 5", (call.from_user.id,), fetch_all=True)
    history = "\n".join([f"🔹 {o[0]}: `{o[1]}`" for o in orders]) if orders else "Nicio cheie."
    text = f"👤 **PROFIL**\n💰 Balanță: `{bal} LEI`\n📅 Data: `{joined}`\n\n📜 **ULTIMELE CHEI:**\n{history}"
    await call.message.edit_text(text, reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home")).as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("buy_"))
async def handle_buy(call: types.CallbackQuery):
    prod = call.data.replace("buy_", "")
    bal, _, has_pass, _ = get_user_info(call.from_user.id)
    pret = PRICES.get(prod, 999)
    if has_pass and prod != "wknd": pret -= 3

    if bal < pret: return await call.answer(f"❌ Ai nevoie de {pret} LEI!", show_alert=True)

    if prod == "wknd":
        if has_pass: return await call.answer("Deja activ!", show_alert=True)
        db_query("UPDATE users SET balance = balance - ?, has_weekend_pass = 1 WHERE user_id = ?", (pret, call.from_user.id))
        await call.message.answer("🎁 Weekend Pass ACTIV!")
    else:
        key = db_query("SELECT id, key_val FROM keys WHERE type = ? LIMIT 1", (prod,), fetch=True)
        if not key: return await call.answer("❌ STOC EPUIZAT!", show_alert=True)
        db_query("UPDATE users SET balance = balance - ? WHERE user_id = ?", (pret, call.from_user.id))
        db_query("DELETE FROM keys WHERE id = ?", (key[0],))
        db_query("INSERT INTO orders (user_id, product, key_val, date) VALUES (?, ?, ?, ?)", (call.from_user.id, prod, key[1], datetime.now().strftime("%d/%m")))
        await call.message.answer(f"✅ CHEIE: `{key[1]}`")

    await call.message.edit_text(*main_menu(call.from_user.id), parse_mode="Markdown")

# --- ADMIN COMMANDS ---
@dp.message(Command("add"))
async def add_money(m: types.Message):
    if m.from_user.id == ADMIN_ID:
        p = m.text.split()
        db_query("UPDATE users SET balance = balance + ? WHERE user_id = ?", (float(p[2]), int(p[1])))
        await m.answer("✅ Gata!")

@dp.message(Command("addkey"))
async def add_key_admin(m: types.Message):
    if m.from_user.id == ADMIN_ID:
        p = m.text.split()
        db_query("INSERT INTO keys (type, key_val) VALUES (?, ?)", (p[1], p[2]))
        await m.answer(f"✅ Cheie adăugată la {p[1]}")

@dp.callback_query(F.data == "add_info")
async def add_info(call: types.CallbackQuery):
    await call.message.edit_text(f"💳 **REÎNCĂRCARE**\nContact: @zenoficiall\nID: `{call.from_user.id}`", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home")).as_markup())

@dp.callback_query(F.data == "reseller")
async def res_panel(call: types.CallbackQuery):
    await call.message.edit_text("💼 **RESELLER**\nContactează @zenoficiall pentru prețuri bulk.", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home")).as_markup())

async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
