"""
Bot konfiguratsiyasi - tokenni .env faylidan o'qiydi, doimiy sozlamalar shu yerda.
"""

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_NAME = "harajat.db"

# Admin panelga faqat shu Telegram ID kira oladi
ADMIN_ID = 1691140865

# Qarz qaytarish kuni bildirishnoma yuboriladigan vaqt (Toshkent vaqti bo'yicha)
REMINDER_HOUR = 9
REMINDER_MINUTE = 0
REMINDER_TIMEZONE = "Asia/Tashkent"
