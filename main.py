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

# --- PREȚURI (Trebuie să coincidă cu ID-urile butoanelor) ---
PRICES = {
    "8bp7": 6, "8bp15": 10, "8bp30": 12,
    "elx7": 3, "elx30": 7,
    "zn7": 5, "zn30": 8.5,
    "d1": 4, "d7": 10,
    "f1": 5, "f30": 30,
    "wknd": 2
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
    stat = "👑 OWNER" if uid == OWNER_ID else ("🛠️ ADMIN" if is_adm == 1 else "👤 CLIENT")
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛒 SHOP", callback_data="btn_shop"))
    builder.row(types.InlineKeyboardButton(text="👤 PROFIL", callback_data="btn_prof"), types.InlineKeyboardButton(text="💳 REÎNCĂRCARE", callback_data="btn_reinc"))
    builder.row(types.InlineKeyboardButton(text="🔥 OFERTE", callback_data="btn_specials"))
    if uid == OWNER_ID or is_adm == 1:
        builder.row(types.InlineKeyboardButton(text="⚙️ ADMIN PANEL", callback_data="btn_admin_panel"))
    
    txt = f"🏪 **BLESSED PANELS**\n\n🏆 Grad: `{stat}`\n💰 Balanță: `{bal} EUR`"
    if has_p: txt += "\n🎫 Weekend Pass: ✅ ACTIV (-1€ Reducere)"
    return txt, builder.as_markup()

@dp.message(Command("start"))
async def start(m: types.Message):
    t, k = main_kb(m.from_user.id)
    await m.answer(t, reply_markup=k, parse_mode="Markdown")

@dp.callback_query(F.data == "btn_home")
async def home_cb(c: types.CallbackQuery):
    t, k = main_kb(c.from_user.id)
    await c.message.edit_text(t, reply_markup=k, parse_mode="Markdown")

# --- MENIURI SHOP ---
@dp.callback_query(F.data == "btn_shop")
async def shop_menu(c: types.CallbackQuery):
    b = InlineKeyboardBuilder()
    b.row(types.InlineKeyboardButton(text="🎱 8 Ball Pool", callback_data="go_8bp"))
    b.row(types.InlineKeyboardButton(text="🧪 Elixir External", callback_data="go_elx"))
    b.row(types.InlineKeyboardButton(text="🐉 Zenin PC/Andr", callback_data="go_zn"))
    b.row(types.InlineKeyboardButton(text="🤖 Drip", callback_data="go_dr"), types.InlineKeyboardButton(text="🍎 Fluorite", callback_data="go_fl"))
    b.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="btn_home"))
    await c.message.edit_text("🌀 **ALEGE O CATEGORIE:**", reply_markup=b.as_markup())

@dp.callback_query(F.data.startswith("go_"))
async def sub_menu(c: types.CallbackQuery):
    cat = c.data.replace("go_", "")
    b = InlineKeyboardBuilder()
    if cat == "8bp":
        txt = "🎱 **8 BALL POOL**"
        b.row(types.InlineKeyboardButton(text="7z-6€", callback_data="buy_8bp7"), types.InlineKeyboardButton(text="30z-12€", callback_data="buy_8bp30"))
    elif cat == "elx":
        txt = "🧪 **ELIXIR**"
        b.row(types.InlineKeyboardButton(text="7z-3€", callback_data="buy_elx7"), types.InlineKeyboardButton(text="30z-7€", callback_data="buy_elx30"))
    elif cat == "zn":
        txt = "🐉 **ZENIN**"
        b.row(types.InlineKeyboardButton(text="7z-5€", callback_data="buy_zn7"), types.InlineKeyboardButton(text="30z-8.5€", callback_data="buy_zn30"))
    elif cat == "dr":
        txt = "🤖 **DRIP**"
        b.row(types.InlineKeyboardButton(text="1z-4€", callback_data="buy_d1"), types.InlineKeyboardButton(text="7z-10€", callback_data="buy_d7"))
    elif cat == "fl":
        txt = "🍎 **FLUORITE**"
        b.row(types.InlineKeyboardButton(text="1z-5€", callback_data="buy_f1"), types.InlineKeyboardButton(text="30z-30€", callback_data="buy_f30"))
    
    b.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="btn_shop"))
    await c.message.edit_text(txt, reply_markup=b.as_markup())

