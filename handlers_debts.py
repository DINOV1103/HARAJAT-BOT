"""
Qarz daftari: qarz berish, qarz olish, qarzlar ro'yxati va yopish.
"""

from datetime import date

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database import add_debt, get_debts, mark_debt_paid
from states import Form
from utils import format_amount, format_date_human, parse_plain_amount
from keyboards import (
    debt_menu_keyboard,
    cancel_keyboard,
    calendar_keyboard,
    ALL_MENU_BUTTONS,
    BTN_DEBT_NOTEBOOK,
    BTN_DEBT_GIVE,
    BTN_DEBT_TAKE,
    BTN_DEBTS_VIEW,
)

router = Router()


# ---------- Ro'yxatni shakllantirish ----------

def build_debts_view(given, taken):
    today_str = date.today().isoformat()
    lines = ["<b>📋 Qarzlar ro'yxati</b>", ""]
    buttons = []

    if given:
        lines.append("📥 <b>Sizga qarz bo'lganlar:</b>")
        for debt_id, person, amount, due_date in given:
            mark = "⏰" if due_date < today_str else "▫️"
            lines.append(f"{mark} {person} — {format_amount(amount)} (qaytarish: {format_date_human(due_date)})")
            buttons.append([InlineKeyboardButton(
                text=f"✅ {person} — {format_amount(amount)}",
                callback_data=f"debt:paid:{debt_id}",
            )])
        lines.append("")

    if taken:
        lines.append("📤 <b>Sizning qarzlaringiz:</b>")
        for debt_id, person, amount, due_date in taken:
            mark = "⏰" if due_date < today_str else "▫️"
            lines.append(f"{mark} {person} — {format_amount(amount)} (qaytarish: {format_date_human(due_date)})")
            buttons.append([InlineKeyboardButton(
                text=f"✅ {person} — {format_amount(amount)}",
                callback_data=f"debt:paid:{debt_id}",
            )])
        lines.append("")

    if not given and not taken:
        lines.append("Hozircha faol qarzlar yo'q. 🎉")
    elif buttons:
        lines.append("<i>⏰ — muddati o'tgan. Qaytarilgan qarzni yopish uchun pastdagi tugmani bosing.</i>")

    text = "\n".join(lines)
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return text, keyboard


# ---------- Asosiy tugmalar ----------

@router.message(F.text == BTN_DEBT_NOTEBOOK)
async def open_debt_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("📒 <b>Qarz daftari</b>\n\nKerakli amalni tanlang:", reply_markup=debt_menu_keyboard())


@router.message(F.text == BTN_DEBT_GIVE)
async def ask_debt_given(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(Form.waiting_debt_name)
    await state.update_data(debt_type="given")
    await message.answer("🤝 Kimga qarz berdingiz? Ismini yozing.", reply_markup=cancel_keyboard())


@router.message(F.text == BTN_DEBT_TAKE)
async def ask_debt_taken(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(Form.waiting_debt_name)
    await state.update_data(debt_type="taken")
    await message.answer("📥 Kimdan qarz oldingiz? Ismini yozing.", reply_markup=cancel_keyboard())


@router.message(F.text == BTN_DEBTS_VIEW)
async def view_debts(message: Message, state: FSMContext):
    await state.clear()
    given = get_debts(message.from_user.id, type_="given")
    taken = get_debts(message.from_user.id, type_="taken")
    text, keyboard = build_debts_view(given, taken)
    await message.answer(text, reply_markup=keyboard)


# ---------- Bosqichma-bosqich qarz qo'shish ----------

@router.message(Form.waiting_debt_name, ~F.text.in_(ALL_MENU_BUTTONS))
async def process_debt_name(message: Message, state: FSMContext):
    person_name = (message.text or "").strip()
    if not person_name:
        await message.answer("⚠️ Iltimos, ismni matn ko'rinishida yozing.")
        return
    await state.update_data(person_name=person_name)
    data = await state.get_data()
    verb = "berdingiz" if data["debt_type"] == "given" else "oldingiz"
    await state.set_state(Form.waiting_debt_amount)
    await message.answer(f"💰 Qancha summa {verb}? (faqat raqam, masalan: 100000)")


@router.message(Form.waiting_debt_amount, ~F.text.in_(ALL_MENU_BUTTONS))
async def process_debt_amount(message: Message, state: FSMContext):
    amount = parse_plain_amount(message.text)
    if amount is None:
        await message.answer("⚠️ Iltimos, summani faqat raqam bilan yozing. Masalan: <i>100000</i>")
        return
    await state.update_data(amount=amount)
    await state.set_state(Form.waiting_debt_date)
    today = date.today()
    await message.answer(
        "📅 Qaytarish sanasini tanlang:",
        reply_markup=calendar_keyboard(today.year, today.month, prefix="ddate"),
    )


@router.message(Form.waiting_debt_date, ~F.text.in_(ALL_MENU_BUTTONS))
async def remind_use_calendar(message: Message):
    await message.answer("📅 Iltimos, yuqoridagi kalendardan kunni tanlang (yoki 🏠 Asosiy menyu tugmasini bosing).")


# ---------- Qaytarish sanasi uchun kalendar callbacklari ----------

@router.callback_query(Form.waiting_debt_date, F.data == "ddate:ignore")
async def ddate_ignore(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(Form.waiting_debt_date, F.data.startswith("ddate:nav:"))
async def ddate_navigate(callback: CallbackQuery):
    _, _, year, month = callback.data.split(":")
    try:
        await callback.message.edit_reply_markup(reply_markup=calendar_keyboard(int(year), int(month), prefix="ddate"))
    except Exception:
        pass
    await callback.answer()


@router.callback_query(Form.waiting_debt_date, F.data.startswith("ddate:day:"))
async def ddate_day_selected(callback: CallbackQuery, state: FSMContext):
    _, _, year, month, day = callback.data.split(":")
    due_date = date(int(year), int(month), int(day)).isoformat()
    data = await state.get_data()
    debt_type = data["debt_type"]
    person_name = data["person_name"]
    amount = data["amount"]

    add_debt(callback.from_user.id, debt_type, person_name, amount, due_date)
    await state.clear()

    direction = "Siz berdingiz (sizga qaytarishi kerak)" if debt_type == "given" else "Siz oldingiz (siz qaytarishingiz kerak)"
    confirm_text = (
        f"✅ Qarz qo'shildi!\n\n👤 {person_name}\n💰 {format_amount(amount)}\n📌 {direction}\n"
        f"📅 Qaytarish sanasi: {format_date_human(due_date)}\n\n"
        f"⏰ {format_date_human(due_date)} kuni sizga avtomatik eslatma yuboraman."
    )
    try:
        await callback.message.edit_text(confirm_text)
    except Exception:
        await callback.message.answer(confirm_text)
    await callback.message.answer("📒 Qarz daftari", reply_markup=debt_menu_keyboard())
    await callback.answer("Saqlandi ✅")


# ---------- Qarzni yopish (qaytarilgan deb belgilash) ----------

@router.callback_query(F.data.startswith("debt:paid:"))
async def debt_mark_paid(callback: CallbackQuery):
    debt_id = int(callback.data.split(":")[2])
    mark_debt_paid(debt_id, callback.from_user.id)
    given = get_debts(callback.from_user.id, type_="given")
    taken = get_debts(callback.from_user.id, type_="taken")
    text, keyboard = build_debts_view(given, taken)
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer("✅ Qarz yopilgan deb belgilandi")
