"""
Harajat / Daromad qo'shish, statistika (bugungi, haftalik, oylik, kalendar)
va umumiy moliyaviy balans.
"""

from datetime import date, timedelta

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from database import add_transaction, get_transactions_by_date, get_transactions_by_range, get_user_balance
from states import Form
from utils import format_amount, format_date_human, parse_amount_and_description
from keyboards import (
    main_menu_for,
    cancel_keyboard,
    calendar_keyboard,
    ALL_MENU_BUTTONS,
    BTN_EXPENSE,
    BTN_INCOME,
    BTN_TODAY,
    BTN_WEEK,
    BTN_MONTH,
    BTN_CALENDAR,
    BTN_BALANCE,
)

router = Router()


# ---------- Formatlash ----------

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


# ---------- Tugma handlerlari ----------

@router.message(F.text == BTN_EXPENSE)
async def ask_expense(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(Form.waiting_expense)
    await message.answer(
        "✏️ Qancha harajat qildingiz? Summa va sababini yozing.\n\nMasalan: <i>50000 taksi</i>",
        reply_markup=cancel_keyboard(),
    )


@router.message(F.text == BTN_INCOME)
async def ask_income(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(Form.waiting_income)
    await message.answer(
        "✏️ Qancha daromad keldi? Summa va manbasini yozing.\n\nMasalan: <i>500000 oylik</i>",
        reply_markup=cancel_keyboard(),
    )


@router.message(F.text == BTN_TODAY)
async def today_summary(message: Message, state: FSMContext):
    await state.clear()
    today = date.today().isoformat()
    rows = get_transactions_by_date(message.from_user.id, today, type_="expense")
    await message.answer(format_simple_summary(rows, f"📊 Bugungi harajatlar ({format_date_human(today)})"))


@router.message(F.text == BTN_WEEK)
async def week_summary(message: Message, state: FSMContext):
    await state.clear()
    today = date.today()
    start = today - timedelta(days=today.weekday())
    rows = get_transactions_by_range(message.from_user.id, start.isoformat(), today.isoformat(), type_="expense")
    await message.answer(format_period_summary(rows, "📆 Haftalik harajatlar"))


@router.message(F.text == BTN_MONTH)
async def month_summary(message: Message, state: FSMContext):
    await state.clear()
    today = date.today()
    start = today.replace(day=1)
    rows = get_transactions_by_range(message.from_user.id, start.isoformat(), today.isoformat(), type_="expense")
    await message.answer(format_period_summary(rows, "🗓 Oylik harajatlar"))


@router.message(F.text == BTN_CALENDAR)
async def show_calendar(message: Message, state: FSMContext):
    await state.clear()
    today = date.today()
    await message.answer("📅 Kunni tanlang:", reply_markup=calendar_keyboard(today.year, today.month, prefix="cal"))


@router.message(F.text == BTN_BALANCE)
async def show_balance(message: Message, state: FSMContext):
    await state.clear()
    b = get_user_balance(message.from_user.id)
    net_label = "✅ Ortiqcha" if b["net"] >= 0 else "⚠️ Kamomad"
    text = (
        "📈 <b>Umumiy moliyaviy holat</b>\n\n"
        f"💰 Jami daromad: {format_amount(b['total_income'])}\n"
        f"💸 Jami harajat: {format_amount(b['total_expense'])}\n"
        f"{net_label}: {format_amount(abs(b['net']))}\n\n"
        f"📥 Sizga qaytarilishi kerak: {format_amount(b['debt_given'])}\n"
        f"📤 Siz qaytarishingiz kerak: {format_amount(b['debt_taken'])}"
    )
    await message.answer(text)


# ---------- Summa kiritish (faqat tegishli holatda, menyu tugmalaridan tashqari) ----------

@router.message(Form.waiting_expense, ~F.text.in_(ALL_MENU_BUTTONS))
async def save_expense(message: Message, state: FSMContext):
    amount, description = parse_amount_and_description(message.text)
    if amount is None:
        await message.answer("⚠️ Iltimos, summani raqam bilan boshlab yozing.\nMasalan: <i>50000 taksi</i>")
        return
    today = date.today().isoformat()
    add_transaction(message.from_user.id, "expense", amount, description, today)
    await state.clear()
    await message.answer(
        f"✅ Harajat qo'shildi:\n{format_amount(amount)} — {description}",
        reply_markup=main_menu_for(message.from_user.id),
    )


@router.message(Form.waiting_income, ~F.text.in_(ALL_MENU_BUTTONS))
async def save_income(message: Message, state: FSMContext):
    amount, description = parse_amount_and_description(message.text)
    if amount is None:
        await message.answer("⚠️ Iltimos, summani raqam bilan boshlab yozing.\nMasalan: <i>500000 oylik</i>")
        return
    today = date.today().isoformat()
    add_transaction(message.from_user.id, "income", amount, description, today)
    await state.clear()
    await message.answer(
        f"✅ Daromad qo'shildi:\n{format_amount(amount)} — {description}",
        reply_markup=main_menu_for(message.from_user.id),
    )


# ---------- Kalendar callbacklari (statistik ko'rish) ----------

@router.callback_query(F.data == "cal:ignore")
async def cal_ignore(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data.startswith("cal:nav:"))
async def cal_navigate(callback: CallbackQuery):
    _, _, year, month = callback.data.split(":")
    try:
        await callback.message.edit_reply_markup(reply_markup=calendar_keyboard(int(year), int(month), prefix="cal"))
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data.startswith("cal:day:"))
async def cal_day_selected(callback: CallbackQuery):
    _, _, year, month, day = callback.data.split(":")
    selected_date = date(int(year), int(month), int(day)).isoformat()
    rows = get_transactions_by_date(callback.from_user.id, selected_date)
    await callback.message.answer(format_day_detail(rows, selected_date))
    await callback.answer()
