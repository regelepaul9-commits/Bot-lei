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

# --- STATES PENTRU APLICĂRI ---
class ClientApply(StatesGroup):
    q1 = State()
    q2 = State()

class ResellerApply(StatesGroup):
    q1 = State()
    q2 = State()
    q3 = State()

# --- DATABASE ---
conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0, is_reseller INTEGER DEFAULT 0, has_weekend_pass INTEGER DEFAULT 0, is_approved INTEGER DEFAULT 0)')
cursor.execute('CREATE TABLE IF NOT EXISTS keys (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, key_val TEXT)')

# Stoc inițial
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

# --- MENIU PRINCIPAL ---
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

# --- HANDLERE START ---
@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    text, markup = main_menu_keyboard(m.from_user.id)
    await m.answer(text, reply_markup=markup, parse_mode="Markdown")

# --- APLICARE CLIENT ---
@dp.callback_query(F.data == "apply_client")
async def start_client_apply(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(ClientApply.q1)
    await call.message.answer("❓ **Pasul 1:** De unde ai aflat de Blessed Panels?")
    await call.answer()

@dp.message(ClientApply.q1)
async def client_q1(m: types.Message, state: FSMContext):
    await state.update_data(q1=m.text)
    await state.set_state(ClientApply.q2)
    await m.answer("❓ **Pasul 2:** Ce platformă folosești? (iOS sau Android?)")

@dp.message(ClientApply.q2)
async def client_q2(m: types.Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    report = f"👤 **CERERE ACCES CLIENT**\n🆔 ID: `{m.from_user.id}`\n👤 User: {m.from_user.mention}\n\n1️⃣ Sursă: {data['q1']}\n2️⃣ Platformă: {m.text}\n\nComandă aprobare: `/approve {m.from_user.id}`"
    await bot.send_message(ADMIN_ID, report, parse_mode="Markdown")
    await m.answer("✅ **Cererea a fost trimisă!** Așteaptă aprobarea administratorului.")

# --- APLICARE RESELLER ---
@dp.callback_query(F.data == "reseller")
async def reseller_menu(call: types.CallbackQuery, state: FSMContext):
    bal, is_reseller, has_pass, is_approved = get_user_data(call.from_user.id)
    builder = InlineKeyboardBuilder()
    if is_reseller or call.from_user.id == ADMIN_ID:
        text = "💼 **PANEL RESELLER**\n\nStatus: ✅ ACTIV"
    else:
        text = "💼 **INTERVIU RESELLER**\n\nDevino partener oficial."
        builder.row(types.InlineKeyboardButton(text="📝 Începe Interviul", callback_data="start_res_apply"))
    builder.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home"))
    await call.message.edit_text(text, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "start_res_apply")
async def start_res_apply(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(ResellerApply.q1)
    await call.message.answer("❓ **Întrebare Reseller:** Câți clienți ai în prezent?")
    await call.answer()

@dp.message(ResellerApply.q1)
async def res_q1(m: types.Message, state: FSMContext):
    await state.update_data(q1=m.text)
    await state.clear()
    await bot.send_message(ADMIN_ID, f"💼 **CERERE RESELLER**\nID: `{m.from_user.id}`\nInfo: {m.text}")
    await m.answer("✅ Cerere reseller trimisă!")

# --- ADMIN COMMANDS ---
@dp.message(Command("approve"))
async def approve_user(m: types.Message):
    if m.from_user.id == ADMIN_ID:
        try:
            tid = int(m.text.split()[1])
            cursor.execute("UPDATE users SET is_approved = 1 WHERE user_id = ?", (tid,))
            conn.commit()
            await bot.send_message(tid, "🎉 **ACCES APROBAT!**\nAcum poți folosi magazinul. Dă /start")
            await m.answer(f"✅ Utilizatorul {tid} a fost aprobat.")
        except: await m.answer("Sintaxă: `/approve ID`")

@dp.message(Command("add"))
async def add_money(m: types.Message):
    if m.from_user.id == ADMIN_ID:
        p = m.text.split()
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (float(p[2]), int(p[1])))
        conn.commit()
        await m.answer("✅ OK")

# --- NAVIGARE ---
@dp.callback_query(F.data == "home")
async def back_home(call: types.CallbackQuery):
    text, markup = main_menu_keyboard(call.from_user.id)
    await call.message.edit_text(text, reply_markup=markup, parse_mode="Markdown")

@dp.callback_query(F.data == "shop")
async def shop_menu(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🍎 iOS", callback_data="cat_ios"), types.InlineKeyboardButton(text="🤖 Android", callback_data="cat_and"))
    builder.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home"))
    await call.message.edit_text("🌀 **SHOP:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "cat_and")
async def and_menu(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="Drip 1 Zi - 20 LEI", callback_data="buy_d1")).row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="shop"))
    await call.message.edit_text("🤖 **ANDROID:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("buy_"))
async def handle_buy(call: types.CallbackQuery):
    prod = call.data.replace("buy_", "")
    bal, _, has_pass, _ = get_user_data(call.from_user.id)
    pret = PRICES.get(prod, 999)
    if has_pass and prod != "wknd": pret -= 3
    if bal < pret: return await call.answer("❌ Bani insuficienți!", show_alert=True)
    
    cursor.execute("SELECT id, key_val FROM keys WHERE type = ? LIMIT 1", (prod,))
    res = cursor.fetchone()
    if not res: return await call.answer("❌ STOC EPUIZAT!", show_alert=True)
    
    cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (pret, call.from_user.id))
    cursor.execute("DELETE FROM keys WHERE id = ?", (res[0],))
    conn.commit()
    await call.message.answer(f"✅ CHEIE: `{res[1]}`")

@dp.callback_query(F.data == "add_info")
async def add_info(call: types.CallbackQuery):
    await call.message.edit_text(f"💳 **REÎNCĂRCARE**\nContact @zenoficiall\nID: `{call.from_user.id}`", reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home")).as_markup())

async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
