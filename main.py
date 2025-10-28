import asyncio
from aiogram import Bot, Dispatcher
from app.heandler import router
from database.models import create_tables

async def main():
    await create_tables()

    bot = Bot('8025131403:AAGFSmTIO5do4UXS5_kWWdsNXr7trpS3Plo')
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот выключен')