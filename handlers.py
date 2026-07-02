# handlers.py
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
import db  # Импортируем нашу папку-пакет работы с СУБД

# Инициализируем роутер, в который будут складываться все обработчики (main.py его заберет)
router = Router()


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Вспомогательная функция, которая создает главное меню бота.
    Кнопки будут располагаться внизу экрана у пользователя.
    """
    kb = [
        [
            KeyboardButton(text="👤 Мой Профиль"),
            KeyboardButton(text="📅 Моё Расписание")
        ],
        [
            KeyboardButton(text="🏋️‍♂️ Направления клуба")
        ]
    ]
    # resize_keyboard=True делает кнопки аккуратными, а не на пол-экрана
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


@router.message(Command("start"))
async def cmd_start(message: Message):
    """
    Ловит команду /start.
    1. Проверяет наличие юзернейма.
    2. Вызывает нативный SQL-метод для автоматической регистрации.
    """
    username = message.from_user.username

    if not username:
        await message.answer(
            "❌ **Ошибка:** У вас в настройках Telegram не задан публичный `@username`.\n"
            "Пожалуйста, создайте его в настройках профиля Telegram, чтобы бот мог связать вас с базой данных клуба."
        )
        return

    # Отправляем данные в db/users.py
    db.users.register(
        telegram_id=message.from_user.id,
        username=username,
        full_name=message.from_user.full_name
    )

    await message.answer(
        f"🏃‍♂️ **Добро пожаловать в фитнес-клуб!** 👋\n\n"
        f"Вы успешно авторизованы под логином: @{username}\n"
        f"Используйте меню ниже для навигации.",
        reply_markup=get_main_keyboard()
    )


@router.message(F.text == "👤 Мой Профиль")
async def show_profile(message: Message):
    """
    Ловит нажатие кнопки "👤 Мой Профиль".
    Делает SELECT-запрос с LEFT JOIN к таблице абонементов.
    """
    username = message.from_user.username
    profile = db.users.get_profile(username)

    if profile:
        text = (
            "📋 **Ваш профиль в базе данных:**\n\n"
            f"👤 **ФИО:** {profile['fio']}\n"
            f"🌐 **Логин:** @{profile['user_name']}\n"
            f"🎖️ **Роль в системе:** {profile['role_type']}\n"
            f"───────────────────\n"
            f"🎫 **Тип абонемента:** {profile['membership_type']}\n"
            f"⏳ **Срок действия:** {profile['validity_date']}"
        )
    else:
        text = "❌ Вы не найдены в базе данных клуба. Введите /start для регистрации."

    await message.answer(text, parse_mode="Markdown")


@router.message(F.text == "📅 Моё Расписание")
async def show_schedule(message: Message):
    """
    Ловит нажатие кнопки "📅 Моё Расписание".
    Вызывает сложный JOIN из 5 таблиц для формирования расписания занятий.
    """
    username = message.from_user.username
    schedule = db.trainings.get_client_schedule(username)

    if not schedule:
        await message.answer(
            "🗓️ **У вас пока нет запланированных тренировок.**\n"
            "Либо на ваш аккаунт еще не оформлен действующий абонемент."
        )
        return

    response = "📋 **Ваше актуальное расписание занятий:**\n\n"

    for item in schedule:
        # Для каждой тренировки выводим информацию и крепим текстовую команду на её удаление
        response += (
            f"🏋️‍♂️ **Направление:** {item['training_name']}\n"
            f"🕒 **Время:** {item['day_of_the_week']} в {item['time']}\n"
            f"👨‍🏫 **Инструктор:** {item['coach_fio']}\n"
            f"❌ **Отменить занятие:** /cancel_{item['training_id']}\n"
            f"───────────────────\n"
        )

    await message.answer(response, parse_mode="Markdown")


@router.message(F.text == "🏋️‍♂️ Направления клуба")
async def show_club_directions(message: Message):
    """
    Ловит нажатие кнопки "🏋️‍♂️ Направления клуба".
    Выводит справочник типов тренировок из таблицы training_type.
    """
    types = db.training_types.get_all()

    if not types:
        await message.answer("❌ В данный момент список направлений пуст.")
        return

    response = "💪 **Доступные направления в нашем клубе:**\n\n"
    for t in types:
        response += (
            f"🔹 **{t['type']}**\n"
            f"🕒 Стандартное время: {t['time']}\n"
            f"👥 Макс. мест в группе: {t['num_of_places']}\n\n"
        )

    await message.answer(response, parse_mode="Markdown")


@router.message(F.text.startswith("/cancel_"))
async def process_cancel_training(message: Message):
    """
    Динамический обработчик текстовых команд удаления.
    Срабатывает, когда пользователь кликает по ссылкам вида /cancel_1, /cancel_2 и т.д.
    """
    try:
        # Разбиваем строку по знаку подчеркивания и забираем ID тренировки (число)
        training_id = int(message.text.split("_")[1])

        # Вызываем метод DELETE из db/trainings.py
        success = db.trainings.delete_by_id(training_id)

        if success:
            await message.answer(
                f"✅ **Успешно!** Тренировка №{training_id} была удалена из вашего расписания.",
                reply_markup=get_main_keyboard()
            )
        else:
            await message.answer(
                "❌ **Ошибка:** Не удалось отменить тренировку. Возможно, она уже была удалена ранее или не существует."
            )
    except (IndexError, ValueError):
        await message.answer("❌ **Ошибка:** Неверный формат команды для отмены занятия.")