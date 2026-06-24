# bot.py
import os
import asyncio
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from datetime import datetime
import db
import keyboards
from dateutil import parser

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "1691140865"))
DB_PATH = os.getenv("DB_PATH", "harajat.db")

if not BOT_TOKEN:
    print("BOT_TOKEN muhit o'zgaruvchisi o'rnatilmagan. .env faylini tekshiring.")
    exit(1)

USER_STATE = {}  # user_id -> state dict

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await db.add_user(user.id, user.first_name, DB_PATH)
    bal = await db.get_balance(user.id, DB_PATH)
    text = (
        f"Assalomu alaykum, {user.first_name}!\n"
        f"Joriy balans: {bal:.2f} so'm\n\n"
        "Qo'llanma:\n"
        "- Pul kirimi qo'shish uchun 'Kirim' tugmasini bosing.\n"
        "- Harajat qo'shish uchun 'Chiqim' tugmasini bosing.\n"
        "- 'Kalendar' orqali sana bo'yicha ko'rish; 'Qarz daftari' orqali qarzlarni boshqarish.\n"
        "Admin uchun /admin buyrug'i mavjud."
    )
    await update.message.reply_text(text, reply_markup=keyboards.main_keyboard())

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid != ADMIN_ID:
        await update.message.reply_text("Siz admin emassiz.")
        return
    await update.message.reply_text("Admin panel:", reply_markup=keyboards.admin_inline())

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id
    text = update.message.text.strip()

    # Quick commands
    if text.lower().startswith("kirim"):
        USER_STATE[uid] = {"action": "adding_income"}
        await update.message.reply_text("Kirimni quyidagi formatda yuboring:\nmiqdor;kategoriya;izoh\nMasalan: 50000;maosh;oylik")
        return

    if text.lower().startswith("chiqim"):
        USER_STATE[uid] = {"action": "adding_expense"}
        await update.message.reply_text("Chiqimni quyidagi formatda yuboring:\nmiqdor;kategoriya;izoh\nMasalan: 12000;ovqat;non")
        return

    if text.lower().startswith("kunlik"):
        date_iso = datetime.utcnow().date().isoformat()
        rows = await db.get_daily(uid, date_iso, DB_PATH)
        if not rows:
            await update.message.reply_text("Bugun tranzaksiya topilmadi.")
            return
        msg = "Bugungi tranzaksiyalar:\n"
        for r in rows:
            msg += f"{r[5][:19]} | {r[1]} | {r[2]:.2f} | {r[3]} | {r[4]}\n"
        await update.message.reply_text(msg)
        return

    if text.lower().startswith("oylik"):
        ym = datetime.utcnow().strftime("%Y-%m")
        rows = await db.get_monthly(uid, ym, DB_PATH)
        if not rows:
            await update.message.reply_text("Bu oy tranzaksiya topilmadi.")
            return
        msg = f"{ym} oyidagi tranzaksiyalar:\n"
        for r in rows:
            msg += f"{r[5][:19]} | {r[1]} | {r[2]:.2f} | {r[3]} | {r[4]}\n"
        await update.message.reply_text(msg)
        return

    if text.lower().startswith("kalendar"):
        USER_STATE[uid] = {"action": "calendar_wait"}
        await update.message.reply_text("Sana kiriting (YYYY-MM-DD) yoki oy uchun YYYY-MM")
        return

    if text.lower().startswith("qarz"):
        USER_STATE[uid] = {"action": "debt_menu"}
        await update.message.reply_text("Qarz qo'shish uchun 'Qarz qo'shish' deb yozing yoki 'Qarzlar' deb yozing.")
        return

    # Debt submenu
    if USER_STATE.get(uid, {}).get("action") == "debt_menu":
        if text.lower().startswith("qarz qo'shish"):
            USER_STATE[uid] = {"action": "debt_adding"}
            await update.message.reply_text("Qarzni quyidagi formatda yuboring:\nism;miqdor;direction(taken/given);due_date(YYYY-MM-DD);izoh")
            return
        if text.lower().startswith("qarzlar"):
            rows = await db.list_debts(uid, DB_PATH)
            if not rows:
                await update.message.reply_text("Qarzlar ro'yxati bo'sh.")
                return
            msg = "Qarzlar:\n"
            for r in rows:
                msg += f"ID:{r[0]} | {r[1]} | {r[2]:.2f} | {r[3]} | qaytarish: {r[4]} | {r[5]}\n"
            await update.message.reply_text(msg)
            return

    # Admin broadcast quick format
    if uid == ADMIN_ID and text.lower().startswith("broadcast:"):
        msg = text.partition(":")[2].strip()
        if not msg:
            await update.message.reply_text("Xabar matnini yozing: Broadcast: xabar")
            return
        USER_STATE[uid] = {"action": "admin_broadcast_confirm", "msg": msg}
        await update.message.reply_text(f"Quyidagi xabarni barcha foydalanuvchilarga yuborilsinmi?\n\n{msg}", reply_markup=keyboards.confirm_inline("confirm_yes","confirm_no"))
        return

    # Stateful handlers
    state = USER_STATE.get(uid)
    if state:
        action = state.get("action")

        if action in ("adding_income", "adding_expense"):
            parts = [p.strip() for p in text.split(";")]
            try:
                amount = float(parts[0])
            except:
                await update.message.reply_text("Miqdor raqam bo'lishi kerak. Masalan: 50000;maosh;izoh")
                return
            category = parts[1] if len(parts) > 1 else ""
            note = parts[2] if len(parts) > 2 else ""
            ttype = "income" if action == "adding_income" else "expense"
            await db.add_transaction(uid, ttype, amount, category, note, DB_PATH)
            bal = await db.get_balance(uid, DB_PATH)
            await update.message.reply_text(f"{'Kirim' if ttype=='income' else 'Chiqim'} qo'shildi: {amount:.2f}\nJoriy balans: {bal:.2f}")
            USER_STATE.pop(uid, None)
            return

        if action == "calendar_wait":
            txt = text.strip()
            try:
                if len(txt) == 7 and "-" in txt:
                    rows = await db.get_monthly(uid, txt, DB_PATH)
                else:
                    parser.parse(txt)
                    rows = await db.get_daily(uid, txt, DB_PATH)
                if not rows:
                    await update.message.reply_text("Ko'rsatilgan davrda tranzaksiya topilmadi.")
                    USER_STATE.pop(uid, None)
                    return
                msg = "Natija:\n"
                for r in rows:
                    msg += f"{r[5][:19]} | {r[1]} | {r[2]:.2f} | {r[3]} | {r[4]}\n"
                await update.message.reply_text(msg)
            except Exception:
                await update.message.reply_text("Sana formatida xato. YYYY-MM-DD yoki YYYY-MM ko'rinishida yuboring.")
            USER_STATE.pop(uid, None)
            return

        if action == "debt_adding":
            parts = [p.strip() for p in text.split(";")]
            if len(parts) < 4:
                await update.message.reply_text("To'liq ma'lumot kiriting: ism;miqdor;direction(taken/given);due_date(YYYY-MM-DD);izoh")
                return
            person = parts[0]
            try:
                amount = float(parts[1])
            except:
                await update.message.reply_text("Miqdor raqam bo'lishi kerak.")
                return
            direction = parts[2]
            due_date = parts[3]
            note = parts[4] if len(parts) > 4 else ""
            await db.add_debt(uid, person, amount, direction, due_date, note, DB_PATH)
            await update.message.reply_text("Qarz qo'shildi.")
            USER_STATE.pop(uid, None)
            return

    await update.message.reply_text("Buyruq tushunilmadi. Asosiy menyu uchun /start ni bosing.")

