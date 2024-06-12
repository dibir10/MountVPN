from aiogram import Bot, Dispatcher
import asyncio
from aiogram.fsm.storage.memory import MemoryStorage

from VPNbot.engine import create_db, drop_db
from VPNbot.handlers.user_handlers import user_handlers_router
from VPNbot.handlers.admin_handlers import admin_handlers_router

from VPNbot.config import settings
from VPNbot.main_menu import set_main_menu
from VPNbot.middlewares.db import DatabaseSession
from VPNbot.engine import session_maker


async def main():
    # Создаем объекты бота и диспетчера
    bot = Bot(token=settings.BOT_TOKEN)
    storage = MemoryStorage()


    dp = Dispatcher(storage=storage)
    await drop_db()
    try:
        await create_db()
        print('Database created')
    except Exception as e:
        print(f'Raised exception: {e}')

    dp.update.middleware(DatabaseSession(session_pool=session_maker))
    dp.include_router(user_handlers_router)
    dp.include_router(admin_handlers_router)


    # Кладем пул в диспетчер
    dp.startup.register(set_main_menu)
    await dp.start_polling(bot)

if __name__ == '__main__':
    # Регистрируем асинхронную функцию в диспетчере,
    # которая будет выполняться на старте бота,

    asyncio.run(main())
