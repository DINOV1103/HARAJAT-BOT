"""
Moliya Menejeri - Tugmalar (Klaviaturalar).
"""

import calendar as cal_module
from datetime import date
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Asosiy tugmalar matnlari
BTN_EXPENSE = "💸 Harajat qo'shish"
BTN_INCOME = "💰 Daromad qo'shish"
BTN_STATS = "📊 Statistika bo'limi"
BTN_DEBTS = "📒 Qarz daftari"
BTN_NOTES = "📝 Eslatmalar"
BTN_CALENDAR = "📅 Kalendar"
BTN_ADMIN = "🛡 Admin Panel"
BTN_MAIN_MENU = "🏠 Asosiy menyu"

# Statistika menyusi tugmalari
BTN_STATS_TODAY = "📊 Bugungi hisobot"
BTN_STATS_WEEK = "📆 Haftalik hisobot"
BTN_STATS_MONTH = "🗓 Oylik hisobot"
BTN_STATS_TOTAL = "📈 Umumiy balans"

# Qarz menyusi tugmalari
BTN_DEBTS_ADD = "➕ Yangi qarz yozish"
BTN_DEBTS_LIST = "📜 Faol qarzlar"

# Eslatmalar menyusi tugmalari
BTN_NOTES_ADD = "➕ Yangi eslatma"
BTN_NOTES_LIST = "📜 Eslatmalar ro'yxati"

# Admin panel tugmalari
BTN_ADMIN_USERS = "👥 Foydalanuvchilar soni"
BTN_ADMIN_BROADCAST = "📢 Xabar yuborish"

MONTH_NAMES = [
    "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
    "Iyul", "Avgust", "Sentyabr", "Oktyabr", "Noyabr", "Dekabr",
]


def main_menu_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Asosiy boshqaruv menyusi."""
    keyboard_layout = [
        [KeyboardButton(text=BTN_EXPENSE), KeyboardButton(text=BTN_INCOME)],
        [KeyboardButton(text=BTN_STATS), KeyboardButton(text=BTN_DEBTS)],
        [KeyboardButton(text=BTN_NOTES), KeyboardButton(text=BTN_CALENDAR)],
    ]
    if is_admin:
        keyboard_layout.append([KeyboardButton(text=BTN_ADMIN)])
    return ReplyKeyboardMarkup(keyboard=keyboard_layout, resize_keyboard=True)


def cancel_keyboard() -> ReplyKeyboardMarkup:
    """Bekor qilish va orqaga qaytish klavaturasi."""
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=BTN_MAIN_MENU)]], resize_keyboard=True)


def stats_keyboard() -> ReplyKeyboardMarkup:
    """Statistika bo'limi ichki menyusi."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_STATS_TODAY), KeyboardButton(text=BTN_STATS_WEEK)],
            [KeyboardButton(text=BTN_STATS_MONTH), KeyboardButton(text=BTN_STATS_TOTAL)],
            [KeyboardButton(text=BTN_MAIN_MENU)]
        ],
        resize_keyboard=True
    )


def debts_keyboard() -> ReplyKeyboardMarkup:
    """Qarz daftari ichki menyusi."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_DEBTS_ADD), KeyboardButton(text=BTN_DEBTS_LIST)],
            [KeyboardButton(text=BTN_MAIN_MENU)]
        ],
        resize_keyboard=True
    )


def notes_keyboard() -> ReplyKeyboardMarkup:
    """Eslatmalar bo'limi ichki menyusi."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_NOTES_ADD), KeyboardButton(text=BTN_NOTES_LIST)],
            [KeyboardButton(text=BTN_MAIN_MENU)]
        ],
        resize_keyboard=True
    )


def admin_keyboard() -> ReplyKeyboardMarkup:
    """Faqat admin uchun xizmat qiladigan maxfiy menyu."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_ADMIN_USERS), KeyboardButton(text=BTN_ADMIN_BROADCAST)],
            [KeyboardButton(text=BTN_MAIN_MENU)]
        ],
        resize_keyboard=True
    )


def debt_type_inline() -> InlineKeyboardMarkup:
    """Qarz turini tanlash uchun tezkor inline tugmalar."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💸 Men qarz berdim", callback_data="debt_type_lent"),
            InlineKeyboardButton(text="💰 Men qarz oldim", callback_data="debt_type_borrowed")
        ],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="debt_cancel")]
    ])


def calendar_keyboard(year: int, month: int) -> InlineKeyboardMarkup:
    """Interaktiv kalendar generatori."""
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
    
