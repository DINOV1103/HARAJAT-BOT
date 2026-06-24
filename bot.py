"""
Moliya Menejeri - Asosiy ishga tushirish fayli.
Ishga tushirish: python bot.py
"""

import asyncio
import logging
import os
import re
from datetime import date, timedelta

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database import (
    init_db, add_user, get_users_count, get_all_user_ids,
    add_transaction, get_transactions_by_date, get_transactions_by_range,
    add_debt, get_active_debts, mark_debt_as_paid,
    add_note, get_notes, delete_note
)

from keyboards import (
    main_menu_keyboard, cancel_keyboard, stats_keyboard,
    debts_keyboard, notes_keyboard, admin_keyboard, debt_type_inline, calendar_keyboard,
    BTN_EXPENSE, BTN_INCOME, BTN_STATS, BTN_DEBTS, BTN_NOTES, BTN_CALENDAR, BTN_ADMIN, BTN_MAIN_MENU,
    BTN_STATS_TODAY, BTN_STATS_WEEK, BTN_STATS_MONTH, BTN_STATS_TOTAL,
    BTN_DEBTS_ADD, BTN_DEBTS_LIST, BTN_NOTES_ADD, BTN_NOTES_LIST,
    BTN_ADMIN_USERS, BTN_ADMIN_BROADCAST
)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 1691140865  # Siz taqdim etgan yagona admin ID

logging.basicConfig(level=logging.INFO)
router = Router()


class Form(StatesGroup):
    waiting_expense = State()
    waiting_income = State()
    waiting_debt_input = State()
    waiting_note_input = State()
    waiting_admin_broadcast = State()


# ---------- Yordamchi Funksiyalar ----------

def format_amount(amount: float) -> str:
    return f"{int(amount):,}".replace(",", " ") + " so'm"


def format_date_human(date_str: str) -> str:
    y, m, d = date_str.split("-")
    return f"{d}.{m}.{y}"


def parse_amount_and_description(text: str):
    text = text.strip()
    match = re.match(r"^([\d\s.,]+)\s*(.*)$", text)
    if not match:
        return None, None
    raw_number = match.group(1)
    description = match.group(2).strip() or "Izohsiz"
    clean_number = re.sub(r"[\s.,]", "", raw_number)
    if not clean_number.isdigit() or clean_number == "":
        return None, None
    amount = float(clean_number)
    return (amount, description) if amount > 0 else (None, None)


def parse_debt_text(text: str):
    text = text.strip()
    match = re.match(r"^(.+?)\s+([\d\s.,]+)$", text)
    if not match:
        return None, None
    name = match.group(1).strip()
    raw_amount = match.group(2)
    clean_amount = re.sub(r"[\s.,]", "", raw_amount)
    if not clean_amount.isdigit():
        return None, None
    return name, float(clean_amount)


def format_comprehensive_summary(rows, title: str) -> str:
    if not rows:
        return f"<b>{title}</b>\n\nBu davrda hech qanday moliyaviy amallar bajarilmadi."

    expenses = [r for r in rows if r[-1] == 'expense']
    incomes = [r for r in rows if r[-1] == 'income']
    total_exp = sum(r[0] for r in expenses)
    total_inc = sum(r[0] for r in incomes)

    lines = [f"<b>{title}</b>", ""]

    if len(rows[0]) == 4:  # Davriy guruhlash (Hafta/Oy uchun)
        grouped = {}
        for amount, description, txn_date, t_type in rows:
            grouped.setdefault(txn_date, []).append((amount, description, t_type))
        for d in sorted(grouped.keys()):
            lines.append(f"📅 <b>{format_date_human(d)}:</b>")
            for amount, description, t_type in grouped[d]:
                icon = "💸" if t_type == "expense" else "💰"
                lines.append(f"   • {icon} {format_amount(amount)} — {description}")
    else:  # Kunlik oddiy ro'yxat
        for amount, description, t_type in rows:
            icon = "💸" if t_type == "expense" else "💰"
            lines.append(f"• {icon} {format_amount(amount)} — {description}")

    lines.append("\n--------------------------------")
    lines.append(f"💰 Jami daromad: <b>{format_amount(total_inc)}</b>")
    lines.append(f"💸 Jami harajat: <b>{format_amount(total_exp)}</b>")
    lines.append(f"⚖️ Sof Balans: <b>{format_amount(total_inc - total_exp)}</b>")
    return "\n".join(lines)


