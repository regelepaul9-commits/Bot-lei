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

# Init Tables
db_query('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0, is_admin INTEGER DEFAULT 0, has_weekend_pass INTEGER DEFAULT 0)')
db_query('CREATE TABLE IF NOT EXISTS keys (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, key_val TEXT)')
db_query('CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, product TEXT, key_val TEXT, date TEXT)')

# --- PREȚURI EURO ---
PRICES = {
    "d1": 4, "d7": 10, "d30": 25, "f1": 5, "f7": 12, "f30": 30,
    "8bp7": 6, "8bp15": 10, "8bp30": 12, "elx7": 3, "elx14": 6, "elx30": 7,
    "zn7": 5, "zn30": 8.5, "zn60": 15, "wknd": 2
}

def get_u(uid):
    res = db_query("SELECT balance, is_admin, has_weekend_pass FROM users WHERE user_id = ?", (uid,), fetch=True)
    if not res:
        db_query("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (uid,))
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
    
    if uid == OWNER_ID or is_adm:
        builder.row(types.InlineKeyboardButton(text="⚙️ ADMIN PANEL", callback_data="admin_stock"))
    
    txt = f"🏪 **BLESSED PANELS**\n\n🏆 Grad: `{stat}`\n💰 Balanță: `{bal} EUR`"
    if has_p: txt += "\n🎫 Weekend Pass: ✅ ACTIV (-1€ Reducere)"
    return txt, builder.as_markup()

# --- ADMIN COMMANDS ---
@dp.message(Command("setadmin"))
async def set_admin_cmd(m: types.Message):
    if m.from_user.id == OWNER_ID:
        try:
            target_id = int(m.text.split()[1])
            db_query("UPDATE users SET is_admin = 1 WHERE user_id = ?", (target_id,))
            await m.answer(f"✅ Utilizatorul `{target_id}` a primit rolul de **ADMIN**.")
        except:
            await m.answer("Format: `/setadmin ID`")

@dp.message(Command("addkey"))
async def add_key_cmd(m: types.Message):
    _, is_adm, _ = get_u(m.from_user.id)
    if m.from_user.id == OWNER_ID or is_adm:
        try:
            parts = m.text.split(maxsplit=2)
            db_query("INSERT INTO keys (type, key_val) VALUES (?, ?)", (parts[1], parts[2]))
            await m.answer(f"✅ Cheie `{parts[1]}` adăugată!")
        except:
            await m.answer("Format: `/addkey tip cheie` (ex: `/addkey 8bp7 ABC-123`)")

@dp.message(Command("add"))
async def add_bal_cmd(m: types.Message):
    _, is_adm, _ = get_u(m.from_user.id)
    if m.from_user.id == OWNER_ID or is_adm:
        try:
            p = m.text.split()
            db_query("UPDATE users SET balance = balance + ? WHERE user_id = ?", (float(p[2]), int(p[1])))
            await m.answer(f"✅ Adăugat {p[2]}€ utilizatorului `{p[1]}`")
        except:
            await m.answer("Format: `/add ID SUMA`")

# --- HANDLERS (Shop & Navigare) ---
@dp.message(Command("start"))
async def start(m: types.Message):
    t, k = main_kb(m.from_user.id)
    await m.answer(t, reply_markup=k, parse_mode="Markdown")

@dp.callback_query(F.data == "home")
async def home_cb(c: types.CallbackQuery):
    t, k = main_kb(c.from_user.id)
    await c.message.edit_text(t, reply_markup=k, parse_mode="Markdown")

@dp.callback_query(F.data == "admin_stock")
async def view_stock(c: types.CallbackQuery):
    counts = db_query("SELECT type, COUNT(*) FROM keys GROUP BY type", fetch_all=True)
    txt = "📊 **PANEL ADMIN - STOC:**\n\n"
    if not counts: txt += "Stoc gol ❌"
    for row in counts: txt += f"🔹 `{row[0]}`: {row[1]} bucăți\n"
    txt += "\n💡 *Poți folosi /add și /addkey direct în chat.*"
    b = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home"))
    await c.message.edit_text(txt, reply_markup=b.as_markup(), parse_mode="Markdown")

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
    await c.message.edit_text("🎱 **8 BALL POOL**", reply_markup=b.as_markup())

@dp.callback_query(F.data.startswith("buy_"))
async def handle_buy(c: types.CallbackQuery):
    prod = c.data.replace("buy_", "")
    uid = c.from_user.id
    bal, _, has_p = get_u(uid)
    pret = PRICES.get(prod, 99)
    if has_p and prod != "wknd": pret = max(0, pret - 1)
    if bal < pret: return await c.answer(f"❌ Ai nevoie de {pret}€!", show_alert=True)
    
    if prod == "wknd":
        db_query("UPDATE users SET balance = balance - ?, has_weekend_pass = 1 WHERE user_id = ?", (pret, uid))
        await c.message.answer("🎫 **PASS ACTIVAT!**")
    else:
        key = db_query("SELECT id, key_val FROM keys WHERE type = ? LIMIT 1", (prod,), fetch=True)
        if not key: return await c.answer("❌ STOC EPUIZAT!", show_alert=True)
        db_query("UPDATE users SET balance = balance - ? WHERE user_id = ?", (pret, uid))
        db_query("DELETE FROM keys WHERE id = ?", (key[0],))
        db_query("INSERT INTO orders (user_id, product, key_val, date) VALUES (?, ?, ?, ?)", (uid, prod.upper(), key[1], datetime.now().strftime("%d/%m")))
        await c.message.answer(f"✅ **SUCCES!**\n🔑 Cheie: `{key[1]}`")
    t, k = main_kb(uid)
    await c.message.edit_text(t, reply_markup=k, parse_mode="Markdown")

@dp.callback_query(F.data == "prof")
async def profile(c: types.CallbackQuery):
    bal, _, has_p = get_u(c.from_user.id)
    orders = db_query("SELECT product, key_val FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT 3", (c.from_user.id,), fetch_all=True)
    history = "\n".join([f"🔹 {o[0]}: `{o[1]}`" for o in orders]) if orders else "Fără achiziții."
    await c.message.edit_text(f"👤 **PROFIL**\n\n🆔 ID: `{c.from_user.id}`\n💰 Balanță: `{bal} EUR`\n🎫 Pass: {'✅' if has_p else '❌'}\n\n📜 **ISTORIC:**\n{history}", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️", callback_data="home")).as_markup())

@dp.callback_query(F.data == "reinc")
async def reinc(c: types.CallbackQuery):
    await c.message.edit_text(f"💳 **REÎNCĂRCARE**\nContact: @zenoficiall\nID: `{c.from_user.id}`", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️", callback_data="home")).as_markup())

@dp.callback_query(F.data == "specials")
async def specials(c: types.CallbackQuery):
    b = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🎫 WEEKEND PASS - 2€", callback_data="buy_wknd")).row(types.InlineKeyboardButton(text="⬅️", callback_data="home"))
    await c.message.edit_text("🔥 **OFERTE**\n\nWeekend Pass (2€) = -1€ reducere la orice cheie!", reply_markup=b.as_markup())

async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
