"""
HARAJAT BOT - PROFESSIONAL FINAL VERSIYA
Moliyaviy menejer sifatida ishlangan
"""

import asyncio
import logging
import os
import re
from datetime import date, timedelta

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from database import (
    init_db, add_transaction, add_debt, get_transactions_by_date,
    get_transactions_by_range, get_active_debts, mark_debt_returned,
    get_today_reminders, save_user
)
from keyboards import (
    main_menu_keyboard, debt_menu_keyboard, cancel_keyboard,
    calendar_keyboard, BTN_EXPENSE, BTN_INCOME, BTN_TODAY,
    BTN_WEEK, BTN_MONTH, BTN_CALENDAR, BTN_DEBTS, BTN_MAIN_MENU
)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
router = Router()

ADMIN_ID = 1691140865

class Form(StatesGroup):
    waiting_expense = State()
    waiting_income = State()
    waiting_debt_person = State()
    waiting_debt_amount = State()
    waiting_debt_description = State()
    waiting_debt_due_date = State()


# ===================== YORDAMCHI FUNKSIYALAR =====================

def format_amount(amount: float) -> str:
    return f"{int(amount):,}".replace(",", " ") + " so'm"


def format_date_human(date_str: str) -> str:
    y, m, d = date_str.split("-")
    return f"{d}.{m}.{y}"


def parse_amount(text: str):
    text = text.strip()
    match = re.match(r"^([\d\s.,]+)\s*(.*)$", text)
    if not match:
        return None, None
    raw = match.group(1)
    desc = match.group(2).strip() or "Izohsiz"
    clean = re.sub(r"[\s.,]", "", raw)
    if not clean.isdigit():
        return None, None
    amount = float(clean)
    return amount if amount > 0 else None, desc


# ===================== ASOSIY HANDLERLAR =====================

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await save_user(message.from_user.id, message.from_user.username, message.from_user.first_name)

    # Bugungi eslatmalar
    reminders = get_today_reminders(message.from_user.id)
    if reminders:
        text = "🔔 <b>Bugun qaytariladigan qarzlar:</b>\n\n"
        for p, a, d, t in reminders:
            typ = "Sizga berishdi" if t == "taken" else "Siz berdingiz"
            text += f"• {p} — {format_amount(a)} ({typ})\n"
        await message.answer(text)

    await message.answer(
        "👋 <b>Xush kelibsiz! Sizning moliyaviy yordamchingiz</b>\n\n"
        "💰 Harajat va daromadlarni kuzatib boring\n"
        "📒 Qarzlaringizni boshqaring\n"
        "📊 Hisobotlarni oling\n\n"
        "Quyidagi tugmalardan foydalaning 👇",
        reply_markup=main_menu_keyboard()
    )


@router.message(F.text == BTN_EXPENSE)
async def ask_expense(message: Message, state: FSMContext):
    await state.set_state(Form.waiting_expense)
    await message.answer(
        "✏️ <b>Harajat qo'shish</b>\n\n"
        "Summa va izohni yozing:\n"
        "<i>50000 taksi</i> yoki <i>150000 oziq-ovqat</i>",
        reply_markup=cancel_keyboard()
    )


@router.message(F.text == BTN_INCOME)
async def ask_income(message: Message, state: FSMContext):
    await state.set_state(Form.waiting_income)
    await message.answer(
        "✏️ <b>Daromad qo'shish</b>\n\n"
        "Summa va manbani yozing:\n"
        "<i>500000 oylik</i>",
        reply_markup=cancel_keyboard()
    )


@router.message(F.text == BTN_DEBTS)
async def debt_menu_handler(message: Message):
    await message.answer("📒 <b>Qarz daftari</b>", reply_markup=debt_menu_keyboard())


# ==================== QARZ BERISH / OLISH ====================

@router.message(F.text.in_(["➕ Qarz berdim", "➖ Qarz oldim"]))
async def start_debt(message: Message, state: FSMContext):
    debt_type = "given" if "berdim" in message.text else "taken"
    await state.update_data(debt_type=debt_type)
    await state.set_state(Form.waiting_debt_person)
    text = "👤 Kimga qarz berdingiz?" if debt_type == "given" else "👤 Kimdan qarz oldingiz?"
    await message.answer(text, reply_markup=cancel_keyboard())


