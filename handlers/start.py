from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from keyboards.inline import inline_kb_start
from databases.queries import add_user

router = Router()


@router.message(Command("start"))
async def start(message: Message):
    add_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
    )

    await message.answer(
        "👋 Приветствуем! Вы перешли в Telegram-бот Haski Client.\n\n"
        "Для продолжения выберите кнопку ниже:",
        reply_markup=inline_kb_start,
    )
