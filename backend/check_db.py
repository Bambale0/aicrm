#!/usr/bin/env python3
"""
Проверка содержимого базы данных
"""
import sqlite3
import os

def check_database():
    """Проверяет содержимое базы данных"""

    db_path = "./test.db"

    if not os.path.isabs(db_path):
        db_path = os.path.join(os.getcwd(), db_path)

    print(f"Подключаемся к базе данных: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Проверяем таблицу triggers
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='triggers';")
        if cursor.fetchone():
            print("Таблица triggers существует")

            # Проверяем содержимое
            cursor.execute("SELECT event_type, COUNT(*) FROM triggers GROUP BY event_type;")
            results = cursor.fetchall()

            print("Содержимое таблицы triggers:")
            for event_type, count in results:
                print(f"  {event_type}: {count} записей")
        else:
            print("Таблица triggers не существует")

        # Проверяем таблицу robot_actions_config
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='robot_actions_config';")
        if cursor.fetchone():
            print("Таблица robot_actions_config существует")

            cursor.execute("SELECT action_type, COUNT(*) FROM robot_actions_config GROUP BY action_type;")
            results = cursor.fetchall()

            print("Содержимое таблицы robot_actions_config:")
            for action_type, count in results:
                print(f"  {action_type}: {count} записей")
        else:
            print("Таблица robot_actions_config не существует")

    except Exception as e:
        print(f"Ошибка при проверке базы данных: {e}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_database()
