from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from config import ADMIN_IDS


class AdminFilter(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user = getattr(event, "from_user", None)
        return bool(user and user.id in ADMIN_IDS)
