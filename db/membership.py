import pyodbc
from db.base import get_connection

def create_membership(username: str, membership_type: str, price: float, validity_date: str) -> bool:
    """
    CREATE: Оформление нового абонемента для клиента по его @username.
    """
    query = """
        INSERT INTO membership (user_id, type, price, validity_date)
        VALUES (
            (SELECT user_id FROM [user] WHERE user_name = ?),
            ?, ?, ?
        )
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (username, membership_type, price, validity_date))
                conn.commit()
                return True
    except pyodbc.Error as e:
        print(f"[DB/Membership] Ошибка создания абонемента: {e}")
        return False

def get_active_membership(username: str) -> dict or None:
    """
    Проверяет, есть ли у пользователя активный абонемент.
    Активным считается тот, у которого дата окончания больше или равна сегодняшней.
    """
    query = """
        SELECT type, validity_date 
        FROM membership 
        WHERE user_id = (SELECT user_id FROM [user] WHERE user_name = ?)
          AND validity_date >= CAST(GETDATE() AS DATE)
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (username,))
                row = cursor.fetchone()
                if row:
                    return {"type": row[0], "validity_date": row[1]}
                return None
    except pyodbc.Error as e:
        print(f"[DB/Membership] Ошибка проверки абонемента: {e}")
        return None