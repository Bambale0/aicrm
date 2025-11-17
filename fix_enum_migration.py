#!/usr/bin/env python3
"""
Миграция для исправления значений enum RobotAction в базе данных
"""
import sqlite3
import os
from src.aicrm.core.config import settings

def fix_robot_action_enum():
    """Исправляет значения enum RobotAction в базе данных"""

    # Получаем путь к базе данных из URL
    database_url = settings.database_url
    if database_url.startswith('sqlite+aiosqlite:///'):
        db_path = database_url.replace('sqlite+aiosqlite:///', '')
    elif database_url.startswith('sqlite:///'):
        db_path = database_url.replace('sqlite:///', '')
    else:
        # Для других типов баз данных используем другой подход
        print(f"Неподдерживаемый тип базы данных: {database_url}")
        return

    # Если путь относительный, делаем его абсолютным
    if not os.path.isabs(db_path):
        db_path = os.path.join(os.getcwd(), db_path)

    print(f"Подключаемся к базе данных: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Обновляем все записи с 'create_task' на 'CREATE_TASK'
        cursor.execute("""
            UPDATE robot_actions_config
            SET action_type = 'CREATE_TASK'
            WHERE action_type = 'create_task'
        """)
        print(f"Обновлено записей в robot_actions_config: {cursor.rowcount}")

        # Обновляем записи в таблице automation_errors
        cursor.execute("""
            UPDATE automation_errors
            SET action_type = 'CREATE_TASK'
            WHERE action_type = 'create_task'
        """)
        print(f"Обновлено записей в automation_errors: {cursor.rowcount}")

        # Проверяем, есть ли другие проблемные значения
        cursor.execute("""
            SELECT DISTINCT action_type
            FROM robot_actions_config
            WHERE action_type NOT IN (
                'send_email', 'send_sms', 'send_telegram', 'create_message',
                'CREATE_TASK', 'update_task_status', 'create_production_step',
                'update_order_status', 'notify_user', 'notify_group',
                'update_field', 'create_communication', 'analyze_intent',
                'generate_response', 'generate_ai_response', 'send_standard_response',
                'escalate_complex_query', 'call_external_api', 'call_webhook',
                'call_graphql', 'call_soap', 'create_calendar_event',
                'update_calendar_event', 'send_calendar_invite'
            )
        """)

        problematic_values = cursor.fetchall()

        if problematic_values:
            print("Найдены проблемные значения в robot_actions_config:")
            for row in problematic_values:
                print(f"  - {row[0]}")
        else:
            print("Все значения в robot_actions_config корректны")

        # Проверяем automation_errors
        cursor.execute("""
            SELECT DISTINCT action_type
            FROM automation_errors
            WHERE action_type IS NOT NULL
              AND action_type NOT IN (
                'send_email', 'send_sms', 'send_telegram', 'create_message',
                'CREATE_TASK', 'update_task_status', 'create_production_step',
                'update_order_status', 'notify_user', 'notify_group',
                'update_field', 'create_communication', 'analyze_intent',
                'generate_response', 'generate_ai_response', 'send_standard_response',
                'escalate_complex_query', 'call_external_api', 'call_webhook',
                'call_graphql', 'call_soap', 'create_calendar_event',
                'update_calendar_event', 'send_calendar_invite'
            )
        """)

        problematic_values = cursor.fetchall()

        if problematic_values:
            print("Найдены проблемные значения в automation_errors:")
            for row in problematic_values:
                print(f"  - {row[0]}")
        else:
            print("Все значения в automation_errors корректны")

        conn.commit()
        print("Миграция завершена успешно")

    except Exception as e:
        print(f"Ошибка при выполнении миграции: {e}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    fix_robot_action_enum()
