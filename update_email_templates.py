#!/usr/bin/env python3
"""
Скрипт для обновления существующих email шаблонов с исправленными CSS стилями
"""
import os
import sqlite3


def update_templates():
    """Обновление шаблонов с исправленными CSS стилями"""
    # Путь к базе данных из .env файла
    db_path = os.path.join(os.path.dirname(__file__), "test.db")

    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Получаем все шаблоны
        cursor.execute("SELECT id, html_template FROM email_templates")
        templates = cursor.fetchall()

        print(f"Найдено {len(templates)} шаблонов для обновления")

        updated_count = 0
        for template_id, html_template in templates:
            if html_template and "<style>" in html_template:
                # Удаляем CSS стили полностью, чтобы избежать конфликтов с переменными
                import re

                # Удаляем все содержимое между <style> и </style>
                updated_html = re.sub(
                    r"<style>.*?</style>", "", html_template, flags=re.DOTALL
                )

                # Обновляем шаблон в базе данных
                cursor.execute(
                    "UPDATE email_templates SET html_template = ? WHERE id = ?",
                    (updated_html, template_id),
                )

                print(f"✅ Удалены CSS стили из шаблона ID {template_id}")
                updated_count += 1

        conn.commit()
        print(f"🎉 Успешно обновлено {updated_count} шаблонов!")

    except Exception as e:
        print(f"❌ Ошибка обновления шаблонов: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    update_templates()
