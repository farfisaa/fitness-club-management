# main.py
import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import router


async def main():
    # 1. Инициализируем бота, передавая ему токен из конфигуратора
    bot = Bot(token=BOT_TOKEN)

    # 2. Создаем Диспетчер — это главный менеджер событий aiogram
    dp = Dispatcher()

    # 3. Передаем Диспетчеру наш роутер из handlers.py.
    # Теперь бот знает, какие кнопки и команды существуют
    dp.include_router(router)

    print("🚀 Бот успешно запущен и слушает серверы Telegram...")

    # 4. Стираем сообщения, которые боту успели написать, пока он был выключен
    await bot.delete_webhook(drop_pending_updates=True)

    # 5. Запускаем "Polling" — бесконечный асинхронный цикл опроса серверов Telegram
    await dp.start_polling(bot)


if __name__ == "__main__":
    # Запуск асинхронного движка asyncio для управления функциями
    asyncio.run(main())