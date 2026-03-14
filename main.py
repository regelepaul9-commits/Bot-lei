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

# Init Tables
db_query('''CREATE TABLE IF NOT EXISTS users 
            (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0, 
             is_admin INTEGER DEFAULT 0, is_reseller INTEGER DEFAULT 0, has_weekend_pass INTEGER DEFAULT 0)''')
db_query('CREATE TABLE IF NOT EXISTS keys (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, key_val TEXT)')
db_query('CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, product TEXT, key_val TEXT, date TEXT)')

# --- PREȚURI (EURO) ---
PRICES = {
    "d1": 4, "d7": 10, "d30": 25,      # Drip Android
    "f1": 5, "f7": 12, "f30": 30,      # Fluorite iOS
    "8bp7": 6, "8bp15": 10, "8bp30": 12, # 8 Ball
    "elx7": 3, "elx14": 6, "elx30": 7,   # Elixir
    "zn7": 5, "zn30": 8.5, "zn60": 15,   # Zenin
    "wknd": 5                          # Weekend Pass
}

def get_user_data(uid):
    res = db_query("SELECT balance, is_admin, has_weekend_pass FROM users WHERE user_id = ?", (uid,), fetch=True)
    if not res:
        db_query("INSERT INTO users (user_id) VALUES (?)", (uid,))
        return 0.0, 0, 0
    return res

# --- MENIURI ---
def main_kb(uid):
    bal, is_admin, has_pass = get_user_data(uid)
    status = "👑 OWNER" if uid == OWNER_ID else ("🛠️ ADMIN" if is_admin else "👤 CLIENT")
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛒 SHOP", callback_data="shop"), types.InlineKeyboardButton(text="👤 PROFIL", callback_data="profile"))
    builder.row(types.InlineKeyboardButton(text="🔥 OFERTE", callback_data="specials"), types.InlineKeyboardButton(text="💳 REÎNCĂRCARE", callback_data="add_info"))
    builder.row(types.InlineKeyboardButton(text="📞 SUPPORT", url="https://t.me/zenoficiall"))
    
    txt = f"🏪 **BLESSED PANELS**\n\n🏆 Grad: `{status}`\n💰 Balanță: `{bal} EUR`"
    if has_pass: txt += "\n🎫 Weekend Pass: ✅ ACTIV (-5 EUR)"
    txt += f"\n🆔 ID: `{uid}`"
    return txt, builder.as_markup()

# --- HANDLERS ---
@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    await m.answer(*main_kb(m.from_user.id), parse_mode="Markdown")

