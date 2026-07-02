# db/base.py
import pyodbc
from config import CONN_STR

def get_connection():
    """Создает и возвращает подключение к MS SQL Server."""
    return pyodbc.connect(CONN_STR)