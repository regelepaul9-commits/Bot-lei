import asyncio
import logging
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# --- CONFIGURARE ---
TOKEN = '8547474775:AAGQ40_r3l3OyYUL6xMaXi-bugGXozNyFkA'
ADMIN_ID = 7481370573 

bot = Bot(token=TOKEN)
dp = Dispatcher()

class ClientApply(StatesGroup):
    q1 = State()

# --- DATABASE ENGINE ---
def db_query(query, params=(), fetch=False, fetch_all=False):
    conn = sqlite3.connect('database.db', timeout=10)
    cursor = conn.cursor()
    cursor.execute(query, params)
    res = None
    if fetch: res = cursor.fetchone()
    if fetch_all: res = cursor.fetchall()
    conn.commit()
    conn.close()
    return res

# Inițializare tabele
db_query('''CREATE TABLE IF NOT EXISTS users 
            (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0, 
             is_reseller INTEGER DEFAULT 0, has_weekend_pass INTEGER DEFAULT 0, 
             is_approved INTEGER DEFAULT 0, joined_date TEXT)''')
db_query('CREATE TABLE IF NOT EXISTS keys (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, key_val TEXT)')
db_query('CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, product TEXT, key_val TEXT, date TEXT)')

# Adăugăm cheia ta dacă lipsește
check_key = db_query("SELECT id FROM keys WHERE key_val = ?", ('7048507851',), fetch=True)
if not check_key:
    db_query("INSERT INTO keys (type, key_val) VALUES (?, ?)", ('d1', '7048507851'))

def get_user_info(uid):
    user = db_query("SELECT balance, is_reseller, has_weekend_pass, is_approved, joined_date FROM users WHERE user_id = ?", (uid,), fetch=True)
    if not user:
        now = datetime.now().strftime("%d/%m/%Y")
        db_query("INSERT INTO users (user_id, joined_date) VALUES (?, ?)", (uid, now))
        return (0.0, 0, 0, 0, now)
    return user

# --- MENIURI ---
def main_menu_keyboard(uid):
    bal, is_reseller, has_pass, is_approved, _ = get_user_info(uid)
    status = "👑 OWNER" if uid == ADMIN_ID else ("⭐ Reseller" if is_reseller else "👤 Client")
    
    builder = InlineKeyboardBuilder()
    if not is_approved and uid != ADMIN_ID:
        builder.row(types.InlineKeyboardButton(text="📝 Aplică pentru Acces", callback_data="apply_client"))
        text = "🔒 **ACCES RESTRICȚIONAT**\n\nTrebuie să aplici pentru a vedea magazinul."
    else:
        builder.row(types.InlineKeyboardButton(text="🛒 SHOP", callback_data="shop"), types.InlineKeyboardButton(text="👤 PROFIL", callback_data="profile"))
        builder.row(types.InlineKeyboardButton(text="🔥 OFERTE", callback_data="specials"), types.InlineKeyboardButton(text="💼 RESELLER", callback_data="reseller"))
        builder.row(types.InlineKeyboardButton(text="💳 ADAUGĂ BANI", callback_data="add_info"))
        builder.row(types.InlineKeyboardButton(text="📞 SUPPORT", url="https://t.me/zenoficiall"))
        pass_txt = "\n🎫 Weekend Pass: ✅ ACTIV" if has_pass else ""
        text = f"🏪 **BLESSED PANELS**\n\n🦁 Balanță: `{bal} LEI`\n🏆 Status: `{status}`{pass_txt}"
    return text, builder.as_markup()

# --- HANDLERE ---
@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    text, markup = main_menu_keyboard(m.from_user.id)
    await m.answer(text, reply_markup=markup, parse_mode="Markdown")

@dp.callback_query(F.data == "profile")
async def profile_menu(call: types.CallbackQuery):
    uid = call.from_user.id
    bal, is_reseller, has_pass, _, joined = get_user_info(uid)
    orders = db_query("SELECT product, key_val, date FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT 5", (uid,), fetch_all=True)
    
    history = "\n".join([f"🔹 {o[0]} - `{o[1]}` ({o[2]})" for o in orders]) if orders else "Nicio achiziție momentan."
    
    text = (f"👤 **PROFILUL TĂU**\n\n"
            f"📅 Membru din: `{joined}`\n"
            f"💰 Balanță: `{bal} LEI`\n"
            f"🎫 Weekend Pass: {'✅ Da' if has_pass else '❌ Nu'}\n\n"
            f"📜 **ULTIMELE 5 CHEI CUMPĂRATE:**\n{history}")
    
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home"))
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.message(Command("add"))
async def add_money(m: types.Message):
    if m.from_user.id != ADMIN_ID: return
    try:
        parts = m.text.split()
        target_id, suma = int(parts[1]), float(parts[2])
        get_user_info(target_id)
        db_query("UPDATE users SET balance = balance + ?, is_approved = 1 WHERE user_id = ?", (suma, target_id))
        new_bal = db_query("SELECT balance FROM users WHERE user_id = ?", (target_id,), fetch=True)[0]
        await m.answer(f"✅ Balanță: `{new_bal} LEI` pentru `{target_id}`")
        try: await bot.send_message(target_id, f"💳 Ai primit `{suma} LEI`!")
        except: pass
    except: await m.answer("Sintaxă: `/add ID SUMA`")

@dp.callback_query(F.data == "buy_d1")
async def buy_drip_1d(call: types.CallbackQuery):
    uid = call.from_user.id
    bal, _, has_pass, _, _ = get_user_info(uid)
    pret = 20 - (3 if has_pass else 0)
    
    if bal < pret: return await call.answer(f"❌ Ai nevoie de {pret} LEI!", show_alert=True)
    
    key = db_query("SELECT id, key_val FROM keys WHERE type = 'd1' LIMIT 1", fetch=True)
    if not key: return await call.answer("❌ STOC EPUIZAT!", show_alert=True)
    
    now = datetime.now().strftime("%d/%m %H:%M")
    db_query("UPDATE users SET balance = balance - ? WHERE user_id = ?", (pret, uid))
    db_query("DELETE FROM keys WHERE id = ?", (key[0],))
    db_query("INSERT INTO orders (user_id, product, key_val, date) VALUES (?, ?, ?, ?)", (uid, "Drip 1 Zi", key[1], now))
    
    await call.message.answer(f"✅ **ACHIZIȚIE REUȘITĂ!**\n\n🔑 CHEIE: `{key[1]}`\n\nO poți găsi oricând în secțiunea **PROFIL**.")
    text, markup = main_menu_keyboard(uid)
    await call.message.edit_text(text, reply_markup=markup, parse_mode="Markdown")

# --- NAVIGARE CALLBACKS ---
@dp.callback_query(F.data == "home")
async def back_home(call: types.CallbackQuery):
    text, markup = main_menu_keyboard(call.from_user.id)
    await call.message.edit_text(text, reply_markup=markup, parse_mode="Markdown")

@dp.callback_query(F.data == "shop")
async def shop_menu(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🍎 iOS", callback_data="cat_ios"), types.InlineKeyboardButton(text="🤖 Android", callback_data="cat_and")).row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home"))
    await call.message.edit_text("🌀 **SHOP BLESSED:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "cat_and")
async def and_menu(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="Drip 1 Zi - 20 LEI", callback_data="buy_d1")).row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="shop"))
    await call.message.edit_text("🤖 **ANDROID DRIP:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "add_info")
async def add_info(call: types.CallbackQuery):
    await call.message.edit_text(f"💳 **REÎNCĂRCARE**\nContact: @zenoficiall\nID-ul tău: `{call.from_user.id}`", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home")).as_markup())

async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