@dp.callback_query(F.data == "shop")
async def shop_menu(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🤖 Android (Drip)", callback_data="cat_drip"))
    builder.row(types.InlineKeyboardButton(text="🍎 iOS (Fluorite)", callback_data="cat_fluorite"))
    builder.row(types.InlineKeyboardButton(text="🎱 8 Ball Pool PSHX4", callback_data="cat_8bp"))
    builder.row(types.InlineKeyboardButton(text="🧪 Elixir External", callback_data="cat_elx"))
    builder.row(types.InlineKeyboardButton(text="🐉 Zenin Android/PC", callback_data="cat_zn"))
    builder.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home"))
    await call.message.edit_text("🌀 **CATEGORII PRODUSE:**", reply_markup=builder.as_markup())

# --- CATEGORII DETALIATE ---
@dp.callback_query(F.data == "cat_drip")
async def cat_drip(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="1 Zi - 4€", callback_data="buy_d1"), types.InlineKeyboardButton(text="7 Zile - 10€", callback_data="buy_d7"))
    builder.row(types.InlineKeyboardButton(text="30 Zile - 25€", callback_data="buy_d30"))
    builder.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="shop"))
    await call.message.edit_text("🤖 **Drip Android Options:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "cat_fluorite")
async def cat_fluorite(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="1 Zi - 5€", callback_data="buy_f1"), types.InlineKeyboardButton(text="7 Zile - 12€", callback_data="buy_f7"))
    builder.row(types.InlineKeyboardButton(text="30 Zile - 30€", callback_data="buy_f30"))
    builder.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="shop"))
    await call.message.edit_text("🍎 **Fluorite iOS Options:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "cat_8bp")
async def cat_8ball(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="7z - 6€", callback_data="buy_8bp7"), types.InlineKeyboardButton(text="15z - 10€", callback_data="buy_8bp15"))
    builder.row(types.InlineKeyboardButton(text="30z - 12€", callback_data="buy_8bp30"))
    builder.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="shop"))
    await call.message.edit_text("🎱 **8 Ball Pool PSHX4**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "cat_elx")
async def cat_elixir(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="7z - 3€", callback_data="buy_elx7"), types.InlineKeyboardButton(text="14z - 6€", callback_data="buy_elx14"))
    builder.row(types.InlineKeyboardButton(text="30z - 7€", callback_data="buy_elx30"))
    builder.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="shop"))
    await call.message.edit_text("🧪 **Elixir External**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "cat_zn")
async def cat_zenin(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="7z - 5€", callback_data="buy_zn7"), types.InlineKeyboardButton(text="30z - 8.5€", callback_data="buy_zn30"))
    builder.row(types.InlineKeyboardButton(text="60z - 15€", callback_data="buy_zn60"))
    builder.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="shop"))
    await call.message.edit_text("🐉 **ZeninPC-ANDROID-EXTERNAL**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("buy_"))
async def handle_buy(call: types.CallbackQuery):
    prod = call.data.replace("buy_", "")
    uid = call.from_user.id
    bal, _, has_pass = get_user_data(uid)
    pret = PRICES.get(prod, 999)
    if has_pass and prod != "wknd": pret = max(1, pret - 5)

    if bal < pret: return await call.answer(f"❌ Fonduri insuficiente ({pret}€)!", show_alert=True)

    key = db_query("SELECT id, key_val FROM keys WHERE type = ? LIMIT 1", (prod,), fetch=True)
    if not key: return await call.answer("❌ STOC EPUIZAT!", show_alert=True)
    
    db_query("UPDATE users SET balance = balance - ? WHERE user_id = ?", (pret, uid))
    db_query("DELETE FROM keys WHERE id = ?", (key[0],))
    db_query("INSERT INTO orders (user_id, product, key_val, date) VALUES (?, ?, ?, ?)", (uid, prod.upper(), key[1], datetime.now().strftime("%d/%m")))
    await call.message.answer(f"✅ **CUMPĂRARE REUȘITĂ!**\n🔑 Cheie: `{key[1]}`")
    await call.message.edit_text(*main_kb(uid), parse_mode="Markdown")

# --- ADMIN COMMANDS ---
@dp.message(Command("add"))
async def add_bal(m: types.Message):
    _, is_admin, _ = get_user_data(m.from_user.id)
    if m.from_user.id == OWNER_ID or is_admin:
        try:
            p = m.text.split()
            db_query("UPDATE users SET balance = balance + ? WHERE user_id = ?", (float(p[2]), int(p[1])))
            await m.answer(f"✅ Adăugat {p[2]}€ lui `{p[1]}`")
        except: pass

@dp.message(Command("addkey"))
async def add_key_adm(m: types.Message):
    _, is_admin, _ = get_user_data(m.from_user.id)
    if m.from_user.id == OWNER_ID or is_admin:
        try:
            p = m.text.split()
            db_query("INSERT INTO keys (type, key_val) VALUES (?, ?)", (p[1], p[2]))
            await m.answer(f"✅ Cheie {p[1]} adăugată!")
        except: pass

@dp.message(Command("setadmin"))
async def set_admin(m: types.Message):
    if m.from_user.id == OWNER_ID:
        try:
            tid = int(m.text.split()[1])
            db_query("UPDATE users SET is_admin = 1 WHERE user_id = ?", (tid,))
            await m.answer(f"🛠️ `{tid}` este acum ADMIN.")
        except: pass

@dp.callback_query(F.data == "home")
async def home_cb(call: types.CallbackQuery):
    await call.message.edit_text(*main_kb(call.from_user.id), parse_mode="Markdown")

@dp.callback_query(F.data == "add_info")
async def add_info(call: types.CallbackQuery):
    await call.message.edit_text(f"💳 **REÎNCĂRCARE CONT**\n\nContactează: @zenoficiall\nID-ul tău: `{call.from_user.id}`\n\nMetode: Revolut, Crypto, Paysafe.", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home")).as_markup())

async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
