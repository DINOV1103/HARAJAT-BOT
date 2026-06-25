"""
Har kuni belgilangan vaqtda (config.REMINDER_HOUR) qaytarish muddati
shu kunga to'g'ri kelgan qarzlar bo'yicha egasiga avtomatik bildirishnoma yuboradi.
"""

import logging
from datetime import date

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot

from config import REMINDER_HOUR, REMINDER_MINUTE, REMINDER_TIMEZONE
from database import get_debts_due_on, mark_debt_reminded
from utils import format_amount

logger = logging.getLogger(__name__)


async def send_debt_reminders(bot: Bot):
    today = date.today().isoformat()
    rows = get_debts_due_on(today)

    for debt_id, user_id, debt_type, person_name, amount in rows:
        if debt_type == "given":
            text = (
                "⏰ <b>Eslatma!</b>\n\n"
                f"Bugun <b>{person_name}</b> sizga {format_amount(amount)} qaytarishi kerak edi."
            )
        else:
            text = (
                "⏰ <b>Eslatma!</b>\n\n"
                f"Bugun siz <b>{person_name}</b>ga {format_amount(amount)} qaytarishingiz kerak."
            )
        try:
            await bot.send_message(user_id, text)
            mark_debt_reminded(debt_id, today)
        except Exception as e:
            logger.warning(f"Bildirishnoma yuborilmadi (user_id={user_id}): {e}")


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=REMINDER_TIMEZONE)
    scheduler.add_job(
        send_debt_reminders,
        trigger="cron",
        hour=REMINDER_HOUR,
        minute=REMINDER_MINUTE,
        args=[bot],
    )
    return scheduler
