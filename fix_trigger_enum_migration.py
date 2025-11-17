#!/usr/bin/env python3
"""
Миграция для исправления значений enum TriggerEvent в базе данных
"""
import sqlite3
import os
from src.aicrm.core.config import settings

def fix_trigger_event_enum():
    """Исправляет значения enum TriggerEvent в базе данных"""

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

        # Словарь соответствия старых значений новым
        event_mapping = {
            'order_created': 'ORDER_CREATED',
            'order_status_changed': 'ORDER_STATUS_CHANGED',
            'order_completed': 'ORDER_COMPLETED',
            'payment_received': 'PAYMENT_RECEIVED',
            'task_created': 'TASK_CREATED',
            'task_status_changed': 'TASK_STATUS_CHANGED',
            'task_completed': 'TASK_COMPLETED',
            'task_assigned': 'TASK_ASSIGNED',
            'deadline_approaching': 'DEADLINE_APPROACHING',
            'production_started': 'PRODUCTION_STARTED',
            'production_step_completed': 'PRODUCTION_STEP_COMPLETED',
            'production_completed': 'PRODUCTION_COMPLETED',
            'production_overdue': 'PRODUCTION_OVERDUE',
            'print_completed': 'PRINT_COMPLETED',
            'customer_created': 'CUSTOMER_CREATED',
            'customer_updated': 'CUSTOMER_UPDATED',
            'customer_loyalty_changed': 'CUSTOMER_LOYALTY_CHANGED',
            'message_received': 'MESSAGE_RECEIVED',
            'message_sent': 'MESSAGE_SENT',
            'email_opened': 'EMAIL_OPENED',
            'manager_approval': 'MANAGER_APPROVAL',
            'design_completed': 'DESIGN_COMPLETED',
            'client_approved': 'CLIENT_APPROVED',
            'quality_approved': 'QUALITY_APPROVED',
            'designer_assigned': 'DESIGNER_ASSIGNED',
            'printing_completed': 'PRINTING_COMPLETED',
            'stage_entered': 'STAGE_ENTERED',
            'approval_granted': 'APPROVAL_GRANTED',
            'assignee_assigned': 'ASSIGNEE_ASSIGNED',
            'order_approved': 'ORDER_APPROVED',
            'customer_approved': 'CUSTOMER_APPROVED',
            'design_approved': 'DESIGN_APPROVED',
            'stage_completed': 'STAGE_COMPLETED',
            'order_updated': 'ORDER_UPDATED',
            'approval_completed': 'APPROVAL_COMPLETED',
            'avito_message_received': 'AVITO_MESSAGE_RECEIVED',
            'avito_chat_created': 'AVITO_CHAT_CREATED',
            'avito_chat_closed': 'AVITO_CHAT_CLOSED'
        }

        # Обновляем все записи в таблице triggers
        total_updated = 0
        for old_value, new_value in event_mapping.items():
            cursor.execute("""
                UPDATE triggers
                SET event_type = ?
                WHERE event_type = ?
            """, (new_value, old_value))
            updated_count = cursor.rowcount
            if updated_count > 0:
                print(f"Обновлено записей с '{old_value}' на '{new_value}': {updated_count}")
                total_updated += updated_count

        print(f"Всего обновлено записей в triggers: {total_updated}")

        # Проверяем, есть ли другие проблемные значения
        cursor.execute("""
            SELECT DISTINCT event_type
            FROM triggers
            WHERE event_type NOT IN (
                'ORDER_CREATED', 'ORDER_STATUS_CHANGED', 'ORDER_COMPLETED', 'PAYMENT_RECEIVED',
                'TASK_CREATED', 'TASK_STATUS_CHANGED', 'TASK_COMPLETED', 'TASK_ASSIGNED', 'DEADLINE_APPROACHING',
                'PRODUCTION_STARTED', 'PRODUCTION_STEP_COMPLETED', 'PRODUCTION_COMPLETED', 'PRODUCTION_OVERDUE', 'PRINT_COMPLETED',
                'CUSTOMER_CREATED', 'CUSTOMER_UPDATED', 'CUSTOMER_LOYALTY_CHANGED',
                'MESSAGE_RECEIVED', 'MESSAGE_SENT', 'EMAIL_OPENED',
                'MANAGER_APPROVAL', 'DESIGN_COMPLETED', 'CLIENT_APPROVED', 'QUALITY_APPROVED',
                'DESIGNER_ASSIGNED', 'PRINTING_COMPLETED', 'STAGE_ENTERED', 'APPROVAL_GRANTED', 'ASSIGNEE_ASSIGNED', 'ORDER_APPROVED',
                'CUSTOMER_APPROVED', 'DESIGN_APPROVED', 'STAGE_COMPLETED', 'ORDER_UPDATED', 'APPROVAL_COMPLETED',
                'AVITO_MESSAGE_RECEIVED', 'AVITO_CHAT_CREATED', 'AVITO_CHAT_CLOSED'
            )
        """)

        problematic_values = cursor.fetchall()

        if problematic_values:
            print("Найдены проблемные значения в triggers:")
            for row in problematic_values:
                print(f"  - {row[0]}")
        else:
            print("Все значения в triggers корректны")

        conn.commit()
        print("Миграция завершена успешно")

    except Exception as e:
        print(f"Ошибка при выполнении миграции: {e}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    fix_trigger_event_enum()
