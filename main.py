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

# --- MENIURI PRINCIPALE ---
def main_kb(uid):
    bal, is_adm, has_p = get_u(uid)
    stat = "👑 OWNER" if uid == OWNER_ID else ("🛠️ ADMIN" if is_adm else "👤 CLIENT")
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛒 SHOP", callback_data="open_shop"), types.InlineKeyboardButton(text="👤 PROFIL", callback_data="prof"))
    builder.row(types.InlineKeyboardButton(text="🔥 OFERTE", callback_data="specials"), types.InlineKeyboardButton(text="💳 REÎNCĂRCARE", callback_data="reinc"))
    builder.row(types.InlineKeyboardButton(text="📞 SUPPORT", url="https://t.me/zenoficiall"))
    if uid == OWNER_ID or is_adm:
        builder.row(types.InlineKeyboardButton(text="⚙️ ADMIN PANEL", callback_data="admin_stock"))
    txt = f"🏪 **BLESSED PANELS**\n\n🏆 Grad: `{stat}`\n💰 Balanță: `{bal} EUR`"
    if has_p: txt += "\n🎫 Weekend Pass: ✅ ACTIV (-1€ Reducere)"
    return txt, builder.as_markup()

@dp.message(Command("start"))
async def start(m: types.Message):
    t, k = main_kb(m.from_user.id)
    await m.answer(t, reply_markup=k, parse_mode="Markdown")

@dp.callback_query(F.data == "home")
async def home_cb(c: types.CallbackQuery):
    t, k = main_kb(c.from_user.id)
    await c.message.edit_text(t, reply_markup=k, parse_mode="Markdown")

# --- MENIU SHOP ---
@dp.callback_query(F.data == "open_shop")
async def shop_menu(c: types.CallbackQuery):
    b = InlineKeyboardBuilder()
    b.row(types.InlineKeyboardButton(text="🎱 8 Ball Pool", callback_data="go_8bp"))
    b.row(types.InlineKeyboardButton(text="🧪 Elixir External", callback_data="go_elixir"))
    b.row(types.InlineKeyboardButton(text="🐉 Zenin PC/Android", callback_data="go_zenin"))
    b.row(types.InlineKeyboardButton(text="🤖 Drip", callback_data="go_drip"), types.InlineKeyboardButton(text="🍎 Fluorite", callback_data="go_fluorite"))
    b.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home"))
    await c.message.edit_text("🌀 **ALEGE O CATEGORIE:**", reply_markup=b.as_markup())

# --- SUB-MENIURI PRODUSE ---
@dp.callback_query(F.data == "go_8bp")
async def sub_8bp(c: types.CallbackQuery):
    b = InlineKeyboardBuilder()
    b.row(types.InlineKeyboardButton(text="7z - 6€", callback_data="buy_8bp7"), types.InlineKeyboardButton(text="15z - 10€", callback_data="buy_8bp15"))
    b.row(types.InlineKeyboardButton(text="30z - 12€", callback_data="buy_8bp30"), types.InlineKeyboardButton(text="⬅️", callback_data="open_shop"))
    await c.message.edit_text("🎱 **8 BALL POOL PSHX4**", reply_markup=b.as_markup())

@dp.callback_query(F.data == "go_elixir")
async def sub_elixir(c: types.CallbackQuery):
    b = InlineKeyboardBuilder()
    b.row(types.InlineKeyboardButton(text="7z - 3€", callback_data="buy_elx7"), types.InlineKeyboardButton(text="14z - 6€", callback_data="buy_elx14"))
    b.row(types.InlineKeyboardButton(text="30z - 7€", callback_data="buy_elx30"), types.InlineKeyboardButton(text="⬅️", callback_data="open_shop"))
    await c.message.edit_text("🧪 **ELIXIR ANDROID EXTERNAL**", reply_markup=b.as_markup())

@dp.callback_query(F.data == "go_zenin")
async def sub_zenin(c: types.CallbackQuery):
    b = InlineKeyboardBuilder()
    b.row(types.InlineKeyboardButton(text="7z - 5€", callback_data="buy_zn7"), types.InlineKeyboardButton(text="30z - 8.5€", callback_data="buy_zn30"))
    b.row(types.InlineKeyboardButton(text="60z - 15€", callback_data="buy_zn60"), types.InlineKeyboardButton(text="⬅️", callback_data="open_shop"))
    await c.message.edit_text("🐉 **ZENIN PC-ANDROID-EXTERNAL**", reply_markup=b.as_markup())

