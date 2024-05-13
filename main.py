from aiogram import Bot, Dispatcher
import asyncio

# import asyncpg, aiosqlite
from engine import create_db, drop_db
from handlers import handlers_router
from config import settings
from main_menu import set_main_menu
from middlewares.db import DatabaseSession
from engine import session_maker


async def main():
    # Создаем объекты бота и диспетчера
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()
    await drop_db()
    try:
        await create_db()
        print('Database created')
    except Exception as e:
        print(f'Raised exception: {e}')

    dp.update.middleware(DatabaseSession(session_pool=session_maker))
    dp.include_router(handlers_router)

    # Кладем пул в диспетчер
    dp.startup.register(set_main_menu)
    await dp.start_polling(bot)

if __name__ == '__main__':
    # Регистрируем асинхронную функцию в диспетчере,
    # которая будет выполняться на старте бота,

    asyncio.run(main())
