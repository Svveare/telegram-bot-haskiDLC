import asyncio

from aiogram import Bot, Dispatcher

from config import TOKEN
from databases.queries import create_tables
from handlers.start import router as start_router
from handlers.menu import router as menu_router
from handlers.admin import admin_router

bot = Bot(token=TOKEN)
dp = Dispatcher()

dp.include_router(start_router)
dp.include_router(menu_router)
dp.include_router(admin_router)


async def main():
    create_tables()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
