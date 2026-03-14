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

def get_u(uid):
    res = db_query("SELECT balance, is_admin, has_weekend_pass FROM users WHERE user_id = ?", (uid,), fetch=True)
    if not res:
        db_query("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (uid,))
        return 0.0, 0, 0
    return res

# --- MENIURI (Aici am verificat toate "callback_data") ---
def main_kb(uid):
    bal, is_adm, has_p = get_u(uid)
    is_really_admin = (uid == OWNER_ID or is_adm == 1)
    
    stat = "👑 OWNER" if uid == OWNER_ID else ("🛠️ ADMIN" if is_adm == 1 else "👤 CLIENT")
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛒 SHOP", callback_data="btn_shop"))
    builder.row(types.InlineKeyboardButton(text="👤 PROFIL", callback_data="btn_prof"), types.InlineKeyboardButton(text="💳 REÎNCĂRCARE", callback_data="btn_reinc"))
    builder.row(types.InlineKeyboardButton(text="🔥 OFERTE", callback_data="btn_specials"))
    
    if is_really_admin:
        builder.row(types.InlineKeyboardButton(text="⚙️ ADMIN PANEL", callback_data="btn_admin_panel"))
    
    builder.row(types.InlineKeyboardButton(text="📞 SUPPORT", url="https://t.me/zenoficiall"))
    
    txt = f"🏪 **BLESSED PANELS**\n\n🏆 Grad: `{stat}`\n💰 Balanță: `{bal} EUR`"
    if has_p: txt += "\n🎫 Weekend Pass: ✅ ACTIV"
    return txt, builder.as_markup()

# --- HANDLERS COMANDA START ---
@dp.message(Command("start"))
async def start(m: types.Message):
    t, k = main_kb(m.from_user.id)
    await m.answer(t, reply_markup=k, parse_mode="Markdown")

# --- HANDLER PENTRU BUTONUL HOME ---
@dp.callback_query(F.data == "btn_home")
async def home_cb(c: types.CallbackQuery):
    t, k = main_kb(c.from_user.id)
    await c.message.edit_text(t, reply_markup=k, parse_mode="Markdown")

# --- MENIU SHOP ---
@dp.callback_query(F.data == "btn_shop")
async def shop_menu(c: types.CallbackQuery):
    b = InlineKeyboardBuilder()
    b.row(types.InlineKeyboardButton(text="🎱 8 Ball Pool", callback_data="go_8bp"))
    b.row(types.InlineKeyboardButton(text="🧪 Elixir External", callback_data="go_elx"))
    b.row(types.InlineKeyboardButton(text="🐉 Zenin PC/Andr", callback_data="go_zn"))
    b.row(types.InlineKeyboardButton(text="🤖 Drip", callback_data="go_dr"), types.InlineKeyboardButton(text="🍎 Fluorite", callback_data="go_fl"))
    b.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="btn_home"))
    await c.message.edit_text("🌀 **ALEGE O CATEGORIE:**", reply_markup=b.as_markup())

# --- HANDLERS SUB-CATEGORII (8ball, Zenin, etc.) ---
@dp.callback_query(F.data.startswith("go_"))
async def sub_menu(c: types.CallbackQuery):
    cat = c.data.replace("go_", "")
    b = InlineKeyboardBuilder()
    
    if cat == "8bp":
        txt = "🎱 **8 BALL POOL PSHX4**"
        b.row(types.InlineKeyboardButton(text="7z-6€", callback_data="buy_8bp7"), types.InlineKeyboardButton(text="15z-10€", callback_data="buy_8bp15"))
        b.row(types.InlineKeyboardButton(text="30z-12€", callback_data="buy_8bp30"))
    elif cat == "elx":
        txt = "🧪 **ELIXIR ANDROID EXTERNAL**"
        b.row(types.InlineKeyboardButton(text="7z-3€", callback_data="buy_elx7"), types.InlineKeyboardButton(text="30z-7€", callback_data="buy_elx30"))
    elif cat == "zn":
        txt = "🐉 **ZENIN PC/ANDROID**"
        b.row(types.InlineKeyboardButton(text="7z-5€", callback_data="buy_zn7"), types.InlineKeyboardButton(text="30z-8.5€", callback_data="buy_zn30"))
    elif cat == "dr":
        txt = "🤖 **DRIP ANDROID**"
        b.row(types.InlineKeyboardButton(text="1z-4€", callback_data="buy_d1"), types.InlineKeyboardButton(text="7z-10€", callback_data="buy_d7"))
    elif cat == "fl":
        txt = "🍎 **FLUORITE iOS**"
        b.row(types.InlineKeyboardButton(text="1z-5€", callback_data="buy_f1"), types.InlineKeyboardButton(text="30z-30€", callback_data="buy_f30"))
    
    b.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="btn_shop"))
    await c.message.edit_text(txt, reply_markup=b.as_markup())

# --- ADMIN PANEL (Reparat) ---
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
    else:
        await c.answer("Fără acces!", show_alert=True)

# --- PROFIL, REINCARCARE, SPECIALS ---
@dp.callback_query(F.data == "btn_prof")
async def profile(c: types.CallbackQuery):
    bal, _, has_p = get_u(c.from_user.id)
    txt = f"👤 **PROFIL**\n\n🆔 ID: `{c.from_user.id}`\n💰 Balanță: `{bal} EUR`"
    b = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="btn_home"))
    await c.message.edit_text(txt, reply_markup=b.as_markup())

@dp.callback_query(F.data == "btn_reinc")
async def reinc(c: types.CallbackQuery):
    txt = f"💳 **REÎNCĂRCARE**\n\nContact: @zenoficiall\nID-ul tău: `{c.from_user.id}`"
    b = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="btn_home"))
    await c.message.edit_text(txt, reply_markup=b.as_markup())

# --- COMENZI ADMIN (CHAT) ---
@dp.message(Command("setadmin"))
async def set_adm(m: types.Message):
    if m.from_user.id == OWNER_ID:
        try:
            tid = int(m.text.split()[1])
            db_query("UPDATE users SET is_admin = 1 WHERE user_id = ?", (tid,))
            await m.answer(f"✅ User {tid} este acum ADMIN.")
        except: await m.answer("Format: `/setadmin ID`")

@dp.message(Command("add"))
async def add_b(m: types.Message):
    _, is_adm, _ = get_u(m.from_user.id)
    if m.from_user.id == OWNER_ID or is_adm == 1:
        try:
            p = m.text.split()
            db_query("UPDATE users SET balance = balance + ? WHERE user_id = ?", (float(p[2]), int(p[1])))
            await m.answer("✅ Balanță adăugată.")
        except: await m.answer("Format: `/add ID SUMA`")

async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
