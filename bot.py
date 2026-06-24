"""
HARAJAT bot - Mukammallashtirilgan asosiy yadro fayli.
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

from database import (
    init_db, 
    add_transaction, 
    get_transactions_by_date, 
    get_transactions_by_range,
    add_debt,
    get_active_debts,
    settle_debt,
    get_admin_stats
)
from keyboards import (
    main_menu_keyboard,
    cancel_keyboard,
    calendar_keyboard,
    debt_menu_keyboard,
    debt_type_inline,
    debt_calendar_keyboard,
    settle_debt_keyboard,
    BTN_EXPENSE,
    BTN_INCOME,
    BTN_TODAY,
    BTN_WEEK,
    BTN_MONTH,
    BTN_CALENDAR,
    BTN_MAIN_MENU,
    BTN_DEBT_HUB,
    BTN_ADD_DEBT,
    BTN_MY_DEBTS,
    BTN_ADMIN,
)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 1691140865

logging.basicConfig(level=logging.INFO)
router = Router()


class Form(StatesGroup):
    waiting_expense = State()
    waiting_income = State()

# Qarz tizimi uchun FSM holatlari
class DebtForm(StatesGroup):
    waiting_type = State()
    waiting_amount_person = State()
    waiting_date = State()


# ---------- Yordamchi funksiyalar ----------

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


# ---------- Tizim va Navigatsiya Handlerlari ----------

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Salom! Men sizning shaxsiy <b>MOLIYAVIY AQLLI HISOBOT</b> yordamchingizman 👑💰\n\n"
        "Quyidagi tugmalar orqali dynamic hisob-kitoblar, statistika va qarzlarni boshqaring.",
        reply_markup=main_menu_keyboard(message.from_user.id),
    )


@router.message(F.text == BTN_MAIN_MENU)
async def back_to_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Asosiy menyu", reply_markup=main_menu_keyboard(message.from_user.id))


# ---------- Harajat / Daromad Modullari ----------

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


@router.message(Form.waiting_expense)
async def save_expense(message: Message, state: FSMContext):
    amount, description = parse_amount_and_description(message.text or "")
    if amount is None:
        await message.answer("⚠️ Iltimos, summani raqam bilan boshlab yozing.\nMasalan: <i>50000 taksi</i>")
        return
    today = date.today().isoformat()
    add_transaction(message.from_user.id, "expense", amount, description, today)
    await state.clear()
    await message.answer(
        f"✅ Harajat qo'shildi:\n{format_amount(amount)} — {description}",
        reply_markup=main_menu_keyboard(message.from_user.id),
    )


@router.message(Form.waiting_income)
async def save_income(message: Message, state: FSMContext):
    amount, description = parse_amount_and_description(message.text or "")
    if amount is None:
        await message.answer("⚠️ Iltimos, summani raqam bilan boshlab yozing.\nMasalan: <i>500000 oylik</i>")
        return
    today = date.today().isoformat()
    add_transaction(message.from_user.id, "income", amount, description, today)
    await state.clear()
    await message.answer(
        f"✅ Daromad qo'shildi:\n{format_amount(amount)} — {description}",
        reply_markup=main_menu_keyboard(message.from_user.id),
    )


# ---------- Statistika Bo'limlari ----------

@router.message(F.text == BTN_TODAY)
async def today_summary(message: Message):
    today = date.today().isoformat()
    rows = get_transactions_by_date(message.from_user.id, today, type_="expense")
    text = format_simple_summary(rows, f"📊 Bugungi harajatlar ({format_date_human(today)})")
    await message.answer(text)


@router.message(F.text == BTN_WEEK)
async def week_summary(message: Message):
    today = date.today()
    start = today - timedelta(days=today.weekday())
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


# ================= QARZLAR TIYMI HANDLERLARI =================

@router.message(F.text == BTN_DEBT_HUB)
async def debt_hub(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🤝 <b>Qarzlar boshqaruvi bo'limi</b>\n\nBu yerda qarz berish, olish va to'lov muddatlarini aqlli nazorat qilishingiz mumkin.",
        reply_markup=debt_menu_keyboard()
    )


@router.message(F.text == BTN_ADD_DEBT)
async def add_debt_start(message: Message, state: FSMContext):
    await state.set_state(DebtForm.waiting_type)
    await message.answer("🔍 Qarz turini tanlang:", reply_markup=debt_type_inline())


@router.callback_query(F.data.startswith("dtype_"))
async def debt_type_selected(callback: CallbackQuery, state: FSMContext):
    dtype = callback.data.split("_")[1] # 'oldim' yoki 'berdim'
    await state.update_data(debt_type=dtype)
    await state.set_state(DebtForm.waiting_amount_person)
    await callback.message.edit_text("✏️ Qarz summasi va kimligini (ismni) yozing.\n\nMasalan: <code>150000 Vali</code>")
    await callback.answer()


@router.message(DebtForm.waiting_amount_person)
async def debt_amount_person_received(message: Message, state: FSMContext):
    amount, person = parse_amount_and_description(message.text or "")
    if amount is None or person == "Izohsiz":
        await message.answer("⚠️ Iltimos xatolikka yo'l qo'ymang. Summani raqam bilan boshlab yozing.\nMasalan: <code>150000 Vali</code>")
        return
    await state.update_data(amount=amount, person=person)
    await state.set_state(DebtForm.waiting_date)
    today = date.today()
    await message.answer("📅 Ushbu qarz qaysi sanaga qadar to'lanishi kerak? (Muddatni kalendardan tanlang):", reply_markup=debt_calendar_keyboard(today.year, today.month))


@router.callback_query(F.data == "dcal_ignore")
async def dcal_ignore(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data.startswith("dcal_nav_"))
async def dcal_navigate(callback: CallbackQuery):
    _, _, year, month = callback.data.split("_")
    await callback.message.edit_reply_markup(reply_markup=debt_calendar_keyboard(int(year), int(month)))
    await callback.answer()


@router.callback_query(F.data.startswith("dcal_day_"))
async def dcal_day_selected(callback: CallbackQuery, state: FSMContext):
    _, _, year, month, day = callback.data.split("_")
    selected_date = date(int(year), int(month), int(day)).isoformat()
    
    data = await state.get_data()
    dtype = data.get("debt_type")
    amount = data.get("amount")
    person = data.get("person")
    
    add_debt(callback.from_user.id, dtype, amount, person, selected_date)
    await state.clear()
    
    type_label = "📥 Olingan qarz (Oldim)" if dtype == "oldim" else "📤 Berilgan qarz (Berdim)"
    await callback.message.edit_text(
        f"✅ <b>Qarz tizimga muvaffaqiyatli yuklandi!</b>\n\n"
        f"<b>Holati:</b> {type_label}\n"
        f"<b>Kim bilan:</b> {person}\n"
        f"<b>Summa:</b> {format_amount(amount)}\n"
        f"<b>Qaytarish muddati:</b> {format_date_human(selected_date)}",
        reply_markup=None
    )
    await callback.answer()


@router.message(F.text == BTN_MY_DEBTS)
async def view_my_debts(message: Message):
    rows = get_active_debts(message.from_user.id)
    if not rows:
        await message.answer("🎉 Hozircha sizda hech qanday faol qarz majburiyatlari yo'q! Hamma hisoblar yopilgan.")
        return
    
    await message.answer("📋 <b>Sizning faol qarzlar ro'yxatingiz:</b>\n<i>(To'langanlarini o'chirish uchun tegishli tugmani bosing)</i>")
    
    for debt_id, dtype, amount, person, due_date in rows:
        icon = "📥 [Mening qarzim]" if dtype == "oldim" else "📤 [Mendan qarzdor]"
        text = (
            f"{icon} <b>{person}</b>\n"
            f"💰 Summa: {format_amount(amount)}\n"
            f"📅 Qaytarish sanasi: {format_date_human(due_date)}"
        )
        await message.answer(text, reply_markup=settle_debt_keyboard(debt_id))


@router.callback_query(F.data.startswith("settle_"))
async def settle_debt_handler(callback: CallbackQuery):
    debt_id = int(callback.data.split("_")[1])
    settle_debt(debt_id, callback.from_user.id)
    await callback.message.edit_text(callback.message.text + "\n\n💰 ✅ <b>[TO'LANDI] — Ushbu qarz yopildi va arxivlandi!</b>")
    await callback.answer("Qarz muvaffaqiyatli yopildi!")


# ================= PROFESSIONAL ADMIN PANEL MODULI =================

@router.message(F.text == BTN_ADMIN)
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return # begonalarga javob bermaydi
        
    total_users, exp_count, exp_sum, inc_count, inc_sum, active_debts_count = get_admin_stats()
    
    text = (
        "👑 <b>PROFESSIONAL ADMIN PANEL</b>\n"
        "━━━━━━━ ANALITIKA ━━━━━━━\n\n"
        f"👥 <b>Umumiy foydalanuvchilar:</b> {total_users} ta unikal profil\n\n"
        f"💸 <b>Jami Harajatlar:</b> {format_amount(exp_sum)} \n"
        f"↳ <i>Tranzaksiyalar soni: {exp_count} ta</i>\n\n"
        f"💰 <b>Jami Daromadlar:</b> {format_amount(inc_sum)} \n"
        f"↳ <i>Tranzaksiyalar soni: {inc_count} ta</i>\n\n"
        f"🤝 <b>Tizimdagi faol qarzlar:</b> {active_debts_count} ta ochiq hisob\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ <i>Tizim ideal holatda ishlamoqda. Data-analitika yangilandi.</i>"
    )
    await message.answer(text)


# ---------- Kalendar callbacklari (Tranzaksiya tarixi uchun) ----------

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
        raise RuntimeError("BOT_TOKEN topilmadi! .env faylini tekshiring.")
    init_db()
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

