"""
Umumiy buyruqlar: /start (foydalanuvchini ro'yxatga oladi) va asosiy menyuga qaytish.
"""

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import ADMIN_ID
from database import register_user
from keyboards import main_menu_for, BTN_MAIN_MENU

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    register_user(message.from_user.id, message.from_user.username, message.from_user.full_name)

    text = (
        "Salom! Men sizning shaxsiy <b>HARAJAT</b> botingizman 💰\n\n"
        "Quyidagi tugmalar orqali harajat/daromad qo'shing, qarzlarni boshqaring "
        "va moliyaviy holatingizni kuzating."
    )
    if message.from_user.id == ADMIN_ID:
        text += "\n\n🛠 Siz <b>admin</b> sifatida tanildingiz — quyida admin panel ham mavjud."

    await message.answer(text, reply_markup=main_menu_for(message.from_user.id))


@router.message(F.text == BTN_MAIN_MENU)
async def back_to_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Asosiy menyu", reply_markup=main_menu_for(message.from_user.id))
