import aiomysql
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv("DB_HOST", "127.0.0.1"),
    'port': int(os.getenv("DB_PORT", 3306)),
    'user': os.getenv("DB_USER", "root"),
    'password': os.getenv("DB_PASSWORD", ""),
    'db': os.getenv("DB_NAME", "fitness_bot_db"),
    'autocommit': True
}

pool = None

async def init_db():
    """Инициализация пула подключений к MySQL"""
    global pool
    try:
        pool = await aiomysql.create_pool(**DB_CONFIG)
        print(" [DB] Пул соединений с MySQL успешно запущен!")
    except Exception as e:
        print(f" [ERROR] Не удалось подключиться к БД: {e}")


async def close_db():
    """Закрытие пула при остановке бота"""
    if pool:
        pool.close()
        await pool.wait_closed()
        print(" [DB] Пул соединений с MySQL закрыт.")


# --- СТУДЕНТ А: Пошаговое сохранение профиля ---

async def create_empty_user(user_id: int, username: str):
    """Создает первичную запись пользователя (только ID и ник), если его еще нет"""
    if not pool: return
    query = """
    INSERT INTO user (user_id, user_name, fio, role_type) 
    VALUES (%s, %s, 'Заполняется', 'user')
    ON DUPLICATE KEY UPDATE user_name=%s;
    """
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, (user_id, username, username))


async def update_user_profile(user_id: int, fio: str, phone: str):
    """Обновляет ФИО и телефон у уже созданного пользователя"""
    if not pool: return
    query = """
    UPDATE user 
    SET fio = %s, phone_number = %s 
    WHERE user_id = %s;
    """
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, (fio, phone, user_id))
            print(f" [DB] Профиль пользователя {user_id} успешно обновлен!")


# --- СТУДЕНТ В: Расписание ---
async def get_schedule():
    """Получение актуального расписания тренировок"""
    if not pool: return []
    query = """
    SELECT t.training_id, u_coach.fio AS coach_name, tt.type AS training_title, tt.time 
    FROM training t
    JOIN user u_coach ON t.user_id_coach = u_coach.user_id
    JOIN training_type tt ON t.tr_type_id = tt.tr_type_id;
    """
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(query)
            return await cur.fetchall()