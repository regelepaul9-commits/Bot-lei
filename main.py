import asyncio
import logging
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- CONFIG ---
TOKEN = '8547474775:AAGQ40_r3l3OyYUL6xMaXi-bugGXozNyFkA'
OWNER_ID = 7481370573 

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- DB ENGINE ---
def db_query(query, params=(), fetch=False, fetch_all=False):
    conn = sqlite3.connect('database.db', timeout=30)
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        if fetch: return cursor.fetchone()
        if fetch_all: return cursor.fetchall()
        conn.commit()
    finally:
        conn.close()

# Asigură-te că tabelul are coloana is_admin
db_query('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0, is_admin INTEGER DEFAULT 0, has_weekend_pass INTEGER DEFAULT 0)')
db_query('CREATE TABLE IF NOT EXISTS keys (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, key_val TEXT)')

def get_u(uid):
    res = db_query("SELECT balance, is_admin, has_weekend_pass FROM users WHERE user_id = ?", (uid,), fetch=True)
    if not res:
        db_query("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (uid,))
        return 0.0, 0, 0
    return res

# --- MENIU PRINCIPAL (Verifică Admin) ---
def main_kb(uid):
    bal, is_adm, has_p = get_u(uid)
    # Forțăm recunoașterea OWNER-ului ca ADMIN suprem
    is_really_admin = (uid == OWNER_ID or is_adm == 1)
    
    stat = "👑 OWNER" if uid == OWNER_ID else ("🛠️ ADMIN" if is_adm == 1 else "👤 CLIENT")
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🛒 SHOP", callback_data="open_shop"), types.InlineKeyboardButton(text="👤 PROFIL", callback_data="prof"))
    builder.row(types.InlineKeyboardButton(text="🔥 OFERTE", callback_data="specials"), types.InlineKeyboardButton(text="💳 REÎNCĂRCARE", callback_data="reinc"))
    
    if is_really_admin:
        builder.row(types.InlineKeyboardButton(text="⚙️ ADMIN PANEL", callback_data="admin_panel_view"))
    
    builder.row(types.InlineKeyboardButton(text="📞 SUPPORT", url="https://t.me/zenoficiall"))
    
    txt = f"🏪 **BLESSED PANELS**\n\n🏆 Grad: `{stat}`\n💰 Balanță: `{bal} EUR`"
    return txt, builder.as_markup()

# --- COMANDA SET ADMIN (Reparată) ---
@dp.message(Command("setadmin"))
async def set_admin_cmd(m: types.Message):
    if m.from_user.id == OWNER_ID:
        try:
            target_id = int(m.text.split()[1])
            db_query("UPDATE users SET is_admin = 1 WHERE user_id = ?", (target_id,))
            await m.answer(f"✅ Utilizatorul `{target_id}` a primit rol de ADMIN.\nAcum poate folosi `/add` și `/addkey`.")
        except Exception as e:
            await m.answer("❌ Format greșit! Folosește: `/setadmin ID_USER`")

# --- ADMIN PANEL / STOCK (Reparat) ---
@dp.callback_query(F.data == "admin_panel_view")
async def admin_stock_view(c: types.CallbackQuery):
    _, is_adm, _ = get_u(c.from_user.id)
    if c.from_user.id == OWNER_ID or is_adm == 1:
        counts = db_query("SELECT type, COUNT(*) FROM keys GROUP BY type", fetch_all=True)
        txt = "📊 **STOC ACTUAL PRODUSE:**\n\n"
        if not counts:
            txt += "Nu există chei în baza de date. ❌"
        else:
            for row in counts:
                txt += f"🔹 `{row[0]}`: {row[1]} bucăți\n"
        
        txt += "\n💡 *Folosește /addkey [tip] [cheie] pentru stoc.*"
        b = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="⬅️ ÎNAPOI", callback_data="home"))
        await c.message.edit_text(txt, reply_markup=b.as_markup(), parse_mode="Markdown")
    else:
        await c.answer("❌ Nu ai acces aici!", show_alert=True)

# --- ALTE COMENZI ADMIN ---
@dp.message(Command("addkey"))
async def add_key_logic(m: types.Message):
    _, is_adm, _ = get_u(m.from_user.id)
    if m.from_user.id == OWNER_ID or is_adm == 1:
        try:
            p = m.text.split(maxsplit=2)
            db_query("INSERT INTO keys (type, key_val) VALUES (?, ?)", (p[1], p[2]))
            await m.answer(f"✅ Adăugat în stoc: `{p[1]}`")
        except:
            await m.answer("Format: `/addkey tip cheie`")

@dp.message(Command("add"))
async def add_bal_logic(m: types.Message):
    _, is_adm, _ = get_u(m.from_user.id)
    if m.from_user.id == OWNER_ID or is_adm == 1:
        try:
            p = m.text.split()
            db_query("UPDATE users SET balance = balance + ? WHERE user_id = ?", (float(p[2]), int(p[1])))
            await m.answer(f"✅ Balanță actualizată pentru `{p[1]}`")
        except:
            await m.answer("Format: `/add ID SUMA`")

# Restul codului (Start, Shop, etc. rămân la fel)
@dp.message(Command("start"))
async def start(m: types.Message):
    t, k = main_kb(m.from_user.id)
    await m.answer(t, reply_markup=k, parse_mode="Markdown")

@dp.callback_query(F.data == "home")
async def home_cb(c: types.CallbackQuery):
    t, k = main_kb(c.from_user.id)
    await c.message.edit_text(t, reply_markup=k, parse_mode="Markdown")

async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
