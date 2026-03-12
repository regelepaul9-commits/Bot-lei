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

# --- DATABASE ENGINE (Îmbunătățit pentru stabilitate) ---
def db_query(query, params=(), fetch=False, fetch_all=False):
    conn = sqlite3.connect('database.db', timeout=20)
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        res = None
        if fetch: res = cursor.fetchone()
        if fetch_all: res = cursor.fetchall()
        conn.commit()
        return res
    except Exception as e:
        logging.error(f"Database error: {e}")
        return None
    finally:
        conn.close()

# Inițializare tabele
db_query('''CREATE TABLE IF NOT EXISTS users 
            (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0, 
             is_reseller INTEGER DEFAULT 0, has_weekend_pass INTEGER DEFAULT 0, 
             is_approved INTEGER DEFAULT 0, joined_date TEXT)''')
db_query('CREATE TABLE IF NOT EXISTS keys (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, key_val TEXT)')
db_query('CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, product TEXT, key_val TEXT, date TEXT)')

# Prețuri
PRICES = {"f1": 25, "f7": 60, "d1": 20, "d7": 50, "wknd": 15}

def get_user_info(uid):
    user = db_query("SELECT balance, is_reseller, has_weekend_pass, is_approved, joined_date FROM users WHERE user_id = ?", (uid,), fetch=True)
    if not user:
        now = datetime.now().strftime("%d/%m/%Y")
        db_query("INSERT INTO users (user_id, joined_date, is_approved) VALUES (?, ?, ?)", (uid, now, 0))
        return (0.0, 0, 0, 0, now)
    return user

# --- MENIURI ---
def main_menu_keyboard(uid):
    info = get_user_info(uid)
    bal, is_reseller, has_pass, is_approved, _ = info
    
    # OWNER-ul are mereu acces total
    if uid == ADMIN_ID: is_approved = 1
    
    builder = InlineKeyboardBuilder()
    
    if is_approved == 0:
        builder.row(types.InlineKeyboardButton(text="📝 Aplică pentru Acces", callback_data="apply_client"))
        text = "👋 **BINE AI VENIT LA BLESSED PANELS**\n\n🔒 Accesul la magazin este restricționat pentru utilizatorii noi.\n\nTe rugăm să apeși butonul de mai jos pentru a primi acces."
    else:
        status = "👑 OWNER" if uid == ADMIN_ID else ("⭐ Reseller" if is_reseller else "👤 Client")
        builder.row(types.InlineKeyboardButton(text="🛒 SHOP", callback_data="shop"), types.InlineKeyboardButton(text="👤 PROFIL", callback_data="profile"))
        builder.row(types.InlineKeyboardButton(text="🔥 OFERTE", callback_data="specials"), types.InlineKeyboardButton(text="💼 RESELLER", callback_data="reseller"))
        builder.row(types.InlineKeyboardButton(text="💳 ADAUGĂ BANI", callback_data="add_info"))
        builder.row(types.InlineKeyboardButton(text="📞 SUPPORT", url="https://t.me/zenoficiall"))
        
        pass_txt = "\n🎫 Weekend Pass: ✅ ACTIV" if has_pass else ""
        text = f"🏪 **BLESSED PANELS**\n\n🦁 Balanță: `{bal} LEI`\n🏆 Status: `{status}`{pass_txt}\n🆔 ID: `{uid}`"
    
    return text, builder.as_markup()

# --- HANDLERE ---
@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    try:
        text, markup = main_menu_keyboard(m.from_user.id)
        await m.answer(text, reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Error in start command: {e}")

@dp.callback_query(F.data == "apply_client")
async def apply_start(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(ClientApply.q1)
    await call.message.answer("❓ **De unde ai aflat de Blessed Panels?** (Scrie răspunsul aici)")
    await call.answer()

@dp.message(ClientApply.q1)
async def apply_done(m: types.Message, state: FSMContext):
    await state.clear()
    report = f"🚨 **CERERE NOUĂ ACCES**\n👤 User: {m.from_user.mention}\n🆔 ID: `{m.from_user.id}`\nℹ️ Sursă: {m.text}\n\n👉 `/approve {m.from_user.id}`"
    await bot.send_message(ADMIN_ID, report, parse_mode="Markdown")
    await m.answer("✅ **Cererea ta a fost trimisă!** Administratorul te va verifica și îți va da acces în cel mai scurt timp.")

@dp.message(Command("approve"))
async def approve_cmd(m: types.Message):
    if m.from_user.id != ADMIN_ID: return
    try:
        tid = int(m.text.split()[1])
        db_query("UPDATE users SET is_approved = 1 WHERE user_id = ?", (tid,))
        await m.answer(f"✅ Utilizatorul `{tid}` a fost aprobat!")
        try:
            await bot.send_message(tid, "🎉 **ACCES APROBAT!**\nAcum poți folosi magazinul Blessed Panels.\nDă /start pentru meniu.")
        except: pass
    except:
        await m.answer("❌ Sintaxă: `/approve ID`")

@dp.message(Command("add"))
async def add_money(m: types.Message):
    if m.from_user.id != ADMIN_ID: return
    try:
        parts = m.text.split()
        tid, suma = int(parts[1]), float(parts[2])
        # Îl aprobăm automat dacă primește bani
        db_query("UPDATE users SET balance = balance + ?, is_approved = 1 WHERE user_id = ?", (suma, tid))
        await m.answer(f"✅ Adăugat {suma} LEI lui {tid}.")
        try: await bot.send_message(tid, f"💳 Ai primit {suma} LEI!")
        except: pass
    except:
        await m.answer("❌ Sintaxă: `/add ID SUMA`")

# --- CALLBACKS PENTRU NAVIGARE ---
@dp.callback_query(F.data == "home")
async def back_home(call: types.CallbackQuery):
    text, markup = main_menu_keyboard(call.from_user.id)
    await call.message.edit_text(text, reply_markup=markup, parse_mode="Markdown")

@dp.callback_query(F.data == "shop")
async def shop_menu(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🍎 iOS", callback_data="cat_ios"), types.InlineKeyboardButton(text="🤖 Android", callback_data="cat_and"))
    builder.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home"))
    await call.message.edit_text("🌀 **MAGAZIN BLESSED:**", reply_markup=builder.as_markup())

async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
