import asyncio
import logging
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- CONFIGURAȚIE ---
TOKEN = '8547474775:AAGQ40_r3l3OyYUL6xMaXi-bugGXozNyFkA'
OWNER_ID = 7481370573 

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- BAZA DE DATE ---
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

db_query('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0, is_admin INTEGER DEFAULT 0, has_weekend_pass INTEGER DEFAULT 0)')
db_query('CREATE TABLE IF NOT EXISTS keys (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, key_val TEXT)')
db_query('CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, product TEXT, key_val TEXT, date TEXT)')

# --- NOI PREȚURI (5€ / 8€ / 16€) ---
PRICES = {
    "d1": 5, "d7": 8, "d30": 16,
    "f1": 5, "f7": 8, "f30": 16,
    "wknd": 2
}

def get_u(uid):
    res = db_query("SELECT balance, is_admin, has_weekend_pass FROM users WHERE user_id = ?", (uid,), fetch=True)
    if not res:
        db_query("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (uid,))
        return 0.0, 0, 0
    return res

# --- MENIURI ---
def main_kb(uid):
    bal, is_adm, has_p = get_u(uid)
    is_admin_access = (uid == OWNER_ID or is_adm == 1)
    stat = "👑 OWNER" if uid == OWNER_ID else ("🛠️ ADMIN" if is_adm == 1 else "👤 CLIENT")
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛒 SHOP", callback_data="m_shop"), types.InlineKeyboardButton(text="👤 PROFIL", callback_data="m_prof"))
    builder.row(types.InlineKeyboardButton(text="🔥 OFERTE", callback_data="m_spec"), types.InlineKeyboardButton(text="💳 REÎNCĂRCARE", callback_data="m_reinc"))
    if is_admin_access:
        builder.row(types.InlineKeyboardButton(text="⚙️ ADMIN PANEL", callback_data="m_admin"))
    builder.row(types.InlineKeyboardButton(text="📞 SUPPORT", url="https://t.me/zenoficiall"))
    
    txt = f"🏪 **BLESSED PANELS**\n\n🏆 Grad: `{stat}`\n💰 Balanță: `{bal} EUR`"
    if has_p: txt += "\n🎫 Weekend Pass: ✅ ACTIV (-1€ Reducere)"
    return txt, builder.as_markup()

@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    t, k = main_kb(m.from_user.id)
    await m.answer(t, reply_markup=k, parse_mode="Markdown")

@dp.callback_query(F.data == "m_home")
async def cb_home(c: types.CallbackQuery):
    t, k = main_kb(c.from_user.id)
    await c.message.edit_text(t, reply_markup=k, parse_mode="Markdown")

# --- SHOP ---
@dp.callback_query(F.data == "m_shop")
async def cb_shop(c: types.CallbackQuery):
    b = InlineKeyboardBuilder()
    b.row(types.InlineKeyboardButton(text="🤖 Drip Android", callback_data="cat_dr"))
    b.row(types.InlineKeyboardButton(text="🍎 Fluorite iOS", callback_data="cat_fl"))
    b.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="m_home"))
    await c.message.edit_text("🌀 **ALEGE PRODUSUL:**", reply_markup=b.as_markup())

@dp.callback_query(F.data.startswith("cat_"))
async def cb_category(c: types.CallbackQuery):
    cat = c.data.split("_")[1]
    b = InlineKeyboardBuilder()
    if cat == "dr":
        txt = "🤖 **DRIP ANDROID**"
        b.row(types.InlineKeyboardButton(text="1z - 5€", callback_data="buy_d1"), types.InlineKeyboardButton(text="7z - 8€", callback_data="buy_d7"))
        b.row(types.InlineKeyboardButton(text="30z - 16€", callback_data="buy_d30"))
    elif cat == "fl":
        txt = "🍎 **FLUORITE iOS**"
        b.row(types.InlineKeyboardButton(text="1z - 5€", callback_data="buy_f1"), types.InlineKeyboardButton(text="7z - 8€", callback_data="buy_f7"))
        b.row(types.InlineKeyboardButton(text="30z - 16€", callback_data="buy_f30"))
    
    b.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="m_shop"))
    await c.message.edit_text(txt, reply_markup=b.as_markup())