async def callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    data = q.data

    if data == "admin_broadcast" and uid == ADMIN_ID:
        USER_STATE[uid] = {"action": "admin_broadcast_wait"}
        await q.message.reply_text("Broadcast xabarini yuboring boshida 'Broadcast:' bilan yoki /cancel bilan bekor qiling.")
        return

    if data == "admin_stats" and uid == ADMIN_ID:
        users, trans = await db.count_users_and_transactions(DB_PATH)
        await q.message.reply_text(f"Foydalanuvchilar: {users}\nTranzaksiyalar: {trans}")
        return

    if data == "confirm_yes":
        st = USER_STATE.get(uid)
        if st and st.get("action") == "admin_broadcast_confirm":
            msg = st.get("msg")
            users = await db.get_all_users(DB_PATH)
            sent = 0
            for u in users:
                try:
                    await context.bot.send_message(u, f"Admin xabari:\n\n{msg}")
                    sent += 1
                except:
                    continue
            await q.message.reply_text(f"Xabar yuborildi. Muvaffaqiyatli: {sent}")
            USER_STATE.pop(uid, None)
        else:
            await q.message.reply_text("Hech qanday tasdiqlanadigan xabar topilmadi.")
        return

    if data == "confirm_no":
        USER_STATE.pop(uid, None)
        await q.message.reply_text("Bekor qilindi.")
        return

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    USER_STATE.pop(uid, None)
    await update.message.reply_text("Amal bekor qilindi.")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Buyruq noma'lum. /start bilan asosiy menyuga qayting.")

async def main():
    await db.init_db(DB_PATH)
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CallbackQueryHandler(callback_query))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    print("Bot ishga tushdi...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())