# --- !!! FUNCȚIA DE CUMPĂRARE REPARATĂ !!! ---
@dp.callback_query(F.data.startswith("buy_"))
async def process_purchase(c: types.CallbackQuery):
    prod = c.data.replace("buy_", "")
    uid = c.from_user.id
    bal, _, has_p = get_u(uid)
    
    # Preț și reducere
    pret = PRICES.get(prod, 999)
    if has_p and prod != "wknd":
        pret = max(0.5, pret - 1) # Reducere 1€ dacă are Pass

    if bal < pret:
        return await c.answer(f"❌ Fonduri insuficiente! Preț: {pret}€", show_alert=True)

    if prod == "wknd":
        if has_p: return await c.answer("Ai deja Pass-ul activ!", show_alert=True)
        db_query("UPDATE users SET balance = balance - ?, has_weekend_pass = 1 WHERE user_id = ?", (pret, uid))
        await c.answer("🎫 Weekend Pass Activat!", show_alert=True)
    else:
        # Căutăm cheie în stoc
        key = db_query("SELECT id, key_val FROM keys WHERE type = ? LIMIT 1", (prod,), fetch=True)
        if not key:
            return await c.answer("❌ STOC EPUIZAT pentru acest produs!", show_alert=True)
        
        # Procesăm tranzacția
        db_query("UPDATE users SET balance = balance - ? WHERE user_id = ?", (pret, uid))
        db_query("DELETE FROM keys WHERE id = ?", (key[0],))
        db_query("INSERT INTO orders (user_id, product, key_val, date) VALUES (?, ?, ?, ?)", (uid, prod.upper(), key[1], datetime.now().strftime("%d/%m %H:%M")))
        
        await c.message.answer(f"✅ **ACHIZIȚIE REUȘITĂ!**\n\n📦 Produs: `{prod.upper()}`\n🔑 Cheie: `{key[1]}`\n💰 Preț: `{pret} EUR`", parse_mode="Markdown")

    # Refresh meniu
    t, k = main_kb(uid)
    await c.message.edit_text(t, reply_markup=k, parse_mode="Markdown")

# --- ADMIN PANEL & PROFIL ---
@dp.callback_query(F.data == "btn_admin_panel")
async def admin_panel(c: types.CallbackQuery):
    _, is_adm, _ = get_u(c.from_user.id)
    if c.from_user.id == OWNER_ID or is_adm == 1:
        counts = db_query("SELECT type, COUNT(*) FROM keys GROUP BY type", fetch_all=True)
        txt = "📊 **STOC ADMIN:**\n\n"
        if not counts: txt += "Stoc gol ❌"
        else:
            for row in counts: txt += f"🔹 `{row[0]}`: {row[1]} bucăți\n"
        b = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="btn_home"))
        await c.message.edit_text(txt, reply_markup=b.as_markup())

@dp.callback_query(F.data == "btn_prof")
async def profile(c: types.CallbackQuery):
    bal, _, has_p = get_u(c.from_user.id)
    orders = db_query("SELECT product, key_val, date FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT 3", (c.from_user.id,), fetch_all=True)
    hist = "\n".join([f"🔹 {o[2]} - {o[0]}" for o in orders]) if orders else "Nicio achiziție."
    txt = f"👤 **PROFIL**\n🆔 ID: `{c.from_user.id}`\n💰 Balanță: `{bal} EUR`\n🎫 Pass: {'✅' if has_p else '❌'}\n\n📜 **ISTORIC:**\n{hist}"
    await c.message.edit_text(txt, reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️", callback_data="btn_home")).as_markup())

@dp.callback_query(F.data == "btn_reinc")
async def reinc(c: types.CallbackQuery):
    await c.message.edit_text(f"💳 **REÎNCĂRCARE**\nContact: @zenoficiall\nID-ul tău: `{c.from_user.id}`", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️", callback_data="btn_home")).as_markup())

@dp.callback_query(F.data == "btn_specials")
async def spec(c: types.CallbackQuery):
    b = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🎫 WEEKEND PASS - 2€", callback_data="buy_wknd")).row(types.InlineKeyboardButton(text="⬅️", callback_data="btn_home"))
    await c.message.edit_text("🔥 **OFERTE**\n\nWeekend Pass (2€) = -1€ reducere la orice!", reply_markup=b.as_markup())

# --- COMENZI ADMIN (CHAT) ---
@dp.message(Command("addkey"))
async def adm_ak(m: types.Message):
    if m.from_user.id == OWNER_ID or get_u(m.from_user.id)[1]:
        try:
            p = m.text.split(maxsplit=2)
            db_query("INSERT INTO keys (type, key_val) VALUES (?, ?)", (p[1], p[2]))
            await m.answer(f"✅ Adăugat `{p[1]}`")
        except: await m.answer("Format: `/addkey tip cheie`")

@dp.message(Command("add"))
async def adm_ab(m: types.Message):
    if m.from_user.id == OWNER_ID or get_u(m.from_user.id)[1]:
        try:
            p = m.text.split()
            db_query("UPDATE users SET balance = balance + ? WHERE user_id = ?", (float(p[2]), int(p[1])))
            await m.answer(f"✅ Adăugat {p[2]}€")
        except: await m.answer("Format: `/add ID SUMA`")

async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
