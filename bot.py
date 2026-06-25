"""
HARAJAT bot - ishga tushirish nuqtasi.
Ishga tushirish: python bot.py

DIQQAT: Bu loyihada ataylab hech qanday subfolder (handlers/ va h.k.)
ishlatilmaydi - barcha fayllar bitta darajada turadi. Sababi: GitHub'ga
mobil orqali "Upload files" qilinganda, papka tuzilishi saqlanmaydi.
Shu uchun barcha modul nomlari tekis (flat) qilib tanlangan.
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from database import init_db
from scheduler import setup_scheduler

import handlers_common
import handlers_finance
import handlers_debts
import handlers_admin

logging.basicConfig(level=logging.INFO)

# Tartib muhim: 'handlers_common' birinchi bo'lishi kerak, chunki u
# "Asosiy menyu" tugmasi orqali har qanday holatni bekor qiladi.
ROUTERS = [
    handlers_common.router,
    handlers_finance.router,
    handlers_debts.router,
    handlers_admin.router,
]


async def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN topilmadi! Railway'da Settings > Variables bo'limiga "
            "BOT_TOKEN qo'shing (yoki lokal ishlatsangiz .env faylga yozing)."
        )

    init_db()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    for r in ROUTERS:
        dp.include_router(r)

    scheduler = setup_scheduler(bot)
    scheduler.start()
    logging.info("Bildirishnoma scheduler ishga tushdi.")

    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
