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
    cursor.execute("INSERT INTO users (user_id, balance, is_reseller) VALUES (?, ?, ?)", (uid, 0.0, 0))
    conn.commit()
    return (0.0, 0)

# --- FUNCTIE PENTRU MENU ---
def main_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛒 SHOP PRODUSE", callback_data="shop"))
    builder.row(types.InlineKeyboardButton(text="🔥 OFERTE SPECIALE", callback_data="specials"))
    builder.row(types.InlineKeyboardButton(text="💼 RESELLER PANEL", callback_data="reseller"))
    builder.row(types.InlineKeyboardButton(text="💳 ADAUGĂ BANI", callback_data="add_info"))
    builder.row(types.InlineKeyboardButton(text="📞 SUPPORT", url="https://t.me/zenoficiall"))
    return builder.as_markup()

# --- HANDLERE ---
@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    bal, is_reseller = get_user_data(m.from_user.id)
    
    # LOGICA DE STATUS
    if m.from_user.id == ADMIN_ID:
        status = "👑 OWNER"
    elif is_reseller:
        status = "⭐ Reseller"
    else:
        status = "👤 Client"
    
    await m.answer(
        f"🏪 **BLESSED PANELS - BINE AI VENIT!**\n\n"
        f"🆔 ID: `{m.from_user.id}`\n"
        f"🦁 Balanță: `{bal} LEI`\n"
        f"🏆 Status: `{status}`\n\n"
        f"✨ Alege o secțiune de mai jos:", 
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "home")
async def back_home(call: types.CallbackQuery):
    bal, is_reseller = get_user_data(call.from_user.id)
    if call.from_user.id == ADMIN_ID:
        status = "👑 OWNER"
    elif is_reseller:
        status = "⭐ Reseller"
    else:
        status = "👤 Client"
        
    await call.message.edit_text(
        f"🏪 **BLESSED PANELS**\n\n🦁 Balanță: `{bal} LEI`\n🏆 Status: `{status}`", 
        reply_markup=main_menu_keyboard(), 
        parse_mode="Markdown"
    )

# ... restul handlerelor (shop, specials, reseller, add_info) rămân la fel ...
@dp.callback_query(F.data == "shop")
async def shop_menu(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🍎 iOS (Fluorite)", callback_data="cat_ios"), types.InlineKeyboardButton(text="🤖 Android (Drip)", callback_data="cat_and"))
    builder.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home"))
    await call.message.edit_text("🌀 **ALEGE PLATFORMA:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "specials")
async def specials_menu(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="💎 Pack All-In-One", callback_data="bs1"), types.InlineKeyboardButton(text="🎁 Weekend Pass", callback_data="bs2"))
    builder.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home"))
    await call.message.edit_text("🔥 **OFERTE LIMITATE:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "reseller")
async def reseller_menu(call: types.CallbackQuery):
    bal, is_reseller = get_user_data(call.from_user.id)
    if is_reseller or call.from_user.id == ADMIN_ID:
        text = "💼 **PANEL RESELLER ACTIV**\n\nAi acces la prețuri reduse și stoc bulk. Contactează @zenoficiall pentru listă."
    else:
        text = "💼 **VREI SĂ DEVII RESELLER?**\n\n💰 Taxă activare: `100 LEI`"
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home"))
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "add_info")
async def add_info(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⬅️ Înapoi", callback_data="home"))
    await call.message.edit_text("💳 **METODE DE PLATĂ:**\n\nTrimite suma la @zenoficiall cu ID-ul tău.", reply_markup=builder.as_markup(), parse_mode="Markdown")

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

async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
