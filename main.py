import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# TOKEN-UL TĂU
TOKEN = '8547474775:AAGmcaWK706de3V3YxC8LdTr_lHLZn1Pihk'

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("🚀 Botul este ONLINE pe Render!\n\nShop-ul se încarcă...")

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Pornire bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