@dp.callback_query(F.data == "go_drip")
async def sub_drip(c: types.CallbackQuery):
    b = InlineKeyboardBuilder()
    b.row(types.InlineKeyboardButton(text="1z - 4€", callback_data="buy_d1"), types.InlineKeyboardButton(text="7z - 10€", callback_data="buy_d7"))
    b.row(types.InlineKeyboardButton(text="30z - 25€", callback_data="buy_d30"), types.InlineKeyboardButton(text="⬅️", callback_data="open_shop"))
    await c.message.edit_text("🤖 **DRIP ANDROID**", reply_markup=b.as_markup())

@dp.callback_query(F.data == "go_fluorite")
async def sub_fluor(c: types.CallbackQuery):
    b = InlineKeyboardBuilder()
    b.row(types.InlineKeyboardButton(text="1z - 5€", callback_data="buy_f1"), types.InlineKeyboardButton(text="7z - 12€", callback_data="buy_f7"))
    b.row(types.InlineKeyboardButton(text="30z - 30€", callback_data="buy_f30"), types.InlineKeyboardButton(text="⬅️", callback_data="open_shop"))
    await c.message.edit_text("🍎 **FLUORITE iOS**", reply_markup=b.as_markup())

# --- LOGICA CUMPĂRARE ---
@dp.callback_query(F.data.startswith("buy_"))
async def process_buy(c: types.CallbackQuery):
    prod = c.data.replace("buy_", "")
    uid = c.from_user.id
    bal, _, has_p = get_u(uid)
    pret = PRICES.get(prod, 99)
    if has_p and prod != "wknd": pret = max(0, pret - 1)

    if bal < pret: return await c.answer(f"❌ Ai nevoie de {pret}€!", show_alert=True)
    
    if prod == "wknd":
        db_query("UPDATE users SET balance = balance - ?, has_weekend_pass = 1 WHERE user_id = ?", (pret, uid))
        await c.answer("🎫 Pass Activat!", show_alert=True)
    else:
        key = db_query("SELECT id, key_val FROM keys WHERE type = ? LIMIT 1", (prod,), fetch=True)
        if not key: return await c.answer("❌ STOC EPUIZAT!", show_alert=True)
        db_query("UPDATE users SET balance = balance - ? WHERE user_id = ?", (pret, uid))
        db_query("DELETE FROM keys WHERE id = ?", (key[0],))
        db_query("INSERT INTO orders (user_id, product, key_val, date) VALUES (?, ?, ?, ?)", (uid, prod.upper(), key[1], datetime.now().strftime("%d/%m")))
        await c.message.answer(f"✅ **ACHIZIȚIE REUȘITĂ!**\n🔑 Cheie: `{key[1]}`")
    
    t, k = main_kb(uid)
    await c.message.edit_text(t, reply_markup=k, parse_mode="Markdown")

# --- ADMIN & PROFIL ---
@dp.message(Command("addkey"))
async def adm_addkey(m: types.Message):
    if m.from_user.id == OWNER_ID or get_u(m.from_user.id)[1]:
        try:
            parts = m.text.split(maxsplit=2)
            db_query("INSERT INTO keys (type, key_val) VALUES (?, ?)", (parts[1], parts[2]))
            await m.answer(f"✅ Adăugat `{parts[1]}`")
        except: pass

@dp.message(Command("add"))
async def adm_addbal(m: types.Message):
    if m.from_user.id == OWNER_ID or get_u(m.from_user.id)[1]:
        try:
            p = m.text.split()
            db_query("UPDATE users SET balance = balance + ? WHERE user_id = ?", (float(p[2]), int(p[1])))
            await m.answer("✅ Balanță actualizată!")
        except: pass

@dp.callback_query(F.data == "prof")
async def profile(c: types.CallbackQuery):
    bal, _, has_p = get_u(c.from_user.id)
    txt = f"👤 **PROFIL**\n🆔 ID: `{c.from_user.id}`\n💰 Balanță: `{bal} EUR`\n🎫 Pass: {'✅' if has_p else '❌'}"
    await c.message.edit_text(txt, reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️", callback_data="home")).as_markup())

@dp.callback_query(F.data == "reinc")
async def reinc(c: types.CallbackQuery):
    await c.message.edit_text(f"💳 **REÎNCĂRCARE**\nContact: @zenoficiall\nID: `{c.from_user.id}`", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️", callback_data="home")).as_markup())

@dp.callback_query(F.data == "specials")
async def spec(c: types.CallbackQuery):
    b = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🎫 WEEKEND PASS - 2€", callback_data="buy_wknd")).row(types.InlineKeyboardButton(text="⬅️", callback_data="home"))
    await c.message.edit_text("🔥 **OFERTE**\n\nWeekend Pass (2€) = -1€ reducere!", reply_markup=b.as_markup())

async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
