"""
HARAJAT bot - to'liq versiya (Qarz daftari bilan)
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
from aiogram.types import Message, CallbackQuery

from database import init_db, add_transaction, add_debt, get_today_reminders
from keyboards import (
    main_menu_keyboard, debt_type_keyboard, cancel_keyboard,
    calendar_keyboard, BTN_EXPENSE, BTN_INCOME, BTN_TODAY,
    BTN_WEEK, BTN_MONTH, BTN_CALENDAR, BTN_DEBTS, BTN_MAIN_MENU
)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
router = Router()


class Form(StatesGroup):
    waiting_expense = State()
    waiting_income = State()
    waiting_person = State()
    waiting_debt_amount = State()
    waiting_due_date = State()


# ==================== YORDAMCHI FUNKSIYALAR ====================

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
    if amount <= 0:
        return None, None
    return amount, description


def format_simple_summary(rows, title):
    if not rows:
        return f"<b>{title}</b>\n\nBu kunda hech qanday yozuv yo'q."
    total = sum(r[0] for r in rows)
    lines = [f"<b>{title}</b>", ""]
    for amount, description, _type in rows:
        lines.append(f"• {format_amount(amount)} — {description}")
    lines.append("")
    lines.append(f"<b>Jami: {format_amount(total)}</b>")
    return "\n".join(lines)


def format_period_summary(rows, title):
    if not rows:
        return f"<b>{title}</b>\n\nBu davrda hech qanday yozuv yo'q."
    total = sum(r[0] for r in rows)
    grouped = {}
    for amount, description, txn_date, _type in rows:
        grouped.setdefault(txn_date, []).append((amount, description))
    lines = [f"<b>{title}</b>", ""]
    for d in sorted(grouped.keys()):
        day_total = sum(a for a, _ in grouped[d])
        lines.append(f"📅 {format_date_human(d)} — {format_amount(day_total)}")
        for amount, description in grouped[d]:
            lines.append(f"   • {format_amount(amount)} — {description}")
    lines.append("")
    lines.append(f"<b>Jami: {format_amount(total)}</b>")
    return "\n".join(lines)


def format_day_detail(rows, date_str):
    expenses = [(a, d) for a, d, t in rows if t == "expense"]
    incomes = [(a, d) for a, d, t in rows if t == "income"]
    lines = [f"<b>📅 {format_date_human(date_str)}</b>", ""]
    if expenses:
        lines.append("💸 <b>Harajatlar:</b>")
        for amount, description in expenses:
            lines.append(f"   • {format_amount(amount)} — {description}")
        lines.append(f"   Jami: {format_amount(sum(a for a, _ in expenses))}")
        lines.append("")
    if incomes:
        lines.append("💰 <b>Daromadlar:</b>")
        for amount, description in incomes:
            lines.append(f"   • {format_amount(amount)} — {description}")
        lines.append(f"   Jami: {format_amount(sum(a for a, _ in incomes))}")
        lines.append("")
    if not expenses and not incomes:
        lines.append("Bu kunda hech qanday yozuv yo'q.")
    return "\n".join(lines)


# ==================== HANDLERLAR ====================

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    
    # Bugungi qarz eslatmalari
    reminders = get_today_reminders(message.from_user.id)
    if reminders:
        text = "🔔 <b>Bugun qaytarilishi kerak bo'lgan qarzlar:</b>\n\n"
        for person, amount, desc, dtype in reminders:
            typ = "Sizga berishdi" if dtype == "taken" else "Siz berdingiz"
            text += f"• {person} — {format_amount(amount)} ({typ})\n"
        await message.answer(text)
    
    await message.answer(
        "Salom! Men sizning shaxsiy <b>HARAJAT</b> botingizman 💰\n\n"
        "Quyidagi tugmalar orqali ishlating:",
        reply_markup=main_menu_keyboard(),
    )


@router.message(F.text == BTN_EXPENSE)
async def ask_expense(message: Message, state: FSMContext):
    await state.set_state(Form.waiting_expense)
    await message.answer(
        "✏️ Qancha harajat qildingiz? Summa va sababini yozing.\n\nMasalan: <i>50000 taksi</i>",
        reply_markup=cancel_keyboard(),
    )


@router.message(F.text == BTN_INCOME)
async def ask_income(message: Message, state: FSMContext):
    await state.set_state(Form.waiting_income)
    await message.answer(
        "✏️ Qancha daromad keldi? Summa va manbasini yozing.\n\nMasalan: <i>500000 oylik</i>",
        reply_markup=cancel_keyboard(),
    )


@router.message(F.text == BTN_DEBTS)
async def debt_menu(message: Message, state: FSMContext):
    await message.answer(
        "📒 Qarz turini tanlang:",
        reply_markup=debt_type_keyboard()
    )


@router.message(F.text == "👤 Qarz oldim (menga berishdi)")
async def debt_taken(message: Message, state: FSMContext):
    await state.update_data(debt_type="taken")
    await state.set_state(Form.waiting_person)
    await message.answer("👤 Kimdan qarz oldingiz? (To'liq ism yozing)", reply_markup=cancel_keyboard())


@router.message(F.text == "👥 Qarz berdim (men berganman)")
async def debt_given(message: Message, state: FSMContext):
    await state.update_data(debt_type="given")
    await state.set_state(Form.waiting_person)
    await message.answer("👤 Kimga qarz berdingiz? (To'liq ism yozing)", reply_markup=cancel_keyboard())


@router.message(Form.waiting_person)
async def process_person(message: Message, state: FSMContext):
    await state.update_data(person=message.text.strip())
    await state.set_state(Form.waiting_debt_amount)
    await message.answer("💰 Qancha summa? (Masalan: 500000 yoki 1 200 000)", reply_markup=cancel_keyboard())


@router.message(Form.waiting_debt_amount)
async def process_debt_amount(message: Message, state: FSMContext):
    try:
        clean = re.sub(r"[\s.,]", "", message.text)
        amount = float(clean)
        if amount <= 0:
            raise ValueError
    except:
        await message.answer("⚠️ To'g'ri summa kiriting (faqat raqam).")
        return
    
    await state.update_data(amount=amount)
    await state.set_state(Form.waiting_due_date)
    await message.answer(
        "📅 Qachon qaytarilishi kerak?\n"
        "Misol: <code>2026-07-15</code> yoki <code>15.07.2026</code>",
        reply_markup=cancel_keyboard()
    )


@router.message(Form.waiting_due_date)
async def process_due_date(message: Message, state: FSMContext):
    data = await state.get_data()
    text = message.text.strip()
    
    # Sana formatini to'g'rilash
    try:
        if '.' in text:
            d, m, y = map(int, text.split('.'))
            due_date = f"{y:04d}-{m:02d}-{d:02d}"
        else:
            due_date = text
    except:
        due_date = date.today().isoformat()
    
    add_debt(
        message.from_user.id,
        data['debt_type'],
        data['person'],
        data['amount'],
        "Qarz",
        due_date
    )
    
    await state.clear()
    await message.answer(
        f"✅ Qarz muvaffaqiyatli saqlandi!\n\n"
        f"{'👤 Qarz oldim' if data['debt_type']=='taken' else '👥 Qarz berdim'}\n"
        f"Shaxs: {data['person']}\n"
        f"Summa: {format_amount(data['amount'])}\n"
        f"Qaytarish sanasi: {due_date}",
        reply_markup=main_menu_keyboard()
    )


@router.message(F.text == BTN_MAIN_MENU)
async def back_to_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Asosiy menyu", reply_markup=main_menu_keyboard())


@router.message(F.text == BTN_TODAY)
async def today_summary(message: Message):
    today = date.today().isoformat()
    rows = get_transactions_by_date(message.from_user.id, today)  # type_=None bo'lsa ikkalasini ham
    text = format_day_detail(rows, today) if rows else format_simple_summary([], f"Bugungi ({format_date_human(today)})")
    await message.answer(text)


@router.message(F.text == BTN_WEEK)
async def week_summary(message: Message):
    today = date.today()
    start = today - timedelta(days=today.weekday())
    rows = get_transactions_by_range(message.from_user.id, start.isoformat(), today.isoformat())
    text = format_period_summary(rows, "📆 Haftalik harajat va daromadlar")
    await message.answer(text)


@router.message(F.text == BTN_MONTH)
async def month_summary(message: Message):
    today = date.today()
    start = today.replace(day=1)
    rows = get_transactions_by_range(message.from_user.id, start.isoformat(), today.isoformat())
    text = format_period_summary(rows, "🗓 Oylik harajat va daromadlar")
    await message.answer(text)


@router.message(F.text == BTN_CALENDAR)
async def show_calendar(message: Message):
    today = date.today()
    await message.answer("📅 Kunni tanlang:", reply_markup=calendar_keyboard(today.year, today.month))


# Kalendar callbacklari
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
    text = format_day_detail(rows, selected_date)
    await callback.message.answer(text)
    await callback.answer()


# ==================== ISHGA TUSHIRISH ====================
async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN topilmadi! .env faylida yozing.")
    init_db()
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
