# db/users.py
import pyodbc
from db.base import get_connection

def register(telegram_id: int, username: str, full_name: str) -> bool:
    """
    CREATE: Регистрация нового пользователя.
    Так как у тебя первичный ключ user_id INT IDENTITY, мы привязываем Telegram-сессию
    к текстовому полю user_name (сохраняем туда username из телеграма).
    """
    query = """
        IF NOT EXISTS (SELECT 1 FROM [user] WHERE user_name = ?)
        BEGIN
            INSERT INTO [user] (fio, user_name, phone_number, role_type)
            VALUES (?, ?, NULL, 'user');
        END
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (username, full_name, username))
                conn.commit()
                return True
    except pyodbc.Error as e:
        print(f"[DB/Users] Ошибка регистрации: {e}")
        return False

def get_profile(username: str) -> dict | None:
    """
    READ: Получение профиля по user_name.
    Дополнительно подтягиваем информацию об абонементе (membership) через LEFT JOIN.
    """
    query = """
        SELECT 
            u.fio, 
            u.user_name, 
            u.role_type, 
            m.type AS membership_type, 
            m.validity_date
        FROM [user] u
        LEFT JOIN [membership] m ON u.user_id = m.user_id
        WHERE u.user_name = ?
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (username,))
                row = cursor.fetchone()
                if row:
                    return {
                        "fio": row[0],
                        "user_name": row[1],
                        "role_type": row[2],
                        "membership_type": row[3] or "Отсутствует",
                        "validity_date": row[4].strftime('%d.%m.%Y') if row[4] else "—"
                    }
                return None
    except pyodbc.Error as e:
        print(f"[DB/Users] Ошибка чтения профиля: {e}")
        return None