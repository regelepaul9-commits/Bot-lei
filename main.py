import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- CONFIGURARE ---
TOKEN = '8547474775:AAGQ40_r3l3OyYUL6xMaXi-bugGXozNyFkA'
ADMIN_ID = 7481370573 

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- DATABASE ---
conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0, is_reseller INTEGER DEFAULT 0)')
conn.commit()

def get_user_data(uid):
    cursor.execute("SELECT balance, is_reseller FROM users WHERE user_id = ?", (uid,))
    res = cursor.fetchone()
    if res: return res
    cursor.execute("INSERT INTO users (user_id, balance, is_reseller) VALUES (?, 0.0, 0)", (uid,))
    conn.commit()
    return (0.0, 0)

# --- MENIU PRINCIPAL ---
def main_menu_keyboard(uid):
    bal, is_reseller = get_user_data(uid)
    if uid == ADMIN_ID: status = "👑 OWNER"
    elif is_reseller: status = "⭐ Reseller"
    else: status = "👤 Client"
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛒 SHOP PRODUSE", callback_data="shop"))
    builder.row(types.InlineKeyboardButton(text="🔥 OFERTE SPECIALE", callback_data="specials"))
    builder.row(types.InlineKeyboardButton(text="💼 RESELLER PANEL", callback_data="reseller"))
    builder.row(types.InlineKeyboardButton(text="💳 ADAUGĂ BANI", callback_data="add_info"))
    builder.row(types.InlineKeyboardButton(text="📞 SUPPORT", url="https://t.me/zenoficiall"))
    
    text = f"🏪 **BLESSED PANELS**\n\n🦁 Balanță: `{bal} LEI`\n🏆 Status: `{status}`\n🆔 ID: `{uid}`"
    return text, builder.as_markup()

# --- HANDLERE ---
@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    text, markup = main_menu_keyboard(m.from_user.id)
    await m.answer(text, reply_markup=markup, parse_mode="Markdown")

@dp.callback_query(F.data == "home")
async def back_home(call: types.CallbackQuery):
    text, markup = main_menu_keyboard(call.from_user.id)
    await call.message.edit_text(text, reply_markup=markup, parse_mode="Markdown")

# --- SHOP ---
@dp.callback_query(F.data == "shop")
async def shop_menu(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🍎 iOS (Fluorite)", callback_data="cat_ios"))
    builder.row(types.InlineKeyboardButton(text="🤖 Android (Drip)", callback_data="cat_and"))
    builder.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home"))
    await call.message.edit_text("🌀 **ALEGE PLATFORMA:**", reply_markup=builder.as_markup())

# --- CATEGORII PRODUSE ---
@dp.callback_query(F.data == "cat_ios")
async def ios_products(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Fluorite 1 Zi - 25 LEI", callback_data="buy_f1"))
    builder.row(types.InlineKeyboardButton(text="Fluorite 7 Zile - 60 LEI", callback_data="buy_f7"))
    builder.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="shop"))
    await call.message.edit_text("🍎 **PRODUSE iOS (FLUORITE):**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "cat_and")
async def and_products(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Drip 1 Zi - 20 LEI", callback_data="buy_d1"))
    builder.row(types.InlineKeyboardButton(text="Drip 7 Zile - 50 LEI", callback_data="buy_d7"))
    builder.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="shop"))
    await call.message.edit_text("🤖 **PRODUSE ANDROID (DRIP):**", reply_markup=builder.as_markup())

# --- OFERTE SPECIALE ---
@dp.callback_query(F.data == "specials")
async def specials_menu(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="💎 Pack All-In (iOS+And) - 100 LEI", callback_data="buy_pack"))
    builder.row(types.InlineKeyboardButton(text="🎁 Weekend Pass - 15 LEI", callback_data="buy_wknd"))
    builder.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home"))
    await call.message.edit_text("🔥 **OFERTE SPECIALE:**", reply_markup=builder.as_markup())

# --- RESELLER ---
@dp.callback_query(F.data == "reseller")
async def reseller_menu(call: types.CallbackQuery):
    bal, is_reseller = get_user_data(call.from_user.id)
    if is_reseller or call.from_user.id == ADMIN_ID:
        text = "💼 **PANEL RESELLER**\n\nStatus: ✅ ACTIV\nContactează @zenoficiall pentru chei în format bulk."
    else:
        text = "💼 **VREI SĂ DEVII RESELLER?**\n\nBeneficii:\n✅ Reduceri 40%\n✅ Panou special\n\n💰 Taxă: `100 LEI`"
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home"))
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

# --- ADD INFO ---
@dp.callback_query(F.data == "add_info")
async def add_info(call: types.CallbackQuery):
    text = f"💳 **ADAUGARE BANI**\n\nTrimite suma dorita la @zenoficiall\nID-ul tau: `{call.from_user.id}`"
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⬅️ Înapoi", callback_data="home"))
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

# --- ADMIN COMMANDS ---
@dp.message(Command("add"))
async def add_money(m: types.Message):
    if m.from_user.id == ADMIN_ID:
        try:
            p = m.text.split()
            cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (float(p[2]), int(p[1])))
            conn.commit()
            await m.answer(f"✅ Adăugat `{p[2]} LEI`.")
        except: await m.answer("Sintaxă: `/add ID SUMA`")

@dp.message(Command("setreseller"))
async def set_reseller(m: types.Message):
    if m.from_user.id == ADMIN_ID:
        try:
            tid = int(m.text.split()[1])
            cursor.execute("UPDATE users SET is_reseller = 1 WHERE user_id = ?", (tid,))
            conn.commit()
            await m.answer(f"✅ Utilizatorul `{tid}` este acum RESELLER!")
        except: await m.answer("Sintaxă: `/setreseller ID`")

# --- START BOT ---
async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
