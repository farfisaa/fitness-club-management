import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from dotenv import load_dotenv

from database import init_db, close_db, create_empty_user, update_user_profile, get_schedule

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


class RegistrationStates(StatesGroup):
    waiting_for_fio = State()
    waiting_for_phone = State()


@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"

    await create_empty_user(user_id, username)

    await message.answer(
        f"Привет, {message.from_user.first_name}! Добро пожаловать в фитнес-клуб.\n"
        "Для регистрации в системе, пожалуйста, введи свои **ФИО** (например: Иванов Иван Иванoвич):",
        parse_mode="Markdown"
    )
    await state.set_state(RegistrationStates.waiting_for_fio)


@dp.message(RegistrationStates.waiting_for_fio)
async def process_fio(message: types.Message, state: FSMContext):
    await state.update_data(chosen_fio=message.text)

    kb = [
        [types.KeyboardButton(text="📱 Отправить свой номер", request_contact=True)]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)

    await message.answer("Отлично! Теперь нажми на кнопку ниже, чтобы поделиться номером телефона:",
                         reply_markup=keyboard)
    await state.set_state(RegistrationStates.waiting_for_phone)


@dp.message(RegistrationStates.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = message.text

    if not phone.replace('+', '').isdigit() or len(phone) < 9:
        await message.answer(
            "Непохоже на номер телефона. Пожалуйста, введи корректный номер (например, +375XXXXXXXXX):")
        return

    user_data = await state.get_data()
    fio = user_data.get("chosen_fio")
    user_id = message.from_user.id

    await update_user_profile(user_id, fio, phone)
    await state.clear()

    await message.answer(
        f"Ура, регистрация успешно завершена! 🎉\n\n"
        f"**Твоя анкета:**\n👤 ФИО: {fio}\n📞 Телефон: {phone}\n\n"
        f"Теперь ты можешь использовать команду /schedule для просмотра тренировок.",
        reply_markup=types.ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )


@dp.message(Command("schedule"))
async def cmd_schedule(message: types.Message):
    trainings = await get_schedule()

    if not trainings:
        await message.answer("Расписание тренировок пока пустое.")
        return

    response = "📅 **Актуальное расписание тренировок:**\n\n"
    for t in trainings:
        response += f"🏋️‍♂️ Тренировка: {t['training_title']}\n👤 Тренер: {t['coach_name']}\n⏰ Время: {t['time']}\n\n"

    await message.answer(response, parse_mode="Markdown")


@dp.message()
async def echo_message(message: types.Message):
    await message.answer(f"Ты вне регистрации написал: {message.text}")


async def main():
    await init_db()
    print("Бот успешно запущен и слушает сообщения...")
    try:
        await dp.start_polling(bot)
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())