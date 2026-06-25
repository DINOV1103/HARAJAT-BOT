"""
Admin panel - faqat config.ADMIN_ID uchun ochiq.
"""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import ADMIN_ID
from database import get_admin_stats, get_all_user_ids, get_all_users
from states import Form
from utils import format_amount
from keyboards import (
    admin_menu_keyboard,
    cancel_keyboard,
    ALL_MENU_BUTTONS,
    BTN_ADMIN_PANEL,
    BTN_ADMIN_STATS,
    BTN_ADMIN_BROADCAST,
    BTN_ADMIN_USERS,
)

router = Router()


def _is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


@router.message(F.text == BTN_ADMIN_PANEL)
async def open_admin_panel(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        await message.answer("⛔ Sizda ruxsat yo'q.")
        return
    await state.clear()
    await message.answer("🛠 <b>Admin panel</b>\n\nKerakli bo'limni tanlang:", reply_markup=admin_menu_keyboard())


@router.message(F.text == BTN_ADMIN_STATS)
async def show_stats(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        await message.answer("⛔ Sizda ruxsat yo'q.")
        return
    await state.clear()
    s = get_admin_stats()
    text = (
        "📊 <b>Bot statistikasi</b>\n\n"
        f"👥 Foydalanuvchilar: <b>{s['total_users']}</b>\n\n"
        f"💸 Harajat yozuvlari: {s['expense_count']} ta — {format_amount(s['expense_sum'])}\n"
        f"💰 Daromad yozuvlari: {s['income_count']} ta — {format_amount(s['income_sum'])}\n\n"
        f"📥 Faol berilgan qarzlar: {s['given_count']} ta — {format_amount(s['given_sum'])}\n"
        f"📤 Faol olingan qarzlar: {s['taken_count']} ta — {format_amount(s['taken_sum'])}\n"
        f"✅ Yopilgan qarzlar: {s['paid_count']} ta"
    )
    await message.answer(text)


@router.message(F.text == BTN_ADMIN_USERS)
async def show_users(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        await message.answer("⛔ Sizda ruxsat yo'q.")
        return
    await state.clear()
    users = get_all_users()
    if not users:
        await message.answer("👥 Hozircha foydalanuvchilar yo'q.")
        return
    lines = [f"👥 <b>Foydalanuvchilar ({len(users)} ta)</b>", ""]
    for user_id, username, full_name, first_seen in users[:30]:
        uname = f"@{username}" if username else "(username yo'q)"
        name = full_name or "Noma'lum"
        lines.append(f"• {name} {uname} — ID: <code>{user_id}</code>")
    if len(users) > 30:
        lines.append(f"\n... va yana {len(users) - 30} ta foydalanuvchi")
    await message.answer("\n".join(lines))


@router.message(F.text == BTN_ADMIN_BROADCAST)
async def ask_broadcast(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        await message.answer("⛔ Sizda ruxsat yo'q.")
        return
    await state.clear()
    await state.set_state(Form.waiting_broadcast_message)
    await message.answer(
        "📢 Barcha foydalanuvchilarga yubormoqchi bo'lgan xabarni yozing:",
        reply_markup=cancel_keyboard(),
    )


@router.message(Form.waiting_broadcast_message, ~F.text.in_(ALL_MENU_BUTTONS))
async def send_broadcast(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        await state.clear()
        return
    text = message.text
    user_ids = get_all_user_ids()
    sent, failed = 0, 0
    for uid in user_ids:
        try:
            await message.bot.send_message(uid, f"📢 <b>Xabar:</b>\n\n{text}")
            sent += 1
        except Exception:
            failed += 1
    await state.clear()
    await message.answer(
        f"✅ Xabar yuborildi.\nMuvaffaqiyatli: {sent}\nXato: {failed}",
        reply_markup=admin_menu_keyboard(),
    )
