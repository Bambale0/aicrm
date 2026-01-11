#!/usr/bin/env python3
"""
Скрипт для миграции Pydantic схем с V1 на V2
"""
import re
from pathlib import Path


def migrate_config_blocks(content):
    """Мигрирует блоки class Config на model_config = ConfigDict(...)"""

    # Шаблон для поиска блоков class Config с json_schema_extra
    config_pattern = r"(\s+)class Config:\s*\n(?:\s+)(.*?)(?=\n\n|\n\s*class|\n\s*@|\Z)"

    def replace_config(match):
        indent = match.group(1)
        config_content = match.group(2)

        # Разбираем содержимое Config
        lines = config_content.strip().split("\n")
        config_dict_items = []

        for line in lines:
            line = line.strip()
            if line.startswith("json_schema_extra = {"):
                # Это многострочный json_schema_extra
                # Найдем закрывающую скобку
                json_start = content.find("json_schema_extra = {", match.start())
                brace_count = 0
                json_end = json_start
                for i, char in enumerate(content[json_start:], json_start):
                    if char == "{":
                        brace_count += 1
                    elif char == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i + 1
                            break

                json_content = content[json_start:json_end]
                config_dict_items.append(f"json_schema_extra={json_content}")
                break
            elif "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                config_dict_items.append(f"{key.strip()}={value.strip()}")

        if config_dict_items:
            config_dict = ", ".join(config_dict_items)
            return f"{indent}model_config = ConfigDict({config_dict})"
        else:
            return f"{indent}model_config = ConfigDict()"

    # Заменяем все блоки
    result = re.sub(config_pattern, replace_config, content, flags=re.DOTALL)

    # Очищаем дубликаты json_schema_extra если они остались
    result = re.sub(r"(\s+)json_schema_extra = ({.*?});", "", result, flags=re.DOTALL)

    return result


def main():
    """Основная функция миграции"""
    schemas_dir = Path("src/aicrm/api/schemas")

    for py_file in schemas_dir.glob("*.py"):
        print(f"Обработка {py_file}")

        with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Проверяем, есть ли class Config блоки
        if "class Config:" in content:
            migrated_content = migrate_config_blocks(content)

            with open(py_file, "w", encoding="utf-8") as f:
                f.write(migrated_content)

            print(f"✅ Миграция завершена для {py_file}")
        else:
            print(f"⏭️  Пропуск {py_file} - нет блоков Config")


if __name__ == "__main__":
    main()
