import pyodbc
from db.base import get_connection

def get_all() -> list:
    """
    READ: Получение всех доступных направлений клуба для справочника.
    """
    query = "SELECT tr_type_id, type, time, num_of_places FROM training_type"
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                results = []
                for row in cursor.fetchall():
                    # Переводим время в строку формата ЧЧ:ММ
                    time_str = str(row[2])[:5]
                    results.append({
                        "tr_type_id": row[0],
                        "type": row[1],
                        "time": time_str,
                        "num_of_places": row[3]
                    })
                return results
    except pyodbc.Error as e:
        print(f"[DB/TrainingTypes] Ошибка чтения направлений: {e}")
        return []