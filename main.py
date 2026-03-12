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
cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0)')
conn.commit()

def get_bal(uid):
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (uid,))
    res = cursor.fetchone()
    if res: return res[0]
    cursor.execute("INSERT INTO users (user_id, balance) VALUES (?, ?)", (uid, 0.0))
    conn.commit()
    return 0.0

# --- HANDLERE ---
@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    bal = get_bal(m.from_user.id)
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛒 Shop Now", callback_data="shop"))
    builder.row(types.InlineKeyboardButton(text="💳 Cum adaug bani?", callback_data="add_info"))
    builder.row(types.InlineKeyboardButton(text="📞 Support", url="https://t.me/zenoficiall"))
    
    await m.answer(
        f"🏪 **BLESSED PANELS**\n\n🦁 Balanță: `{bal} LEI`\n🆔 ID-ul tău: `{m.from_user.id}`", 
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "add_info")
async def add_info(call: types.CallbackQuery):
    text = (
        "💳 **CUM ADAUGI BANI?**\n\n"
        "1. Trimite suma dorită pe Revolut/PayPal.\n"
        "2. Trimite screenshot cu plata la @zenoficiall\n"
        "3. Trimite-i și **ID-ul tău**: `" + str(call.from_user.id) + "`\n\n"
        "Banii vor fi adăugați instant după verificare!"
    )
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⬅️ Înapoi", callback_data="home"))
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "shop")
async def shop_menu(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🍎 iOS (Fluorite)", callback_data="ios"))
    builder.row(types.InlineKeyboardButton(text="🤖 Android (Drip)", callback_data="and"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Înapoi", callback_data="home"))
    await call.message.edit_text("🌀 **ALEGE PLATFORMA:**", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "home")
async def back_home(call: types.CallbackQuery):
    # Reapelăm start pentru a curăța meniul
    bal = get_bal(call.from_user.id)
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛒 Shop Now", callback_data="shop"))
    builder.row(types.InlineKeyboardButton(text="💳 Cum adaug bani?", callback_data="add_info"))
    builder.row(types.InlineKeyboardButton(text="📞 Support", url="https://t.me/zenoficiall"))
    
    await call.message.edit_text(
        f"🏪 **BLESSED PANELS**\n\n🦁 Balanță: `{bal} LEI`\n🆔 ID-ul tău: `{call.from_user.id}`", 
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

# --- COMANDA ADMIN ---
@dp.message(Command("add"))
async def add_money(m: types.Message):
    if m.from_user.id == ADMIN_ID:
        try:
            parts = m.text.split()
            target_id = int(parts[1])
            suma = float(parts[2])
            
            cursor.execute("SELECT balance FROM users WHERE user_id = ?", (target_id,))
            res = cursor.fetchone()
            new_bal = (res[0] if res else 0) + suma
            
            cursor.execute("INSERT OR REPLACE INTO users (user_id, balance) VALUES (?, ?)", (target_id, new_bal))
            conn.commit()
            
            await m.answer(f"✅ Succes!\nUtilizator: `{target_id}`\nBalanță nouă: `{new_bal} LEI`", parse_mode="Markdown")
            try:
                await bot.send_message(target_id, f"💰 Ți-au fost adăugați `{suma} LEI` în cont!")
            except:
                pass
        except:
            await m.answer("Sintaxă: `/add ID SUMA`", parse_mode="Markdown")

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