# --- LOGICA CUMPĂRARE ---
@dp.callback_query(F.data.startswith("buy_"))
async def cb_buy(c: types.CallbackQuery):
    prod = c.data.split("_")[1]
    uid = c.from_user.id
    bal, _, has_p = get_u(uid)
    pret = PRICES.get(prod, 99)
    if has_p and prod != "wknd": pret = max(1.0, pret - 1)

    if bal < pret:
        return await c.answer(f"❌ Fonduri insuficiente! ({pret}€)", show_alert=True)

    if prod == "wknd":
        if has_p: return await c.answer("Ai deja Weekend Pass activ!", show_alert=True)
        db_query("UPDATE users SET balance = balance - ?, has_weekend_pass = 1 WHERE user_id = ?", (pret, uid))
        await c.answer("🎫 Weekend Pass Activat!", show_alert=True)
    else:
        key = db_query("SELECT id, key_val FROM keys WHERE type = ? LIMIT 1", (prod,), fetch=True)
        if not key: return await c.answer("❌ STOC EPUIZAT!", show_alert=True)
        
        db_query("UPDATE users SET balance = balance - ? WHERE user_id = ?", (pret, uid))
        db_query("DELETE FROM keys WHERE id = ?", (key[0],))
        db_query("INSERT INTO orders (user_id, product, key_val, date) VALUES (?, ?, ?, ?)", (uid, prod.upper(), key[1], datetime.now().strftime("%d/%m %H:%M")))
        await c.message.answer(f"✅ **ACHIZIȚIE REUȘITĂ!**\n🔑 Cheie: `{key[1]}`\n💰 Preț achitat: {pret}€")

    t, k = main_kb(uid)
    await c.message.edit_text(t, reply_markup=k, parse_mode="Markdown")

# --- ADMIN COMMANDS ---
@dp.message(Command("setadmin"))
async def cmd_setadmin(m: types.Message):
    if m.from_user.id == OWNER_ID:
        try:
            tid = int(m.text.split()[1])
            db_query("UPDATE users SET is_admin = 1 WHERE user_id = ?", (tid,))
            await m.answer(f"✅ User `{tid}` promovat ca ADMIN.")
            try: await bot.send_message(tid, "🛠️ Ai primit gradul de ADMIN! Scrie /start.")
            except: pass
        except: await m.answer("Format: `/setadmin ID`")

@dp.message(Command("addkey"))
async def cmd_addkey(m: types.Message):
    _, is_adm, _ = get_u(m.from_user.id)
    if m.from_user.id == OWNER_ID or is_adm == 1:
        try:
            parts = m.text.split(maxsplit=2)
            db_query("INSERT INTO keys (type, key_val) VALUES (?, ?)", (parts[1], parts[2]))
            await m.answer(f"✅ Adăugat în stoc: `{parts[1]}`")
        except: await m.answer("Format: `/addkey tip cheie` (ex: `/addkey d1 ABC`)")

@dp.message(Command("add"))
async def cmd_addbal(m: types.Message):
    _, is_adm, _ = get_u(m.from_user.id)
    if m.from_user.id == OWNER_ID or is_adm == 1:
        try:
            p = m.text.split()
            db_query("UPDATE users SET balance = balance + ? WHERE user_id = ?", (float(p[2]), int(p[1])))
            await m.answer(f"✅ Adăugat {p[2]}€ utilizatorului `{p[1]}`.")
        except: await m.answer("Format: `/add ID SUMA`")

# --- ALTE SECȚIUNI ---
@dp.callback_query(F.data == "m_admin")
async def cb_admin_panel(c: types.CallbackQuery):
    counts = db_query("SELECT type, COUNT(*) FROM keys GROUP BY type", fetch_all=True)
    txt = "📊 **STOC ACTIV:**\n\n"
    if not counts: txt += "Fără chei în bază. ❌"
    for row in counts: txt += f"🔹 `{row[0]}`: {row[1]} buc\n"
    b = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="m_home"))
    await c.message.edit_text(txt, reply_markup=b.as_markup())

@dp.callback_query(F.data == "m_prof")
async def cb_prof(c: types.CallbackQuery):
    bal, _, has_p = get_u(c.from_user.id)
    orders = db_query("SELECT product, key_val FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT 3", (c.from_user.id,), fetch_all=True)
    hist = "\n".join([f"🔹 {o[0]}: `{o[1]}`" for o in orders]) if orders else "Niciuna."
    txt = f"👤 **PROFIL**\n🆔 ID: `{c.from_user.id}`\n💰 Balanță: `{bal}€`\n🎫 Pass: {'✅' if has_p else '❌'}\n\n📜 **ISTORIC:**\n{hist}"
    await c.message.edit_text(txt, reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="m_home")).as_markup())

@dp.callback_query(F.data == "m_reinc")
async def cb_reinc(c: types.CallbackQuery):
    await c.message.edit_text(f"💳 **REÎNCĂRCARE**\nContact: @zenoficiall\nID: `{c.from_user.id}`", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="m_home")).as_markup())

@dp.callback_query(F.data == "m_spec")
async def cb_spec(c: types.CallbackQuery):
    b = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🎫 CUMPĂRĂ PASS - 2€", callback_data="buy_wknd")).row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="m_home"))
    await c.message.edit_text("🔥 **OFERTE**\n\nWeekend Pass (2€) = -1€ reducere la orice!", reply_markup=b.as_markup())

async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
