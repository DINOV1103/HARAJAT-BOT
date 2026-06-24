"""
Bot uchun tugmalar (klaviaturalar).
Admin panel va smart qarzlar interfeysi bilan boyitilgan.
"""

import calendar as cal_module
from datetime import date

from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

# Strukturaviy tugmalar matnlari
BTN_EXPENSE = "💸 Harajat qo'shish"
BTN_INCOME = "💰 Daromad qo'shish"
BTN_TODAY = "📊 Bugungi harajat"
BTN_WEEK = "📆 Haftalik harajat"
BTN_MONTH = "🗓 Oylik harajat"
BTN_CALENDAR = "📅 Kalendar"
BTN_MAIN_MENU = "🏠 Asosiy menyu"

# Yangi bo'limlar
BTN_DEBT_HUB = "🤝 Qarzlar bo'limi"
BTN_ADD_DEBT = "➕ Qarz qo'shish"
BTN_MY_DEBTS = "📋 Qarzlarim (Ro'yxat)"
BTN_ADMIN = "👑 Professional Admin Panel"

MONTH_NAMES = [
    "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
    "Iyul", "Avgust", "Sentyabr", "Oktyabr", "Noyabr", "Dekabr",
]


def main_menu_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    """Asosiy menyu. Agar foydalanuvchi admin bo'lsa, maxsus tugma qo'shiladi."""
    buttons = [
        [KeyboardButton(text=BTN_EXPENSE), KeyboardButton(text=BTN_INCOME)],
        [KeyboardButton(text=BTN_TODAY), KeyboardButton(text=BTN_WEEK)],
        [KeyboardButton(text=BTN_MONTH), KeyboardButton(text=BTN_CALENDAR)],
        [KeyboardButton(text=BTN_DEBT_HUB)]
    ]
    
    # Admin tekshiruvi
    if user_id == 1691140865:
        buttons.append([KeyboardButton(text=BTN_ADMIN)])
        
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def debt_menu_keyboard() -> ReplyKeyboardMarkup:
    """Qarzlar bo'limi boshqaruv hubi."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_ADD_DEBT), KeyboardButton(text=BTN_MY_DEBTS)],
            [KeyboardButton(text=BTN_MAIN_MENU)]
        ],
        resize_keyboard=True
    )


def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_MAIN_MENU)]],
        resize_keyboard=True,
    )


def calendar_keyboard(year: int, month: int) -> InlineKeyboardMarkup:
    """Tranzaksiyalar tarixini ko'rish kalendari."""
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
            InlineKeyboardButton(text="⬅️", callback_data=f"cal_nav_{prev_year}_{prev_month}"),
            InlineKeyboardButton(text=f"{MONTH_NAMES[month - 1]} {year}", callback_data="cal_ignore"),
            InlineKeyboardButton(text="➡️", callback_data=f"cal_nav_{next_year}_{next_month}"),
        ],
        [InlineKeyboardButton(text=d, callback_data="cal_ignore") for d in ["Du", "Se", "Cho", "Pa", "Ju", "Sh", "Ya"]],
    ]

    today = date.today()
    for week in cal.monthdayscalendar(year, month):
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text=" ", callback_data="cal_ignore"))
            else:
                label = f"•{day}" if (year, month, day) == (today.year, today.month, today.day) else str(day)
                row.append(InlineKeyboardButton(text=label, callback_data=f"cal_day_{year}_{month}_{day}"))
        buttons.append(row)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ================= QARZLAR UCHUN KEYBOARDLAR =================

def debt_type_inline() -> InlineKeyboardMarkup:
    """Qarz turini tanlash uchun smart inline tugmalar."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📥 Oldim (Qarzdorman)", callback_data="dtype_oldim"),
            InlineKeyboardButton(text="📤 Berdim (Haqdormand)", callback_data="dtype_berdim")
        ]
    ])


def debt_calendar_keyboard(year: int, month: int) -> InlineKeyboardMarkup:
    """Qarz qaytarilish muddati uchun alohida dcal_ prefiksli kalendar."""
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
            InlineKeyboardButton(text="⬅️", callback_data=f"dcal_nav_{prev_year}_{prev_month}"),
            InlineKeyboardButton(text=f"{MONTH_NAMES[month - 1]} {year}", callback_data="dcal_ignore"),
            InlineKeyboardButton(text="➡️", callback_data=f"dcal_nav_{next_year}_{next_month}"),
        ],
        [InlineKeyboardButton(text=d, callback_data="dcal_ignore") for d in ["Du", "Se", "Cho", "Pa", "Ju", "Sh", "Ya"]],
    ]

    today = date.today()
    for week in cal.monthdayscalendar(year, month):
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text=" ", callback_data="dcal_ignore"))
            else:
                label = f"•{day}" if (year, month, day) == (today.year, today.month, today.day) else str(day)
                row.append(InlineKeyboardButton(text=label, callback_data=f"dcal_day_{year}_{month}_{day}"))
        buttons.append(row)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def settle_debt_keyboard(debt_id: int) -> InlineKeyboardMarkup:
    """Har bir qarz ostida turadigan 'To'landi' trigger tugmasi."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ To'landi (Yopish)", callback_data=f"settle_{debt_id}")]
    ])

