"""
Bot uchun tugmalar (klaviaturalar).
"""

import calendar as cal_module
from datetime import date

from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

# Asosiy menyu tugmalari matni (bir joyda saqlanadi, xatoga yo'l qoldirmaslik uchun)
BTN_EXPENSE = "💸 Harajat qo'shish"
BTN_INCOME = "💰 Daromad qo'shish"
BTN_TODAY = "📊 Bugungi harajat"
BTN_WEEK = "📆 Haftalik harajat"
BTN_MONTH = "🗓 Oylik harajat"
BTN_CALENDAR = "📅 Kalendar"
BTN_MAIN_MENU = "🏠 Asosiy menyu"

MONTH_NAMES = [
    "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
    "Iyul", "Avgust", "Sentyabr", "Oktyabr", "Noyabr", "Dekabr",
]


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_EXPENSE), KeyboardButton(text=BTN_INCOME)],
            [KeyboardButton(text=BTN_TODAY), KeyboardButton(text=BTN_WEEK)],
            [KeyboardButton(text=BTN_MONTH), KeyboardButton(text=BTN_CALENDAR)],
        ],
        resize_keyboard=True,
    )


def cancel_keyboard() -> ReplyKeyboardMarkup:
    """Summa kiritish kutilayotganda ko'rsatiladigan klaviatura (bekor qilish uchun)."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_MAIN_MENU)]],
        resize_keyboard=True,
    )


def calendar_keyboard(year: int, month: int) -> InlineKeyboardMarkup:
    """Berilgan oy uchun inline kalendar tugmalarini quradi."""
    cal = cal_module.Calendar(firstweekday=0)  # Dushanbadan boshlanadi

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
