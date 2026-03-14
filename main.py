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
db_query('CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, product TEXT, key_val TEXT, date TEXT)')

# --- PREȚURI EURO ---
PRICES = {
    "d1": 4, "d7": 10, "d30": 25, "f1": 5, "f7": 12, "f30": 30,
    "8bp7": 6, "8bp15": 10, "8bp30": 12, "elx7": 3, "elx14": 6, "elx30": 7,
    "zn7": 5, "zn30": 8.5, "zn60": 15, "wknd": 2 # Weekend Pass: 2 EURO
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
    builder.row(types.InlineKeyboardButton(text="🔥 OFERTE", callback_data="specials"), types.InlineKeyboardButton(text="💳 REÎNCĂRCARE", callback_data="reinc"))
    builder.row(types.InlineKeyboardButton(text="📞 SUPPORT", url="https://t.me/zenoficiall"))
    txt = f"🏪 **BLESSED PANELS**\n\n🏆 Grad: `{stat}`\n💰 Balanță: `{bal} EUR`"
    if has_p: txt += "\n🎫 Weekend Pass: ✅ ACTIV (-1€ Reducere)"
    return txt, builder.as_markup()

# --- HANDLERS ---
@dp.message(Command("start"))
async def start(m: types.Message):
    t, k = main_kb(m.from_user.id)
    await m.answer(t, reply_markup=k, parse_mode="Markdown")

@dp.callback_query(F.data == "home")
async def home_cb(c: types.CallbackQuery):
    t, k = main_kb(c.from_user.id)
    await c.message.edit_text(t, reply_markup=k, parse_mode="Markdown")

@dp.callback_query(F.data == "shop")
async def shop(c: types.CallbackQuery):
    b = InlineKeyboardBuilder()
    b.row(types.InlineKeyboardButton(text="🎱 8 Ball", callback_data="cat_8"), types.InlineKeyboardButton(text="🧪 Elixir", callback_data="cat_e"))
    b.row(types.InlineKeyboardButton(text="🐉 Zenin", callback_data="cat_z"))
    b.row(types.InlineKeyboardButton(text="🤖 Drip", callback_data="cat_d"), types.InlineKeyboardButton(text="🍎 Fluorite", callback_data="cat_f"))
    b.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home"))
    await c.message.edit_text("🌀 **CATEGORII:**", reply_markup=b.as_markup())

# --- CATEGORII ---
@dp.callback_query(F.data == "cat_d")
async def catd(c: types.CallbackQuery):
    b = InlineKeyboardBuilder()
    b.row(types.InlineKeyboardButton(text="1z-4€", callback_data="buy_d1"), types.InlineKeyboardButton(text="7z-10€", callback_data="buy_d7"))
    b.row(types.InlineKeyboardButton(text="30z-25€", callback_data="buy_d30"))
    b.row(types.InlineKeyboardButton(text="⬅️", callback_data="shop"))
    await c.message.edit_text("🤖 **DRIP ANDROID**", reply_markup=b.as_markup())

# --- ACHIZIȚIE ---
@dp.callback_query(F.data.startswith("buy_"))
async def handle_buy(c: types.CallbackQuery):
    prod = c.data.replace("buy_", "")
    uid = c.from_user.id
    bal, _, has_p = get_u(uid)
    
    pret = PRICES.get(prod, 99)
    if has_p and prod != "wknd": pret = max(0, pret - 1) # Reducere 1 EURO

    if bal < pret: return await c.answer(f"❌ Fonduri insuficiente! ({pret}€)", show_alert=True)

    if prod == "wknd":
        if has_p: return await c.answer("Ai deja Weekend Pass activ!", show_alert=True)
        db_query("UPDATE users SET balance = balance - ?, has_weekend_pass = 1 WHERE user_id = ?", (pret, uid))
        await c.message.answer("🎫 **WEEKEND PASS ACTIVAT!**\nAi 1€ reducere la orice produs timp de o săptămână.")
    else:
        key = db_query("SELECT id, key_val FROM keys WHERE type = ? LIMIT 1", (prod,), fetch=True)
        if not key: return await c.answer("❌ STOC EPUIZAT!", show_alert=True)
        db_query("UPDATE users SET balance = balance - ? WHERE user_id = ?", (pret, uid))
        db_query("DELETE FROM keys WHERE id = ?", (key[0],))
        db_query("INSERT INTO orders (user_id, product, key_val, date) VALUES (?, ?, ?, ?)", (uid, prod.upper(), key[1], datetime.now().strftime("%d/%m")))
        await c.message.answer(f"✅ **SUCCES!**\n🔑 Cheie: `{key[1]}`")

    t, k = main_kb(uid)
    await c.message.edit_text(t, reply_markup=k, parse_mode="Markdown")

# --- PROFIL & REINCARCARE ---
@dp.callback_query(F.data == "prof")
async def profile(c: types.CallbackQuery):
    bal, _, has_p = get_u(c.from_user.id)
    orders = db_query("SELECT product, key_val FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT 3", (c.from_user.id,), fetch_all=True)
    history = "\n".join([f"🔹 {o[0]}: `{o[1]}`" for o in orders]) if orders else "Fără achiziții."
    txt = f"👤 **PROFILUL TĂU**\n\n🆔 ID: `{c.from_user.id}`\n💰 Balanță: `{bal} EUR`\n🎫 Pass: {'✅ Activ' if has_p else '❌ Inactiv'}\n\n📜 **ULTIMELE ACHIZIȚII:**\n{history}"
    b = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home"))
    await c.message.edit_text(txt, reply_markup=b.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "reinc")
async def reinc(c: types.CallbackQuery):
    txt = f"💳 **REÎNCĂRCARE CONT**\n\nContact: @zenoficiall\nID-ul tău: `{c.from_user.id}`\n\nMetode: Revolut, Crypto, Paysafe."
    b = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home"))
    await c.message.edit_text(txt, reply_markup=b.as_markup())

@dp.callback_query(F.data == "specials")
async def specials(c: types.CallbackQuery):
    b = InlineKeyboardBuilder()
    b.row(types.InlineKeyboardButton(text="🎫 WEEKEND PASS - 2€", callback_data="buy_wknd"))
    b.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home"))
    await c.message.edit_text("🔥 **OFERTE SPECIALE**\n\nCumpără Weekend Pass cu 2€ și primești **reducere de 1€** la orice cheie cumpărată!", reply_markup=b.as_markup())

# --- ADMIN ---
@dp.message(Command("add"))
async def add(m: types.Message):
    if m.from_user.id == OWNER_ID or get_u(m.from_user.id)[1]:
        try:
            p = m.text.split()
            db_query("UPDATE users SET balance = balance + ? WHERE user_id = ?", (float(p[2]), int(p[1])))
            await m.answer(f"✅ Adăugat {p[2]}€ lui {p[1]}")
        except: pass

async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
