"""
Bot uchun tugmalar (klaviaturalar).
Admin boshqaruvi va dynamic tugmalar bilan kengaytirilgan shakli.
"""

import calendar as cal_module
from datetime import date

from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

BTN_EXPENSE = "💸 Harajat qo'shish"
BTN_INCOME = "💰 Daromad qo'shish"
BTN_TODAY = "📊 Bugungi harajat"
BTN_WEEK = "📆 Haftalik harajat"
BTN_MONTH = "🗓 Oylik harajat"
BTN_CALENDAR = "📅 Kalendar"
BTN_MAIN_MENU = "🏠 Asosiy menyu"

# Admin panel tugmalari
BTN_ADMIN_PANEL = "👑 Admin Panel"
BTN_BROADCAST = "📢 Barchaga xabar yuborish"

MONTH_NAMES = [
    "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
    "Iyul", "Avgust", "Sentyabr", "Oktyabr", "Noyabr", "Dekabr",
]


def main_menu_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    """Asosiy menyu tugmalari. Admin ID kiritilsa panel ochiladi."""
    buttons = [
        [KeyboardButton(text=BTN_EXPENSE), KeyboardButton(text=BTN_INCOME)],
        [KeyboardButton(text=BTN_TODAY), KeyboardButton(text=BTN_WEEK)],
        [KeyboardButton(text=BTN_MONTH), KeyboardButton(text=BTN_CALENDAR)],
    ]
    
    # Agar foydalanuvchi admin bo'lsa, maxsus tugmani qo'shish
    if user_id == 1691140865:
        buttons.append([KeyboardButton(text=BTN_ADMIN_PANEL)])
        
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def admin_menu_keyboard() -> ReplyKeyboardMarkup:
    """Admin panel ichki navigatsiya klaviaturasi."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_BROADCAST)],
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


