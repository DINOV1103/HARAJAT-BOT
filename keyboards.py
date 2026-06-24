import calendar as cal_module
from datetime import date
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Tugmalar
BTN_EXPENSE = "💸 Harajat qo'shish"
BTN_INCOME = "💰 Daromad qo'shish"
BTN_TODAY = "📊 Bugungi"
BTN_WEEK = "📆 Haftalik"
BTN_MONTH = "🗓 Oylik"
BTN_CALENDAR = "📅 Kalendar"
BTN_DEBTS = "📒 Qarz daftari"
BTN_MAIN_MENU = "🏠 Asosiy menyu"

MONTH_NAMES = ["Yanvar","Fevral","Mart","Aprel","May","Iyun","Iyul","Avgust","Sentyabr","Oktyabr","Noyabr","Dekabr"]


def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(BTN_EXPENSE), KeyboardButton(BTN_INCOME)],
            [KeyboardButton(BTN_TODAY), KeyboardButton(BTN_WEEK)],
            [KeyboardButton(BTN_MONTH), KeyboardButton(BTN_CALENDAR)],
            [KeyboardButton(BTN_DEBTS)],
        ],
        resize_keyboard=True
    )


def debt_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("➕ Qarz berdim")],
            [KeyboardButton("➖ Qarz oldim")],
            [KeyboardButton("📋 Qarzlar ro'yxati")],
            [KeyboardButton(BTN_MAIN_MENU)],
        ],
        resize_keyboard=True
    )


def cancel_keyboard():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(BTN_MAIN_MENU)]], resize_keyboard=True)


def calendar_keyboard(year: int, month: int, callback_prefix="debt_due_"):
    # ... (oldingi calendar_keyboard funksiyasi bilan bir xil, lekin callback_prefix qo'shildi)
    cal = cal_module.Calendar(firstweekday=0)
    if month == 1: prev_y, prev_m = year-1, 12
    else: prev_y, prev_m = year, month-1
    if month == 12: next_y, next_m = year+1, 1
    else: next_y, next_m = year, month+1

    buttons = [
        [InlineKeyboardButton("⬅️", callback_data=f"{callback_prefix}nav_{prev_y}_{prev_m}"),
         InlineKeyboardButton(f"{MONTH_NAMES[month-1]} {year}", callback_data="ignore"),
         InlineKeyboardButton("➡️", callback_data=f"{callback_prefix}nav_{next_y}_{next_m}")],
        [InlineKeyboardButton(d, callback_data="ignore") for d in ["Du","Se","Cho","Pa","Ju","Sh","Ya"]]
    ]

    today = date.today()
    for week in cal.monthdayscalendar(year, month):
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(" ", callback_data="ignore"))
            else:
                label = f"•{day}" if (year, month, day) == (today.year, today.month, today.day) else str(day)
                row.append(InlineKeyboardButton(label, callback_data=f"{callback_prefix}day_{year}_{month}_{day}"))
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)



