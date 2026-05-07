import asyncio

from aiogram import Bot, Dispatcher
from middlewares.throttling import ThrottlingMiddleware

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

dp.message.middleware(ThrottlingMiddleware())
dp.callback_query.middleware(ThrottlingMiddleware())

async def main():
    create_tables()
    await dp.start_polling(bot)


from aiogram.types import ErrorEvent

@dp.errors()
async def errors_handler(event: ErrorEvent):
    print("Ошибка:", event.exception)

if __name__ == "__main__":
    asyncio.run(main())
