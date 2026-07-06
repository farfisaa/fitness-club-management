# handlers.py
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
#
from aiogram.types import CallbackQuery
from datetime import datetime, timedelta
import db  # Импортируем нашу папку-пакет работы с СУБД
from datetime import datetime, timedelta  # Библиотека для работы с датами

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
            KeyboardButton(text="🏋️‍♂️ Направления клуба"),
            KeyboardButton(text="🎫 Купить абонемент")
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
    """
    username = message.from_user.username
    schedule = db.trainings.get_client_schedule(username)

    if not schedule:
        await message.answer(
            "🗓️ <b>У вас пока нет запланированных тренировок.</b>\n"
            "Либо на ваш аккаунт еще не оформлен действующий абонемент.",
            parse_mode="HTML"  # Меняем разметку на HTML!
        )
        return

    response = "📋 <b>Ваше актуальное расписание занятий:</b>\n\n"

    for item in schedule:
        # Заменяем ** на теги <b> и </b>, а подчеркивание теперь полностью безопасно!
        response += (
            f"🏋️‍♂️ <b>Направление:</b> {item['training_name']}\n"
            f"🕒 <b>Время:</b> {item['day_of_the_week']} в {item['time']}\n"
            f"👨‍🏫 <b>Инструктор:</b> {item['coach_fio']}\n"
            f"❌ <b>Отменить занятие:</b> /cancel_{item['training_id']}\n"
            f"───────────────────\n"
        )

    # Меняем parse_mode на HTML
    await message.answer(response, parse_mode="HTML")


@router.message(F.text == "🏋️‍♂️ Направления клуба")
async def show_club_directions(message: Message):
    types = db.training_types.get_all()

    if not types:
        await message.answer("❌ В данный момент список направлений пуст.")
        return

    await message.answer("💪 **Доступные направления в нашем клубе:**")

    for t in types:
        # Для каждого направления создаем свою кнопку "Записаться"
        inline_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"✅ Записаться на {t['type']}",
                        callback_data=f"book_tr:{t['tr_type_id']}"  # Передаем ID типа тренировки
                    )
                ]
            ]
        )

        response = (
            f"🔹 **{t['type']}**\n"
            f"🕒 Время: {t['time']}\n"
            f"👥 Макс. мест: {t['num_of_places']}\n"
        )
        # Отправляем карточку направления с кнопкой под ней
        await message.answer(response, reply_markup=inline_kb, parse_mode="Markdown")


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


@router.message(F.text == "🎫 Купить абонемент")
async def show_membership_options(message: Message):
    """
    Ловит нажатие кнопки "🎫 Купить абонемент" в главном меню.
    Показывает список доступных абонементов в виде инлайн-кнопок.
    """
    # Создаем инлайн-клавиатуру с вариантами
    # В callback_data мы зашиваем кодовое слово и цену, чтобы бот понял, что выбрал юзер
    username = message.from_user.username

    # ПРОВЕРКА: Если абонемент уже есть — блокируем покупку

    active_m = db.membership.get_active_membership(username)
    if active_m:
        date_str = active_m['validity_date'].strftime('%d.%m.%Y')
        await message.answer(
            f"❌ У вас уже есть активный абонемент **'{active_m['type']}'**.\n"
            f"Он действует до **{date_str}**. Покупка нового заблокирована!",
            parse_mode="Markdown"
        )
        return  # Прерываем функцию, кнопки не показываем

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎫 8 занятий — 95.50 BYN",
                    callback_data="buy_m:8_lessons:95.50"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔥 Безлимит 1 месяц — 150.00 BYN",
                    callback_data="buy_m:unlimited_1m:150.00"
                )
            ]
        ]
    )

    await message.answer(
        "🏋️‍♂️ **Выберите подходящий тип абонемента:**\n\n"
        "После выбора абонемент будет автоматически привязан к вашему профилю.",
        reply_markup=inline_kb,
        parse_mode="Markdown"
    )


# Этот хэндлер поймает любое нажатие кнопки, где callback_data начинается с "buy_m:"
@router.callback_query(F.data.startswith("buy_m:"))
async def process_membership_purchase(callback: CallbackQuery):
    username = callback.from_user.username

    # Разбираем нашу секретную строчку callback_data
    # Если нажали "Безлимит", то data_parts будет ['buy_m', 'unlimited_1m', '150.00']
    data_parts = callback.data.split(":")
    m_code = data_parts[1]
    price = float(data_parts[2])

    # Переводим технический код в красивое название для базы данных
    if m_code == "8_lessons":
        m_title = "8 занятий"
    elif m_code == "unlimited_1m":
        m_title = "Безлимит 1 месяц"
    else:
        m_title = "Базовый абонемент"

    # Считаем дату окончания (сегодня + 30 дней)
    expire_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')

    # Отправляем данные в наш файл db/membership.py
    success = db.membership.create_membership(
        username=username,
        membership_type=m_title,
        price=price,
        validity_date=expire_date
    )

    # Обязательно отвечаем на callback, чтобы кнопка перестала «мигать» в Telegram
    await callback.answer()

    if success:
        # Редактируем старое сообщение с кнопками на текст успешной покупки
        await callback.message.edit_text(
            f"🎉 **Успешно оформлено!** 🎉\n\n"
            f"🎫 Абонемент: **'{m_title}'**\n"
            f"💰 Стоимость: {price} BYN\n"
            f"⏳ Действует до: {datetime.now() + timedelta(days=30):%d.%m.%Y}\n\n"
            f"Приятных тренировок! 💪",
            parse_mode="Markdown"
        )
    else:
        await callback.message.answer(
            "❌ Произошла ошибка при оформлении абонемента в базе данных."
        )


@router.callback_query(F.data.startswith("book_tr:"))
async def process_booking(callback: CallbackQuery):
    username = callback.from_user.username
    tr_type_id = int(callback.data.split(":")[1])  # Вытаскиваем ID тренировки

    # Вызываем нашу суровую функцию с проверками
    result = db.trainings.book_training(username, tr_type_id)

    await callback.answer()  # Гасим часики в телеграме

    if result == "no_membership":
        await callback.message.answer(
            "❌ **Ошибка записи:** У вас нет активного абонемента!\n"
            "Пожалуйста, сначала купите его через меню **🎫 Купить абонемент**."
        )
    elif result == "no_places":
        await callback.message.answer("❌ Извините, на это направление все места уже заняты!")
    elif result == "success":
        await callback.message.answer(
            "✅ **Успешно!** Вы записались на занятие.\n"
            "Теперь оно отображается в вашем разделе **📅 Моё Расписание**."
        )