# ---------- Tizim va Navigatsiya Handlerlari ----------

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    add_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    is_admin = (message.from_user.id == ADMIN_ID)
    await message.answer(
        f"Salom, <b>{message.from_user.full_name}</b>! Professional Moliyaviy Menejer botiga xush kelibsiz.\n\n"
        "Quyidagi boshqaruv menyusidan foydalanib hisob-kitoblaringizni boshqaring.",
        reply_markup=main_menu_keyboard(is_admin)
    )


@router.message(F.text == BTN_MAIN_MENU)
async def back_to_menu(message: Message, state: FSMContext):
    await state.clear()
    is_admin = (message.from_user.id == ADMIN_ID)
    await message.answer("🏠 Asosiy menyudasiz.", reply_markup=main_menu_keyboard(is_admin))


# ---------- Harajat va Daromad Bo'limi ----------

@router.message(F.text == BTN_EXPENSE)
async def ask_expense(message: Message, state: FSMContext):
    await state.set_state(Form.waiting_expense)
    await message.answer("✏️ Harajat summasi va sababini yozing.\nMasalan: <i>25000 tushlik</i>", reply_markup=cancel_keyboard())


@router.message(Form.waiting_expense)
async def save_expense(message: Message, state: FSMContext):
    if message.text == BTN_MAIN_MENU:
        await back_to_menu(message, state)
        return
    amount, description = parse_amount_and_description(message.text or "")
    if amount is None:
        await message.answer("⚠️ Xato kiritish. Summani raqam bilan boshlang.\nMasalan: <i>50000 taksi</i>")
        return
    today = date.today().isoformat()
    add_transaction(message.from_user.id, "expense", amount, description, today)
    await state.clear()
    is_admin = (message.from_user.id == ADMIN_ID)
    await message.answer(f"✅ Harajat saqlandi:\n<b>{format_amount(amount)}</b> — {description}", reply_markup=main_menu_keyboard(is_admin))


@router.message(F.text == BTN_INCOME)
async def ask_income(message: Message, state: FSMContext):
    await state.set_state(Form.waiting_income)
    await message.answer("✏️ Kelgan daromad summasi va manbasini yozing.\nMasalan: <i>600000 oylik</i>", reply_markup=cancel_keyboard())


@router.message(Form.waiting_income)
async def save_income(message: Message, state: FSMContext):
    if message.text == BTN_MAIN_MENU:
        await back_to_menu(message, state)
        return
    amount, description = parse_amount_and_description(message.text or "")
    if amount is None:
        await message.answer("⚠️ Xato kiritish. Summani raqam bilan boshlang.\nMasalan: <i>1200000 kassa</i>")
        return
    today = date.today().isoformat()
    add_transaction(message.from_user.id, "income", amount, description, today)
    await state.clear()
    is_admin = (message.from_user.id == ADMIN_ID)
    await message.answer(f"✅ Daromad saqlandi:\n<b>{format_amount(amount)}</b> — {description}", reply_markup=main_menu_keyboard(is_admin))


# ---------- Statistika Bo'limi ----------

@router.message(F.text == BTN_STATS)
async def show_stats_menu(message: Message):
    await message.answer("📊 Hisobot turini tanlang:", reply_markup=stats_keyboard())


@router.message(F.text == BTN_STATS_TODAY)
async def today_summary(message: Message):
    today = date.today().isoformat()
    rows = get_transactions_by_date(message.from_user.id, today)
    await message.answer(format_comprehensive_summary(rows, f"📋 Bugungi amallar ({format_date_human(today)})"))


@router.message(F.text == BTN_STATS_WEEK)
async def week_summary(message: Message):
    today = date.today()
    start = today - timedelta(days=today.weekday())
    rows = get_transactions_by_range(message.from_user.id, start.isoformat(), today.isoformat())
    await message.answer(format_comprehensive_summary(rows, "📆 Haftalik jami ko'rsatkichlar"))


@router.message(F.text == BTN_STATS_MONTH)
async def month_summary(message: Message):
    today = date.today()
    start = today.replace(day=1)
    rows = get_transactions_by_range(message.from_user.id, start.isoformat(), today.isoformat())
    await message.answer(format_comprehensive_summary(rows, "🗓 Joriy oylik ko'rsatkichlar"))


