import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Configurare
TOKEN = '8547474775:AAGmcaWK706de3V3YxC8LdTr_lHLZn1Pihk'
ADMIN_ID = 7481370573

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Database simplu
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

@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    bal = get_bal(m.from_user.id)
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛒 Shop Now", callback_data="shop"))
    builder.row(types.InlineKeyboardButton(text="📞 Support", url="https://t.me/zenoficiall"))
    
    await m.answer(f"🏪 **BLESSED PANELS**\n\n🦁 Balanță: `{bal} LEI`", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "shop")
async def shop(call: types.CallbackQuery):
    await call.message.edit_text("🌀 Shop-ul este în mentenanță 1 minut. Verifică Telegram!")

async def main():
    print("Botul a pornit pe Render!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
