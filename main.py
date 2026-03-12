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
cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0, is_reseller INTEGER DEFAULT 0, has_weekend_pass INTEGER DEFAULT 0)')
cursor.execute('CREATE TABLE IF NOT EXISTS keys (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, key_val TEXT)')

# BĂGĂM CHEIA TA ÎN STOC PENTRU DRIP 1 ZI (d1)
cursor.execute("SELECT * FROM keys WHERE key_val = '7048507851'")
if not cursor.fetchone():
    cursor.execute("INSERT INTO keys (type, key_val) VALUES ('d1', '7048507851')")
    conn.commit()

# Prețuri
PRICES = {"f1": 25, "f7": 60, "d1": 20, "d7": 50, "wknd": 15}

def get_user_data(uid):
    cursor.execute("SELECT balance, is_reseller, has_weekend_pass FROM users WHERE user_id = ?", (uid,))
    res = cursor.fetchone()
    if res: return res
    cursor.execute("INSERT INTO users (user_id, balance, is_reseller, has_weekend_pass) VALUES (?, 0.0, 0, 0)", (uid,))
    conn.commit()
    return (0.0, 0, 0)

def main_menu_keyboard(uid):
    bal, is_reseller, has_pass = get_user_data(uid)
    status = "👑 OWNER" if uid == ADMIN_ID else ("⭐ Reseller" if is_reseller else "👤 Client")
    pass_txt = "\n🎫 Weekend Pass: ✅ ACTIV (-3 LEI)" if has_pass else ""
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛒 SHOP PRODUSE", callback_data="shop"))
    builder.row(types.InlineKeyboardButton(text="🔥 OFERTE SPECIALE", callback_data="specials"))
    builder.row(types.InlineKeyboardButton(text="💼 RESELLER PANEL", callback_data="reseller"))
    builder.row(types.InlineKeyboardButton(text="💳 ADAUGĂ BANI", callback_data="add_info"))
    builder.row(types.InlineKeyboardButton(text="📞 SUPPORT", url="https://t.me/zenoficiall"))
    
    text = f"🏪 **BLESSED PANELS**\n\n🦁 Balanță: `{bal} LEI`\n🏆 Status: `{status}`{pass_txt}\n🆔 ID: `{uid}`"
    return text, builder.as_markup()

@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    text, markup = main_menu_keyboard(m.from_user.id)
    await m.answer(text, reply_markup=markup, parse_mode="Markdown")

@dp.callback_query(F.data == "home")
async def back_home(call: types.CallbackQuery):
    text, markup = main_menu_keyboard(call.from_user.id)
    await call.message.edit_text(text, reply_markup=markup, parse_mode="Markdown")

@dp.callback_query(F.data == "shop")
async def shop_menu(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🍎 iOS (Fluorite)", callback_data="cat_ios"), types.InlineKeyboardButton(text="🤖 Android (Drip)", callback_data="cat_and"))
    builder.row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home"))
    await call.message.edit_text("🌀 **ALEGE PLATFORMA:**", reply_markup=builder.as_markup())

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

@dp.callback_query(F.data.startswith("buy_"))
async def handle_buy(call: types.CallbackQuery):
    prod = call.data.replace("buy_", "")
    bal, is_reseller, has_pass = get_user_data(call.from_user.id)
    pret = PRICES.get(prod, 999)
    if has_pass and prod != "wknd": pret -= 3

    if bal < pret: return await call.answer(f"❌ Ai nevoie de {pret} LEI!", show_alert=True)

    if prod == "wknd":
        cursor.execute("UPDATE users SET balance = balance - ?, has_weekend_pass = 1 WHERE user_id = ?", (pret, call.from_user.id))
        await call.message.answer("🎁 Weekend Pass ACTIVAT! Ai -3 LEI reducere la orice hack.")
    else:
        cursor.execute("SELECT id, key_val FROM keys WHERE type = ? LIMIT 1", (prod,))
        res = cursor.fetchone()
        if not res: return await call.answer("❌ STOC EPUIZAT!", show_alert=True)
        
        cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (pret, call.from_user.id))
        cursor.execute("DELETE FROM keys WHERE id = ?", (res[0],))
        await call.message.answer(f"✅ PLATĂ REUȘITĂ!\n\n🔑 CHEIE: `{res[1]}`")
    
    conn.commit()
    text, markup = main_menu_keyboard(call.from_user.id)
    await call.message.edit_text(text, reply_markup=markup, parse_mode="Markdown")

@dp.callback_query(F.data == "specials")
async def specials_menu(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="🎁 Weekend Pass - 15 LEI", callback_data="buy_wknd")).row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home"))
    await call.message.edit_text("🔥 **OFERTE:**\nWeekend Pass = -3 LEI reducere permanentă la orice hack!", reply_markup=builder.as_markup())

@dp.message(Command("add"))
async def add_money(m: types.Message):
    if m.from_user.id == ADMIN_ID:
        try:
            p = m.text.split()
            cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (float(p[2]), int(p[1])))
            conn.commit()
            await m.answer(f"✅ Adăugat {p[2]} LEI lui {p[1]}")
        except: pass

@dp.message(Command("addkey"))
async def add_key_cmd(m: types.Message):
    if m.from_user.id == ADMIN_ID:
        try:
            p = m.text.split()
            cursor.execute("INSERT INTO keys (type, key_val) VALUES (?, ?)", (p[1], p[2]))
            conn.commit()
            await m.answer(f"✅ Cheie {p[1]} adăugată!")
        except: pass

@dp.callback_query(F.data == "reseller")
async def res_menu(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home"))
    await call.message.edit_text("💼 **RESELLER PANEL**\n\nContactează @zenoficiall.", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "add_info")
async def add_info(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home"))
    await call.message.edit_text(f"💳 **REÎNCĂRCARE**\n\nTrimite screenshot la @zenoficiall\nID: `{call.from_user.id}`", reply_markup=builder.as_markup())

async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
