import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from dotenv import load_dotenv

# Загружаем токен из секретного файла .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
print("Считанный токен:", BOT_TOKEN)
# Инициализируем бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Ответ на команду /start
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(f"Привет, {message.from_user.first_name}! Я твой первый бот, созданный с помощью Git!")

# Эхо-эффект: бот повторяет любое текстовое сообщение
@dp.message()
async def echo_message(message: types.Message):
    await message.answer(message.text)

# Запуск бота
async def main():
    print("Бот успешно запущен и слушает сообщения...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())