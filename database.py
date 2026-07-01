import pymssql
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Настройки подключения берутся напрямую, без путаницы с .env
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 1433,
    'user': 'sa',
    'password': 'FitnesBotVl2026',  # Или Super_Fitnes_Bot_2026!, в зависимости от того, какой подошел в TablePlus
    'database': 'master',           # <--- МЕНЯЕМ НА master ДЛЯ ПРОВЕРКИ АВТОРИЗАЦИИ
    'autocommit': True
}

conn = None


async def init_db():
    """Инициализация подключения к MS SQL Server"""
    global conn
    try:
        conn = await asyncio.to_thread(pymssql.connect, **DB_CONFIG)
        print("[DB] Соединение с MS SQL Server успешно установлено!")
    except Exception as e:
        print(f"[ERROR] Не удалось подключиться к БД: {e}")


async def close_db():
    """Закрытие подключения"""
    global conn
    if conn:
        try:
            await asyncio.to_thread(conn.close)
            print("[DB] Соединение с MS SQL Server закрыто.")
        except Exception as e:
            print(f"[ERROR] Ошибка при закрытии БД: {e}")


async def create_empty_user(user_id: int, username: str):
    """Создает первичную запись пользователя при нажатии /start"""
    global conn
    if not conn: return

    # Используем синтаксис MERGE для MS SQL Server
    query = """
    MERGE [user] AS target
    USING (SELECT %s AS user_id) AS source
    ON (target.user_id = source.user_id)
    WHEN MATCHED THEN
        UPDATE SET user_name = %s
    WHEN NOT MATCHED THEN
        INSERT (user_id, user_name, fio, role_type)
        VALUES (source.user_id, %s, N'Заполняется', 'user');
    """

    def _execute():
        with conn.cursor() as cur:
            cur.execute(query, (user_id, username, username))
            conn.commit()

    await asyncio.to_thread(_execute)


async def update_user_profile(user_id: int, fio: str, phone: str):
    """Обновляет ФИО и телефон по завершении регистрации"""
    global conn
    if not conn: return

    query = """
    UPDATE [user] 
    SET fio = %s, phone_number = %s 
    WHERE user_id = %s;
    """

    def _execute():
        with conn.cursor() as cur:
            cur.execute(query, (fio, phone, user_id))
            conn.commit()
            print(f"[DB] Профиль пользователя {user_id} успешно обновлен!")

    await asyncio.to_thread(_execute)


async def get_schedule():
    """Получение актуального расписания тренировок (Студент В)"""
    global conn
    if not conn: return []

    # Запрос адаптирован под новые таблицы
    query = """
    SELECT 
        t.training_id, 
        u_coach.fio AS coach_name, 
        tt.type AS training_title, 
        tt.time 
    FROM training t
    JOIN [user] u_coach ON t.user_id_coach = u_coach.user_id
    JOIN training_type tt ON t.tr_type_id = tt.tr_type_id;
    """

    def _execute():
        with conn.cursor(as_dict=True) as cur:
            cur.execute(query)
            return cur.fetchall()

    return await asyncio.to_thread(_execute)