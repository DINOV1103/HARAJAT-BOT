"""
HARAJAT bot - asosiy fayl.
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
from aiogram.types import Message, CallbackQuery

from database import init_db, add_transaction, get_transactions_by_date, get_transactions_by_range
from keyboards import (
    main_menu_keyboard,
    cancel_keyboard,
    calendar_keyboard,
    BTN_EXPENSE,
    BTN_INCOME,
    BTN_TODAY,
    BTN_WEEK,
    BTN_MONTH,
    BTN_CALENDAR,
    BTN_MAIN_MENU,
)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
router = Router()


class Form(StatesGroup):
    waiting_expense = State()
    waiting_income = State()


# ---------- Yordamchi funksiyalar ----------

def format_amount(amount: float) -> str:
    return f"{int(amount):,}".replace(",", " ") + " so'm"


def format_date_human(date_str: str) -> str:
    y, m, d = date_str.split("-")
    return f"{d}.{m}.{y}"


def parse_amount_and_description(text: str):
    """
    '50000 taksi' -> (50000.0, 'taksi')
    '50 000 taksiga' -> (50000.0, 'taksiga')
    Summa har doim xabar boshida bo'lishi kerak.
    """
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


# ---------- Handlerlar ----------
# DIQQAT: tugma handlerlari (aniq matn bilan) Form holatidagi "ixtiyoriy matn"
# handlerlaridan OLDIN ro'yxatdan o'tishi kerak. Aks holda, masalan "Harajat
# qo'shish" rejimida turib "Bugungi harajat" tugmasini bossangiz, bot uni
# summa deb tushunib xato beradi.

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Salom! Men sizning shaxsiy <b>HARAJAT</b> botingizman 💰\n\n"
        "Quyidagi tugmalar orqali harajat/daromad qo'shing va statistikani kuzating.",
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


@router.message(F.text == BTN_MAIN_MENU)
async def back_to_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Asosiy menyu", reply_markup=main_menu_keyboard())


@router.message(F.text == BTN_TODAY)
async def today_summary(message: Message):
    today = date.today().isoformat()
    rows = get_transactions_by_date(message.from_user.id, today, type_="expense")
    text = format_simple_summary(rows, f"📊 Bugungi harajatlar ({format_date_human(today)})")
    await message.answer(text)


@router.message(F.text == BTN_WEEK)
async def week_summary(message: Message):
    today = date.today()
    start = today - timedelta(days=today.weekday())  # joriy hafta dushanbasi
    rows = get_transactions_by_range(message.from_user.id, start.isoformat(), today.isoformat(), type_="expense")
    text = format_period_summary(rows, "📆 Haftalik harajatlar")
    await message.answer(text)


@router.message(F.text == BTN_MONTH)
async def month_summary(message: Message):
    today = date.today()
    start = today.replace(day=1)
    rows = get_transactions_by_range(message.from_user.id, start.isoformat(), today.isoformat(), type_="expense")
    text = format_period_summary(rows, "🗓 Oylik harajatlar")
    await message.answer(text)


@router.message(F.text == BTN_CALENDAR)
async def show_calendar(message: Message):
    today = date.today()
    await message.answer("📅 Kunni tanlang:", reply_markup=calendar_keyboard(today.year, today.month))


# ---------- Summa kiritish (har qanday matn, faqat tegishli holatda) ----------

@router.message(Form.waiting_expense)
async def save_expense(message: Message, state: FSMContext):
    amount, description = parse_amount_and_description(message.text or "")
    if amount is None:
        await message.answer(
            "⚠️ Iltimos, summani raqam bilan boshlab yozing.\nMasalan: <i>50000 taksi</i>"
        )
        return
    today = date.today().isoformat()
    add_transaction(message.from_user.id, "expense", amount, description, today)
    await state.clear()
    await message.answer(
        f"✅ Harajat qo'shildi:\n{format_amount(amount)} — {description}",
        reply_markup=main_menu_keyboard(),
    )


@router.message(Form.waiting_income)
async def save_income(message: Message, state: FSMContext):
    amount, description = parse_amount_and_description(message.text or "")
    if amount is None:
        await message.answer(
            "⚠️ Iltimos, summani raqam bilan boshlab yozing.\nMasalan: <i>500000 oylik</i>"
        )
        return
    today = date.today().isoformat()
    add_transaction(message.from_user.id, "income", amount, description, today)
    await state.clear()
    await message.answer(
        f"✅ Daromad qo'shildi:\n{format_amount(amount)} — {description}",
        reply_markup=main_menu_keyboard(),
    )


# ---------- Kalendar callbacklari ----------

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


# ---------- Ishga tushirish ----------

async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN topilmadi! .env faylida BOT_TOKEN=... deb yozing (README.md ga qarang).")
    init_db()
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