@router.message(F.text == BTN_STATS_TOTAL)
async def total_summary(message: Message):
    rows = get_transactions_by_range(message.from_user.id, "1970-01-01", date.today().isoformat())
    await message.answer(format_comprehensive_summary(rows, "📈 Tizimdagi umumiy moliyaviy balans"))


# ---------- Qarz Daftari Bo'limi ----------

@router.message(F.text == BTN_DEBTS)
async def show_debts_menu(message: Message):
    await message.answer("📒 Qarz daftari bo'limi:", reply_markup=debts_keyboard())


@router.message(F.text == BTN_DEBTS_ADD)
async def ask_debt(message: Message, state: FSMContext):
    await state.set_state(Form.waiting_debt_input)
    await message.answer("✏️ Kim bilan qarz munosabati bo'ldi va qancha?\nMasalan: <i>Ali 450000</i>", reply_markup=cancel_keyboard())


@router.message(Form.waiting_debt_input)
async def process_debt_input(message: Message, state: FSMContext):
    if message.text == BTN_MAIN_MENU:
        await back_to_menu(message, state)
        return
    name, amount = parse_debt_text(message.text or "")
    if not name or amount is None:
        await message.answer("⚠️ Noto'g'ri shakl. Ism va summani aniq yozing.\nMasalan: <i>Olim 300000</i>")
        return
    await state.update_data(d_name=name, d_amount=amount)
    await message.answer(f"👤 {name} — {format_amount(amount)}\n\nUshbu qarz turini tanlang:", reply_markup=debt_type_inline())


@router.callback_query(F.data.startswith("debt_type_"))
async def save_debt_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    name = data.get("d_name")
    amount = data.get("d_amount")
    if not name or not amount:
        await callback.answer("Ma'lumot topilmadi, qaytadan urinib ko'ring.", show_alert=True)
        return
    g_type = callback.data.split("_")[2]  # 'lent' yoki 'borrowed'
    add_debt(callback.from_user.id, name, amount, g_type)
    await state.clear()
    await callback.message.delete()
    is_admin = (callback.from_user.id == ADMIN_ID)
    type_str = "Qarz berildi 💸" if g_type == "lent" else "Qarz olindi 💰"
    await callback.message.answer(f"✅ Qarz saqlandi:\n👤 {name} — <b>{format_amount(amount)}</b> ({type_str})", reply_markup=main_menu_keyboard(is_admin))
    await callback.answer()


@router.callback_query(F.data == "debt_cancel")
async def cancel_debt_cb(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    is_admin = (callback.from_user.id == ADMIN_ID)
    await callback.message.answer("❌ Qarz yozish bekor qilindi.", reply_markup=main_menu_keyboard(is_admin))
    await callback.answer()


@router.message(F.text == BTN_DEBTS_LIST)
async def list_debts(message: Message):
    rows = get_active_debts(message.from_user.id)
    if not rows:
        await message.answer("📒 Hozirda faol qarzlaringiz mavjud emas.")
        return
    await message.answer("📜 <b>Sizning faol qarzlaringiz ro'yxati:</b>\n<i>(To'langan bo'lsa, 'To'landi' tugmasini bosing)</i>")
    for d_id, name, amount, d_type in rows:
        direction = "Bergan qarzim (menga qaytadi) ➡️" if d_type == "lent" else "Olgan qarzim (qaytarishim kerak) ⬅️"
        txt = f"👤 <b>{name}</b>\n💵 Summa: {format_amount(amount)}\n📋 Holat: {direction}"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ To'landi (Yopish)", callback_data=f"pay_{d_id}")]
        ])
        await message.answer(txt, reply_markup=kb)


@router.callback_query(F.data.startswith("pay_"))
async def close_debt(callback: CallbackQuery):
    debt_id = int(callback.data.split("_")[1])
    mark_debt_as_paid(debt_id, callback.from_user.id)
    await callback.message.edit_text(callback.message.text + "\n\n✅ <b>Ushbu qarz to'liq yopildi!</b>")
    await callback.answer("Qarz yopildi", show_alert=False)


# ---------- Eslatmalar Bo'limi ----------

@router.message(F.text == BTN_NOTES)
async def show_notes_menu(message: Message):
    await message.answer("📝 Eslatmalar bo'limi:", reply_markup=notes_keyboard())


@router.message(F.text == BTN_NOTES_ADD)
async def ask_note(message: Message, state: FSMContext):
    await state.set_state(Form.waiting_note_input)
    await message.answer("✏️ Eslatmalarni kiriting (Matn ko'rinishida):", reply_markup=cancel_keyboard())