@router.message(Form.waiting_debt_person)
async def debt_person(message: Message, state: FSMContext):
    await state.update_data(person=message.text.strip())
    await state.set_state(Form.waiting_debt_amount)
    await message.answer("💰 Qancha summa?", reply_markup=cancel_keyboard())


@router.message(Form.waiting_debt_amount)
async def debt_amount(message: Message, state: FSMContext):
    amount, _ = parse_amount(message.text)
    if not amount:
        return await message.answer("⚠️ To'g'ri summa kiriting.")
    
    await state.update_data(amount=amount)
    await state.set_state(Form.waiting_debt_description)
    await message.answer("📝 Izoh (ixtiyoriy):", reply_markup=cancel_keyboard())


@router.message(Form.waiting_debt_description)
async def debt_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip() or "Izohsiz")
    today = date.today()
    await message.answer(
        "📅 Qachon qaytarilishi kerak?",
        reply_markup=calendar_keyboard(today.year, today.month, callback_prefix="debt_due_")
    )
    await state.set_state(Form.waiting_debt_due_date)


@router.callback_query(F.data.startswith("debt_due_nav_"))
async def debt_calendar_nav(callback: CallbackQuery):
    _, _, year, month = callback.data.split("_")
    await callback.message.edit_reply_markup(
        reply_markup=calendar_keyboard(int(year), int(month), "debt_due_")
    )
    await callback.answer()


@router.callback_query(F.data.startswith("debt_due_day_"))
async def debt_date_selected(callback: CallbackQuery, state: FSMContext):
    _, _, year, month, day = callback.data.split("_")
    due_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    
    data = await state.get_data()
    add_debt(
        callback.from_user.id,
        data['debt_type'],
        data['person'],
        data['amount'],
        data['description'],
        due_date
    )
    
    await state.clear()
    await callback.message.answer(
        f"✅ <b>Qarz saqlandi!</b>\n\n"
        f"Shaxs: {data['person']}\n"
        f"Summa: {format_amount(data['amount'])}\n"
        f"Sana: {format_date_human(due_date)}",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()


# ==================== QARZLAR RO'YXATI ====================

@router.message(F.text == "📋 Qarzlar ro'yxati")
async def show_debts(message: Message):
    debts = get_active_debts(message.from_user.id)
    if not debts:
        return await message.answer("Hozircha faol qarz yo'q.")

    text = "📋 <b>Faol qarzlar:</b>\n\n"
    for d_id, dtype, person, amount, desc, due in debts:
        status = "🟢" if dtype == "given" else "🔵"
        text += f"{status} {person} — {format_amount(amount)}\n"
        text += f"   📅 {format_date_human(due)}\n\n"
    
    await message.answer(text)


# ==================== QOLGAN HANDLERLAR ====================

@router.message(F.text == BTN_MAIN_MENU)
async def back_to_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Asosiy menyu", reply_markup=main_menu_keyboard())


@router.message(F.text == BTN_TODAY)
async def today_summary(message: Message):
    today = date.today().isoformat()
    rows = get_transactions_by_date(message.from_user.id, today)
    # format_day_detail funksiyasini kerak bo'lsa qo'shing


@router.message(F.text == BTN_WEEK)
async def week_summary(message: Message):
    today = date.today()
    start = today - timedelta(days=today.weekday())
    rows = get_transactions_by_range(message.from_user.id, start.isoformat(), today.isoformat())
    # format_period_summary kerak


@router.message(F.text == BTN_MONTH)
async def month_summary(message: Message):
    today = date.today()
    start = today.replace(day=1)
    rows = get_transactions_by_range(message.from_user.id, start.isoformat(), today.isoformat())
    # format_period_summary


@router.message(F.text == BTN_CALENDAR)
async def show_calendar(message: Message):
    today = date.today()
    await message.answer("📅 Kunni tanlang:", reply_markup=calendar_keyboard(today.year, today.month))


# Admin Broadcast
@router.message(Command("broadcast"), F.from_user.id == ADMIN_ID)
async def broadcast(message: Message):
    if not message.reply_to_message:
        return await message.answer("Xabarni reply qilib /broadcast yozing!")
    # Broadcast logikasi (keyinroq to'liq qilamiz)


# ==================== ISHGA TUSHIRISH ====================
async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN topilmadi!")
    init_db()
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())



