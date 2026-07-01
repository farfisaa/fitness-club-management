import pyodbc

# СТРОКА ПОДКЛЮЧЕНИЯ ДЛЯ ВАШЕГО СЛУЧАЯ!
conn_str = (
    "DRIVER={SQL Server};"
    "SERVER=(local);"  # ← Имя сервера
    "DATABASE=ProjectDB;"  # ← Имя вашей БД (поменяйте, если другое)
    "Trusted_Connection=yes;"  # ← Windows-аутентификация
)

try:
    # Подключаемся
    conn = pyodbc.connect(conn_str)
    print(" ПОДКЛЮЧЕНИЕ К БД УСПЕШНО!")

    # Проверяем, какие таблицы есть
    cursor = conn.cursor()
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'")
    tables = cursor.fetchall()

    print("\n СПИСОК ТАБЛИЦ В БД:")
    if tables:
        for table in tables:
            print(f"  - {table[0]}")
    else:
        print("  (таблиц нет)")

    cursor.close()
    conn.close()

except Exception as e:
    print(f" ОШИБКА ПОДКЛЮЧЕНИЯ: {e}")
    print("\n ВОЗМОЖНЫЕ ПРИЧИНЫ:")
    print("1. База данных 'FitnesDB' не существует")
    print("2. SQL Server не запущен")
    print("3. Неправильное имя сервера")