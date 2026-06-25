"""
Bot uchun barcha tugmalar (klaviaturalar).
"""

import calendar as cal_module
from datetime import date

from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from config import ADMIN_ID

# ---------- Tugma matnlari ----------

BTN_EXPENSE = "💸 Harajat qo'shish"
BTN_INCOME = "💰 Daromad qo'shish"
BTN_TODAY = "📊 Bugungi harajat"
BTN_WEEK = "📆 Haftalik harajat"
BTN_MONTH = "🗓 Oylik harajat"
BTN_CALENDAR = "📅 Kalendar"
BTN_BALANCE = "📈 Umumiy balans"
BTN_DEBT_NOTEBOOK = "📒 Qarz daftari"
BTN_MAIN_MENU = "🏠 Asosiy menyu"

BTN_DEBT_GIVE = "🤝 Qarz berish"
BTN_DEBT_TAKE = "📥 Qarz olish"
BTN_DEBTS_VIEW = "📋 Qarzlar"

BTN_ADMIN_PANEL = "🛠 Admin panel"
BTN_ADMIN_STATS = "📊 Statistika"
BTN_ADMIN_BROADCAST = "📢 Xabar yuborish"
BTN_ADMIN_USERS = "👥 Foydalanuvchilar"

# Holat (state) ichida turib tasodifan bosilsa ham to'g'ri ishlashi uchun:
# har qanday "erkin matn kutilayotgan" handler shu ro'yxatdagi tugmalarni
# summa/ism o'rniga navigatsiya buyrug'i sifatida tushunishi kerak.
ALL_MENU_BUTTONS = {
    BTN_EXPENSE, BTN_INCOME, BTN_TODAY, BTN_WEEK, BTN_MONTH, BTN_CALENDAR,
    BTN_BALANCE, BTN_DEBT_NOTEBOOK, BTN_MAIN_MENU,
    BTN_DEBT_GIVE, BTN_DEBT_TAKE, BTN_DEBTS_VIEW,
    BTN_ADMIN_PANEL, BTN_ADMIN_STATS, BTN_ADMIN_BROADCAST, BTN_ADMIN_USERS,
}

MONTH_NAMES = [
    "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
    "Iyul", "Avgust", "Sentyabr", "Oktyabr", "Noyabr", "Dekabr",
]


# ---------- Reply klaviaturalar ----------

def main_menu_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=BTN_EXPENSE), KeyboardButton(text=BTN_INCOME)],
        [KeyboardButton(text=BTN_TODAY), KeyboardButton(text=BTN_WEEK)],
        [KeyboardButton(text=BTN_MONTH), KeyboardButton(text=BTN_CALENDAR)],
        [KeyboardButton(text=BTN_BALANCE)],
        [KeyboardButton(text=BTN_DEBT_NOTEBOOK)],
    ]
    if is_admin:
        rows.append([KeyboardButton(text=BTN_ADMIN_PANEL)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def main_menu_for(user_id: int) -> ReplyKeyboardMarkup:
    """Foydalanuvchi admin bo'lsa, admin panel tugmasi bilan asosiy menyu qaytaradi."""
    return main_menu_keyboard(is_admin=(user_id == ADMIN_ID))


def debt_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_DEBT_GIVE), KeyboardButton(text=BTN_DEBT_TAKE)],
            [KeyboardButton(text=BTN_DEBTS_VIEW)],
            [KeyboardButton(text=BTN_MAIN_MENU)],
        ],
        resize_keyboard=True,
    )


def admin_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_ADMIN_STATS), KeyboardButton(text=BTN_ADMIN_BROADCAST)],
            [KeyboardButton(text=BTN_ADMIN_USERS)],
            [KeyboardButton(text=BTN_MAIN_MENU)],
        ],
        resize_keyboard=True,
    )


def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_MAIN_MENU)]],
        resize_keyboard=True,
    )


# ---------- Inline kalendar ----------

def calendar_keyboard(year: int, month: int, prefix: str = "cal") -> InlineKeyboardMarkup:
    """
    prefix='cal'   -> kunlar tarixini ko'rish uchun (statistika)
    prefix='ddate' -> qarz qaytarish sanasini tanlash uchun
    """
    cal = cal_module.Calendar(firstweekday=0)

    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1

    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1

    buttons = [
        [
            InlineKeyboardButton(text="⬅️", callback_data=f"{prefix}:nav:{prev_year}:{prev_month}"),
            InlineKeyboardButton(text=f"{MONTH_NAMES[month - 1]} {year}", callback_data=f"{prefix}:ignore"),
            InlineKeyboardButton(text="➡️", callback_data=f"{prefix}:nav:{next_year}:{next_month}"),
        ],
        [InlineKeyboardButton(text=d, callback_data=f"{prefix}:ignore") for d in ["Du", "Se", "Cho", "Pa", "Ju", "Sh", "Ya"]],
    ]

    today = date.today()
    for week in cal.monthdayscalendar(year, month):
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text=" ", callback_data=f"{prefix}:ignore"))
            else:
                label = f"•{day}" if (year, month, day) == (today.year, today.month, today.day) else str(day)
                row.append(InlineKeyboardButton(text=label, callback_data=f"{prefix}:day:{year}:{month}:{day}"))
        buttons.append(row)

    return InlineKeyboardMarkup(inline_keyboard=buttons)
