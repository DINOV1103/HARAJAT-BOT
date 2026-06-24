# keyboards.py
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_keyboard():
    kb = [
        [KeyboardButton("Kirim ➕"), KeyboardButton("Chiqim ➖")],
        [KeyboardButton("Kunlik harajatlar"), KeyboardButton("Oylik harajatlar")],
        [KeyboardButton("Kalendar"), KeyboardButton("Qarz daftari")]
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def admin_inline():
    kb = [
        [InlineKeyboardButton("Umumiy xabar yuborish", callback_data="admin_broadcast")],
        [InlineKeyboardButton("Statistika", callback_data="admin_stats")]
    ]
    return InlineKeyboardMarkup(kb)

def confirm_inline(yes_data="confirm_yes", no_data="confirm_no"):
    kb = [
        [InlineKeyboardButton("Tasdiqlash", callback_data=yes_data),
         InlineKeyboardButton("Bekor qilish", callback_data=no_data)]
    ]
    return InlineKeyboardMarkup(kb)