from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = 'TOKEN_UL_TAU_DE_LA_BOTFATHER'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    # Textul cu design-ul din imagine
    text = (
        "🏪 **WELCOME TO SHOP**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "👋 Hello, **zen**!\n\n"
        "💳 **YOUR ACCOUNT** ━━\n"
        "┣ 💰 **Balance:** $1.00\n"
        "┣ 🛍️ **Purchases:** 5\n"
        "┗ 💸 **Total Spent:** $38.00\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📝 *Select an option below:*"
    )

    # Construirea butoanelor (Inline Keyboard)
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    btn_shop = InlineKeyboardButton("🛒 Shop Now", callback_data="shop")
    btn_orders = InlineKeyboardButton("📦 My Orders", callback_data="orders")
    btn_stats = InlineKeyboardButton("📊 My Stats", callback_data="stats")
    btn_balance = InlineKeyboardButton("💰 My Balance", callback_data="balance")
    btn_trans = InlineKeyboardButton("💳 Transactions", callback_data="trans")
    btn_files = InlineKeyboardButton("📁 Latest Files (1)", callback_data="files")
    btn_support = InlineKeyboardButton("📞 Support", callback_data="support")

    # Adăugarea butoanelor în layout
    keyboard.add(btn_shop) # Primul e singur pe rând
    keyboard.row(btn_orders, btn_stats) # Două pe rând
    keyboard.row(btn_balance, btn_trans) # Două pe rând
    keyboard.add(btn_files) # Singur
    keyboard.add(btn_support) # Singur

    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
