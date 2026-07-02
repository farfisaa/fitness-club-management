# db/trainings.py
import pyodbc
from db.base import get_connection


def get_client_schedule(username: str) -> list:
    """
    JOIN-READ: Получение расписания тренировок для конкретного клиента по его user_name.
    Связываем 5 таблиц строго по твоей схеме.
    """
    query = """
        SELECT 
            t.training_id,
            tt.type AS training_name,
            tt.time AS training_time,
            t.day_of_the_week,
            u_coach.fio AS coach_fio
        FROM [training] t
        JOIN [training_type] tt ON t.tr_type_id = tt.tr_type_id
        JOIN [membership] m ON t.membership_id_client = m.membership_id
        JOIN [user] u_client ON m.user_id = u_client.user_id
        JOIN [user] u_coach ON t.user_id_coach = u_coach.user_id
        WHERE u_client.user_name = ?
        ORDER BY t.day_of_the_week ASC
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (username,))

                # Массив дней недели для красивого вывода человеком
                days = {1: "Понедельник", 2: "Вторник", 3: "Среда", 4: "Четверг", 5: "Пятница", 6: "Суббота",
                        7: "Воскресенье"}

                results = []
                for row in cursor.fetchall():
                    # Форматируем время, убирая лишние микросекунды, если они прилетят из MSSQL
                    time_str = str(row[2])[:5]
                    results.append({
                        "training_id": row[0],
                        "training_name": row[1],
                        "time": time_str,
                        "day_of_the_week": days.get(row[3], "Неизвестный день"),
                        "coach_fio": row[4]
                    })
                return results
    except pyodbc.Error as e:
        print(f"[DB/Trainings] Ошибка чтения расписания: {e}")
        return []


def delete_by_id(training_id: int) -> bool:
    """
    DELETE: Удаление тренировки по её PRIMARY KEY (training_id).
    """
    query = "DELETE FROM [training] WHERE training_id = ?"
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (training_id,))
                conn.commit()
                return cursor.rowcount > 0
    except pyodbc.Error as e:
        print(f"[DB/Trainings] Ошибка удаления тренировки: {e}")
        return False