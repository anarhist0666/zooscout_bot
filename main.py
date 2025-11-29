import asyncio
from aiogram import Bot, Dispatcher
from app.heandler import router
from database.models import create_tables
async def main():
    # Инициализация базы данных - создание таблиц, если они не существуют
    await create_tables()

    # Создание экземпляра бота с использованием токена для авторизации в Telegram API
    bot = Bot('8025131403:AAH0ZsTT2bwYCfgeL4MZ2tSwFIruRROk4-w')
    
    # Создание диспетчера - основного объекта для обработки входящих сообщений
    dp = Dispatcher()
    
    # Подключение роутера с обработчиками сообщений (все команды и кнопки)
    dp.include_router(router)
    
    # Запуск бота в режиме long-polling (постоянный опрос серверов Telegram на наличие новых сообщений)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        # Запуск асинхронной функции main() - точка входа в приложение
        asyncio.run(main())
    except KeyboardInterrupt:
        # Обработка прерывания клавишами Ctrl+C - graceful shutdown
        print('Бот выключен')
