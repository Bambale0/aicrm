#!/usr/bin/env python3
"""
Скрипт для самостоятельной проверки корректности настройки роутеров

Проверяет:
1. Корректность импорта FastAPI приложения
2. Наличие всех необходимых роутеров
3. Генерацию OpenAPI схемы
4. Доступность ключевых эндпоинтов
5. Корректность префиксов роутеров
"""

import sys
import requests
import time
from typing import Dict, List, Tuple

def check_app_import():
    """Проверка импорта FastAPI приложения"""
    print("🔍 Проверка импорта FastAPI приложения...")
    try:
        from src.aicrm.main import app
        print("✅ FastAPI приложение успешно импортировано")
        return True, app
    except Exception as e:
        print(f"❌ Ошибка импорта FastAPI приложения: {e}")
        return False, None

def check_openapi_generation(app):
    """Проверка генерации OpenAPI схемы"""
    print("🔍 Проверка генерации OpenAPI схемы...")
    try:
        schema = app.openapi()
        paths_count = len(schema.get('paths', {}))
        print(f"✅ OpenAPI схема сгенерирована успешно: {paths_count} путей")
        return True, paths_count
    except Exception as e:
        print(f"❌ Ошибка генерации OpenAPI схемы: {e}")
        return False, 0

def check_router_prefixes(app):
    """Проверка корректности префиксов роутеров"""
    print("🔍 Проверка префиксов роутеров...")
    try:
        schema = app.openapi()
        paths = schema.get('paths', {})

        expected_prefixes = {
            '/customers/': 'customers',
            '/tasks/': 'tasks',
            '/communications/': 'communications',
            '/orders/': 'orders',
            '/production/': 'production',
            '/automation/': 'automation',
            '/telegram/': 'telegram',
            '/avito/': 'avito',
            '/campaigns/': 'campaigns',
            '/organizations/': 'organizations',
            '/plugins/': 'plugins',
            '/email-templates/': 'email-templates',
            '/catalog/': 'catalog',
            '/settings/': 'system-settings',
            '/ai/': 'ai',
            '/ai-manager/': 'ai-manager',
            '/ai-settings/': 'ai-settings',
            '/email/': 'email',
            '/workflow/': 'workflow'
        }

        found_prefixes = {}
        for path in paths.keys():
            for prefix, tag in expected_prefixes.items():
                if path.startswith(prefix):
                    if tag not in found_prefixes:
                        found_prefixes[tag] = []
                    found_prefixes[tag].append(path)

        print(f"✅ Найдено {len(found_prefixes)} групп роутеров с правильными префиксами")

        # Проверка основных роутеров
        required_routers = ['customers', 'tasks', 'communications', 'orders', 'automation', 'telegram']
        missing_routers = []

        for router in required_routers:
            if router not in found_prefixes:
                missing_routers.append(router)

        if missing_routers:
            print(f"❌ Отсутствуют роутеры: {missing_routers}")
            return False, found_prefixes

        print("✅ Все основные роутеры присутствуют")
        return True, found_prefixes

    except Exception as e:
        print(f"❌ Ошибка проверки префиксов роутеров: {e}")
        return False, {}

def check_basic_endpoints(base_url: str = "http://localhost:8000"):
    """Проверка доступности базовых эндпоинтов"""
    print(f"🔍 Проверка доступности эндпоинтов на {base_url}...")

    test_endpoints = [
        ("GET", "/health"),
        ("GET", "/api/health"),
        ("GET", "/ping"),
        ("GET", "/customers/customers/"),
        ("GET", "/tasks/tasks/"),
        ("GET", "/communications/communications/"),
        ("GET", "/automation/automation/processes"),
        ("GET", "/telegram/telegram/settings"),
    ]

    results = []

    for method, endpoint in test_endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
                # Для защищенных эндпоинтов ожидаем 401, для публичных - 200
                if endpoint in ["/health", "/api/health", "/ping"]:
                    expected_codes = [200]
                else:
                    expected_codes = [200, 401, 403]  # Могут требовать аутентификации

                if response.status_code in expected_codes:
                    results.append((endpoint, "✅", response.status_code))
                else:
                    results.append((endpoint, "⚠️", response.status_code))
            else:
                results.append((endpoint, "⏭️", "не проверяется"))
        except requests.exceptions.ConnectionError:
            results.append((endpoint, "❌", "нет соединения"))
        except requests.exceptions.Timeout:
            results.append((endpoint, "⏳", "таймаут"))
        except Exception as e:
            results.append((endpoint, "❌", str(e)))

    # Вывод результатов
    for endpoint, status, detail in results:
        print(f"   {status} {endpoint}: {detail}")

    # Проверка общего результата
    success_count = sum(1 for _, status, _ in results if status == "✅")
    total_count = len([r for r in results if r[2] != "не проверяется"])

    if success_count == total_count:
        print("✅ Все проверенные эндпоинты доступны")
        return True
    else:
        print(f"⚠️ Доступно {success_count}/{total_count} эндпоинтов")
        return success_count > 0

def run_server_check():
    """Запуск комплексной проверки"""
    print("🚀 Запуск проверки настройки роутеров...\n")

    # 1. Проверка импорта
    import_success, app = check_app_import()
    if not import_success:
        print("\n❌ Критическая ошибка: невозможно импортировать приложение")
        return False

    print()

    # 2. Проверка OpenAPI
    openapi_success, paths_count = check_openapi_generation(app)
    if not openapi_success:
        print("\n❌ Критическая ошибка: невозможно сгенерировать OpenAPI схему")
        return False

    print()

    # 3. Проверка префиксов
    prefixes_success, found_prefixes = check_router_prefixes(app)
    if not prefixes_success:
        print("\n⚠️ Предупреждение: некоторые роутеры могут отсутствовать")
    else:
        print()

    # 4. Проверка доступности эндпоинтов
    print("💡 Для полной проверки запустите сервер и проверьте доступность эндпоинтов")
    print("   Команда для запуска сервера:")
    print("   cd /home/dev/aicrm/backend/aicrm && python3 -m uvicorn src.aicrm.main:app --host 0.0.0.0 --port 8000")
    print()

    endpoints_success = check_basic_endpoints()

    # Итоговый отчет
    print("\n" + "="*60)
    print("📊 ИТОГОВЫЙ ОТЧЕТ ПРОВЕРКИ")
    print("="*60)

    checks = [
        ("Импорт FastAPI приложения", import_success),
        ("Генерация OpenAPI схемы", openapi_success),
        ("Проверка префиксов роутеров", prefixes_success),
        ("Доступность эндпоинтов", endpoints_success),
    ]

    all_passed = True
    for check_name, passed in checks:
        status = "✅ ПРОЙДЕНО" if passed else "❌ ПРОВАЛЕНО"
        print(f"{status}: {check_name}")
        if not passed:
            all_passed = False

    print(f"\n🔢 Найдено эндпоинтов: {paths_count}")
    print(f"🔗 Групп роутеров: {len(found_prefixes)}")

    if all_passed:
        print("\n🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ! Роутеры настроены корректно.")
        return True
    else:
        print("\n⚠️ НЕКОТОРЫЕ ПРОВЕРКИ ПРОВАЛЕНЫ. Проверьте конфигурацию.")
        return False

def main():
    """Основная функция"""
    try:
        success = run_server_check()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Проверка прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()