@router.message(Form.waiting_note_input)
async def save_note_msg(message: Message, state: FSMContext):
    if message.text == BTN_MAIN_MENU:
        await back_to_menu(message, state)
        return
    if not message.text:
        await message.answer("⚠️ Iltimos, faqat matn yuboring.")
        return
    add_note(message.from_user.id, message.text)
    await state.clear()
    is_admin = (message.from_user.id == ADMIN_ID)
    await message.answer("✅ Eslatma muvaffaqiyatli saqlandi!", reply_markup=main_menu_keyboard(is_admin))


@router.message(F.text == BTN_NOTES_LIST)
async def list_notes(message: Message):
    rows = get_notes(message.from_user.id)
    if not rows:
        await message.answer("📝 Eslatmalaringiz ro'yxati bo'sh.")
        return
    await message.answer("📌 <b>Sizning eslatmalaringiz:</b>")
    for n_id, content in rows:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"del_note_{n_id}")]
        ])
        await message.answer(f"▫️ {content}", reply_markup=kb)


@router.callback_query(F.data.startswith("del_note_"))
async def remove_note_cb(callback: CallbackQuery):
    note_id = int(callback.data.split("_")[2])
    delete_note(note_id, callback.from_user.id)
    await callback.message.delete()
    await callback.answer("Eslatma o'chirildi")


# ---------- Kalendar Bo'limi ----------

@router.message(F.text == BTN_CALENDAR)
async def show_calendar(message: Message):
    today = date.today()
    await message.answer("📅 Tarixni ko'rish uchun kunni tanlang:", reply_markup=calendar_keyboard(today.year, today.month))


@router.callback_query(F.data == "cal_ignore")
async def cal_ignore(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data.startswith("cal_nav_"))
async def cal_navigate(callback: CallbackQuery):
    _, _, year, month = callback.data.split("_")
    await callback.message.edit_reply_markup(reply_markup=calendar_keyboard(int(year), int(month)))
    await callback.answer()


@router.callback_query(F.data.startswith("cal_day_"))
async def cal_day_selected(callback: CallbackQuery):
    _, _, year, month, day = callback.data.split("_")
    selected_date = date(int(year), int(month), int(day)).isoformat()
    rows = get_transactions_by_date(callback.from_user.id, selected_date)
    text = format_comprehensive_summary(rows, f"📅 {format_date_human(selected_date)} kunidagi hisobot")
    await callback.message.answer(text)
    await callback.answer()


# ---------- Admin Panel Bo'limi ----------

@router.message(F.text == BTN_ADMIN)
async def show_admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("🛡 Admin panel boshqaruv tizimi:", reply_markup=admin_keyboard())


@router.message(F.text == BTN_ADMIN_USERS)
async def admin_users_count(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    count = get_users_count()
    await message.answer(f"👥 Bot ichidagi jami a'zolar soni: <b>{count} ta</b>")


@router.message(F.text == BTN_ADMIN_BROADCAST)
async def admin_broadcast_ask(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.set_state(Form.waiting_admin_broadcast)
    await message.answer("📢 Barcha foydalanuvchilarga yuboriladigan xabar matnini kiriting:", reply_markup=cancel_keyboard())


@router.message(Form.waiting_admin_broadcast)
async def admin_broadcast_send(message: Message, state: FSMContext, bot: Bot):
    if message.from_user.id != ADMIN_ID:
        return
    if message.text == BTN_MAIN_MENU:
        await back_to_menu(message, state)
        return

    u_ids = get_all_user_ids()
    sent_count = 0
    await message.answer("⏳ Tarqatish boshlandi, iltimos kuting...")

    for uid in u_ids:
        try:
            await bot.send_message(chat_id=uid, text=message.text, parse_mode="HTML")
            sent_count += 1
            await asyncio.sleep(0.05)  # Telegram flood limit oldini olish uchun
        except Exception:
            pass

    await state.clear()
    await message.answer(f"📢 Tarqatish yakunlandi.\n✅ {sent_count} ta a'zoga muvaffaqiyatli yetib bordi.", reply_markup=main_menu_keyboard(True))


# ---------- Loyihani Ishga Tushirish ----------

async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN topilmadi! .env faylini to'g'ri sozlang.")
    init_db()
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    dp.include_router(router)
    logging.info("Bot muvaffaqiyatli ishga tushdi!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
    
