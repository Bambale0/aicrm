"""
Запуск всех тестов проекта AI CRM
"""

import os
import sys
from pathlib import Path

import pytest

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def run_all_tests():
    """Запуск всех тестов проекта"""
    print("🚀 Запуск всех тестов проекта AI CRM")
    print("=" * 50)

    # Опции pytest
    pytest_args = [
        "--verbose",
        "--tb=short",
        "--strict-markers",
        "--asyncio-mode=auto",
        "--cov=backend/src/aicrm",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-fail-under=80",
        "backend/src/aicrm/tests/",
    ]

    # Запуск тестов
    exit_code = pytest.main(pytest_args)

    if exit_code == 0:
        print("\n✅ Все тесты пройдены успешно!")
        print("📊 Отчет о покрытии: htmlcov/index.html")
    else:
        print(f"\n❌ Некоторые тесты провалились (код выхода: {exit_code})")
        print("📊 Проверьте отчет о покрытии для деталей")

    return exit_code


def run_unit_tests():
    """Запуск только unit тестов"""
    print("🧪 Запуск unit тестов")
    print("-" * 30)

    pytest_args = [
        "-m",
        "not integration",
        "--verbose",
        "--tb=short",
        "backend/src/aicrm/tests/",
    ]

    return pytest.main(pytest_args)


def run_integration_tests():
    """Запуск только интеграционных тестов"""
    print("🔗 Запуск интеграционных тестов")
    print("-" * 35)

    pytest_args = [
        "-m",
        "integration",
        "--verbose",
        "--tb=short",
        "backend/src/aicrm/tests/",
    ]

    return pytest.main(pytest_args)


def run_specific_test(test_file):
    """Запуск конкретного тестового файла"""
    print(f"🎯 Запуск тестов из файла: {test_file}")
    print("-" * 40)

    test_path = f"backend/src/aicrm/tests/{test_file}"
    if not os.path.exists(test_path):
        print(f"❌ Файл {test_path} не найден")
        return 1

    pytest_args = ["--verbose", "--tb=short", test_path]

    return pytest.main(pytest_args)


def run_with_coverage():
    """Запуск тестов с подробным отчетом о покрытии"""
    print("📊 Запуск тестов с анализом покрытия")
    print("-" * 40)

    pytest_args = [
        "--cov=backend/src/aicrm",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-report=xml",
        "--verbose",
        "--tb=short",
        "backend/src/aicrm/tests/",
    ]

    exit_code = pytest.main(pytest_args)

    if exit_code == 0:
        print("\n📈 Подробный отчет о покрытии сохранен в:")
        print("   - HTML: htmlcov/index.html")
        print("   - XML: coverage.xml")

    return exit_code


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "unit":
            exit_code = run_unit_tests()
        elif command == "integration":
            exit_code = run_integration_tests()
        elif command == "coverage":
            exit_code = run_with_coverage()
        elif command.startswith("test_"):
            exit_code = run_specific_test(command)
        else:
            print("Использование:")
            print("  python test_runner.py              # Все тесты")
            print("  python test_runner.py unit         # Только unit тесты")
            print("  python test_runner.py integration  # Только интеграционные тесты")
            print("  python test_runner.py coverage     # С анализом покрытия")
            print("  python test_runner.py test_file.py # Конкретный файл")
            exit_code = 1
    else:
        exit_code = run_all_tests()

    sys.exit(exit_code)
