import asyncio
import logging
import sqlite3
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

# --- STATES ---
class ClientApply(StatesGroup):
    q1 = State()
    q2 = State()

class ResellerApply(StatesGroup):
    q1 = State()

# --- DATABASE ---
conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0, 
                   is_reseller INTEGER DEFAULT 0, has_weekend_pass INTEGER DEFAULT 0, 
                   is_approved INTEGER DEFAULT 0)''')
cursor.execute('CREATE TABLE IF NOT EXISTS keys (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, key_val TEXT)')
conn.commit()

# Stoc inițial (Drip 1 Zi)
cursor.execute("SELECT * FROM keys WHERE key_val = '7048507851'")
if not cursor.fetchone():
    cursor.execute("INSERT INTO keys (type, key_val) VALUES ('d1', '7048507851')")
    conn.commit()

PRICES = {"f1": 25, "f7": 60, "d1": 20, "d7": 50, "wknd": 15}

def get_user_data(uid):
    cursor.execute("SELECT balance, is_reseller, has_weekend_pass, is_approved FROM users WHERE user_id = ?", (uid,))
    res = cursor.fetchone()
    if res: return res
    cursor.execute("INSERT INTO users (user_id, balance, is_reseller, has_weekend_pass, is_approved) VALUES (?, 0.0, 0, 0, 0)", (uid,))
    conn.commit()
    return (0.0, 0, 0, 0)

# --- MENIURI ---
def main_menu_keyboard(uid):
    bal, is_reseller, has_pass, is_approved = get_user_data(uid)
    if uid == ADMIN_ID: status = "👑 OWNER"
    elif is_reseller: status = "⭐ Reseller"
    else: status = "👤 Client"
    
    builder = InlineKeyboardBuilder()
    if not is_approved and uid != ADMIN_ID:
        builder.row(types.InlineKeyboardButton(text="📝 Aplică pentru Acces", callback_data="apply_client"))
        text = "🔒 **ACCES RESTRICȚIONAT**\n\nTrebuie să aplici pentru a vedea magazinul."
    else:
        builder.row(types.InlineKeyboardButton(text="🛒 SHOP PRODUSE", callback_data="shop"))
        builder.row(types.InlineKeyboardButton(text="🔥 OFERTE SPECIALE", callback_data="specials"))
        builder.row(types.InlineKeyboardButton(text="💼 RESELLER PANEL", callback_data="reseller"))
        builder.row(types.InlineKeyboardButton(text="💳 ADAUGĂ BANI", callback_data="add_info"))
        builder.row(types.InlineKeyboardButton(text="📞 SUPPORT", url="https://t.me/zenoficiall"))
        pass_txt = "\n🎫 Weekend Pass: ✅ ACTIV" if has_pass else ""
        text = f"🏪 **BLESSED PANELS**\n\n🦁 Balanță: `{bal} LEI`\n🏆 Status: `{status}`{pass_txt}\n🆔 ID: `{uid}`"
    return text, builder.as_markup()

# --- HANDLERE ---
@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    text, markup = main_menu_keyboard(m.from_user.id)
    await m.answer(text, reply_markup=markup, parse_mode="Markdown")

# --- ADMIN: ADAUGA BANI (FIXED) ---
@dp.message(Command("add"))
async def add_money(m: types.Message):
    if m.from_user.id == ADMIN_ID:
        try:
            parts = m.text.split()
            if len(parts) < 3:
                return await m.answer("Sintaxă corectă: `/add ID SUMA` (ex: `/add 7481370573 50`)")
            
            target_id = int(parts[1])
            suma = float(parts[2])
            
            # Verificăm dacă userul există, dacă nu îl creăm și îl aprobăm
            get_user_data(target_id)
            cursor.execute("UPDATE users SET balance = balance + ?, is_approved = 1 WHERE user_id = ?", (suma, target_id))
            conn.commit()
            
            await m.answer(f"✅ Succes!\n💰 Suma: `{suma} LEI`\n👤 User ID: `{target_id}`\n🔓 Status: Aprobat automat")
            try:
                await bot.send_message(target_id, f"💳 **Balanță actualizată!**\nAi primit `{suma} LEI` în cont.\nAcum poți folosi magazinul!")
            except: pass
        except Exception as e:
            await m.answer(f"❌ Eroare: {str(e)}")

@dp.message(Command("approve"))
async def approve_user(m: types.Message):
    if m.from_user.id == ADMIN_ID:
        try:
            tid = int(m.text.split()[1])
            cursor.execute("UPDATE users SET is_approved = 1 WHERE user_id = ?", (tid,))
            conn.commit()
            await m.answer(f"✅ Utilizatorul `{tid}` a fost aprobat!")
            await bot.send_message(tid, "🎉 **Acces aprobat!** Acum poți vedea produsele.")
        except: await m.answer("Sintaxă: `/approve ID`")

# --- INTERVIU CLIENT ---
@dp.callback_query(F.data == "apply_client")
async def start_client_apply(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(ClientApply.q1)
    await call.message.answer("❓ **Pasul 1:** De unde ai aflat de noi?")
    await call.answer()

@dp.message(ClientApply.q1)
async def client_q1(m: types.Message, state: FSMContext):
    await state.update_data(q1=m.text)
    await state.set_state(ClientApply.q2)
    await m.answer("❓ **Pasul 2:** Ce platformă folosești (iOS/Android)?")

@dp.message(ClientApply.q2)
async def client_q2(m: types.Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    report = f"👤 **CERERE NOUĂ**\n🆔 ID: `{m.from_user.id}`\n\n1️⃣ Sursă: {data['q1']}\n2️⃣ Device: {m.text}\n\n👉 `/approve {m.from_user.id}`"
    await bot.send_message(ADMIN_ID, report, parse_mode="Markdown")
    await m.answer("✅ Cererea a fost trimisă spre aprobare!")

# --- NAVIGARE SHOP ---
@dp.callback_query(F.data == "home")
async def back_home(call: types.CallbackQuery):
    text, markup = main_menu_keyboard(call.from_user.id)
    await call.message.edit_text(text, reply_markup=markup, parse_mode="Markdown")

@dp.callback_query(F.data == "shop")
async def shop_menu(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🍎 iOS", callback_data="cat_ios"), types.InlineKeyboardButton(text="🤖 Android", callback_data="cat_and"))
    builder.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home"))
    await call.message.edit_text("🌀 **SHOP BLESSED:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "cat_and")
async def and_menu(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="Drip 1 Zi - 20 LEI", callback_data="buy_d1")).row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="shop"))
    await call.message.edit_text("🤖 **ANDROID DRIP:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "buy_d1")
async def buy_drip_1d(call: types.CallbackQuery):
    bal, _, has_pass, _ = get_user_data(call.from_user.id)
    pret = 20 - (3 if has_pass else 0)
    
    if bal < pret: return await call.answer(f"❌ Ai nevoie de {pret} LEI!", show_alert=True)
    
    cursor.execute("SELECT id, key_val FROM keys WHERE type = 'd1' LIMIT 1")
    res = cursor.fetchone()
    if not res: return await call.answer("❌ STOC EPUIZAT!", show_alert=True)
    
    cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (pret, call.from_user.id))
    cursor.execute("DELETE FROM keys WHERE id = ?", (res[0],))
    conn.commit()
    await call.message.answer(f"✅ PLATĂ REUȘITĂ!\n🔑 CHEIE: `{res[1]}`")
    text, markup = main_menu_keyboard(call.from_user.id)
    await call.message.edit_text(text, reply_markup=markup, parse_mode="Markdown")

@dp.callback_query(F.data == "add_info")
async def add_info(call: types.CallbackQuery):
    await call.message.edit_text(f"💳 **REÎNCĂRCARE**\nContact: @zenoficiall\nID-ul tău: `{call.from_user.id}`", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home")).as_markup())

async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
