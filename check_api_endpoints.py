#!/usr/bin/env python3
"""
Скрипт для проверки работоспособности всех API эндпоинтов.
Выполняет авторизацию и проверяет каждый эндпоинт на наличие серверных ошибок.
"""

import json
import logging
import sys
from typing import Dict, List, Optional

import requests
from requests.exceptions import RequestException

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("api_check.log"), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class APIEndpointChecker:
    """Класс для проверки API эндпоинтов"""

    def __init__(self, base_url: str = "https://dev.chillcreative.ru"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.token: Optional[str] = None

    def authenticate(self, email: str, password: str) -> bool:
        """Авторизация и получение токена"""
        try:
            login_url = f"{self.base_url}/auth/login/json"
            login_data = {"email": email, "password": password}

            logger.info(f"Авторизация пользователя: {email}")
            response = self.session.post(login_url, json=login_data)

            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                if self.token:
                    self.session.headers.update(
                        {"Authorization": f"Bearer {self.token}"}
                    )
                    logger.info("Авторизация успешна")
                    return True
                else:
                    logger.error("Токен не найден в ответе")
                    return False
            else:
                logger.error(
                    f"Ошибка авторизации: {response.status_code} - {response.text}"
                )
                return False

        except RequestException as e:
            logger.error(f"Ошибка сети при авторизации: {e}")
            return False

    def get_openapi_schema(self) -> Optional[Dict]:
        """Получение OpenAPI схемы"""
        try:
            schema_url = f"{self.base_url}/openapi.json"
            logger.info(f"Получение OpenAPI схемы: {schema_url}")
            response = self.session.get(schema_url)

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Ошибка получения схемы: {response.status_code}")
                return None

        except RequestException as e:
            logger.error(f"Ошибка сети при получении схемы: {e}")
            return None

    def extract_endpoints(self, schema: Dict) -> List[Dict]:
        """Извлечение списка эндпоинтов из OpenAPI схемы"""
        endpoints = []

        if "paths" not in schema:
            logger.error("Схема не содержит paths")
            return endpoints

        for path, methods in schema["paths"].items():
            for method, details in methods.items():
                if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    endpoints.append(
                        {
                            "path": path,
                            "method": method.upper(),
                            "summary": details.get("summary", ""),
                            "description": details.get("description", ""),
                            "parameters": details.get("parameters", []),
                            "requestBody": details.get("requestBody", None),
                        }
                    )

        logger.info(f"Найдено {len(endpoints)} эндпоинтов")
        return endpoints

    def check_endpoint(self, endpoint: Dict) -> Dict:
        """Проверка одного эндпоинта"""
        url = f"{self.base_url}{endpoint['path']}"
        method = endpoint["method"]

        # Пропускаем эндпоинты авторизации, так как уже авторизованы
        if "/auth/" in endpoint["path"] and method in ["POST", "PUT"]:
            return {
                "path": endpoint["path"],
                "method": method,
                "status": "skipped",
                "reason": "auth endpoint",
            }

        try:
            # Для простоты проверки используем только GET для всех методов
            # В реальности для POST/PUT может понадобиться тело запроса
            if method in ["POST", "PUT", "PATCH"]:
                # Пробуем с пустым телом
                response = self.session.request(method, url, json={})
            else:
                response = self.session.get(url)

            result = {
                "path": endpoint["path"],
                "method": method,
                "status_code": response.status_code,
                "status": "success" if response.status_code < 500 else "error",
                "response_time": response.elapsed.total_seconds(),
                "content_length": len(response.content),
            }

            if response.status_code >= 500:
                result["error"] = response.text[:200]  # Ограничим длину ошибки
                logger.warning(
                    f"Серверная ошибка на {method} {endpoint['path']}: {response.status_code}"
                )

            return result

        except RequestException as e:
            logger.error(f"Ошибка сети при проверке {method} {endpoint['path']}: {e}")
            return {
                "path": endpoint["path"],
                "method": method,
                "status": "network_error",
                "error": str(e),
            }

    def check_all_endpoints(self, schema: Dict) -> Dict:
        """Проверка всех эндпоинтов"""
        endpoints = self.extract_endpoints(schema)
        results = []

        logger.info(f"Начинаем проверку {len(endpoints)} эндпоинтов")

        for i, endpoint in enumerate(endpoints, 1):
            logger.info(
                f"Проверка {i}/{len(endpoints)}: {endpoint['method']} {endpoint['path']}"
            )
            result = self.check_endpoint(endpoint)
            results.append(result)

        # Статистика
        total = len(results)
        successful = len([r for r in results if r.get("status") == "success"])
        errors = len([r for r in results if r.get("status") == "error"])
        network_errors = len([r for r in results if r.get("status") == "network_error"])
        skipped = len([r for r in results if r.get("status") == "skipped"])

        stats = {
            "total": total,
            "successful": successful,
            "errors": errors,
            "network_errors": network_errors,
            "skipped": skipped,
            "success_rate": successful / total * 100 if total > 0 else 0,
        }

        logger.info(f"Проверка завершена. Статистика: {stats}")

        return {"stats": stats, "results": results}

    def run_check(self, email: str, password: str) -> Optional[Dict]:
        """Основной метод запуска проверки"""
        logger.info("Начинаем проверку API эндпоинтов")

        # Авторизация
        if not self.authenticate(email, password):
            logger.error("Не удалось авторизоваться")
            return None

        # Получение схемы
        schema = self.get_openapi_schema()
        if not schema:
            logger.error("Не удалось получить OpenAPI схему")
            return None

        # Проверка эндпоинтов
        return self.check_all_endpoints(schema)


def main():
    """Основная функция"""
    import argparse

    parser = argparse.ArgumentParser(description="Проверка API эндпоинтов")
    parser.add_argument(
        "--url", default="https://dev.chillcreative.ru/api", help="Базовый URL API"
    )
    parser.add_argument("--email", help="Email для авторизации")
    parser.add_argument("--password", help="Пароль для авторизации")
    parser.add_argument(
        "--use-dev-admin",
        action="store_true",
        help="Использовать credentials dev админа",
    )
    parser.add_argument(
        "--output",
        default="api_check_results.json",
        help="Файл для сохранения результатов",
    )

    args = parser.parse_args()

    # Если указан флаг --use-dev-admin, используем дефолтные credentials
    if args.use_dev_admin:
        email = "iloveigor@chillcreative.ru"
        password = "25896311Aaa"
        logger.info("Используем credentials dev админа")
    else:
        if not args.email or not args.password:
            parser.error(
                "--email и --password обязательны, если не используется --use-dev-admin"
            )
        email = args.email
        password = args.password

    checker = APIEndpointChecker(args.url)
    results = checker.run_check(email, password)

    if results:
        # Сохранение результатов
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        logger.info(f"Результаты сохранены в {args.output}")

        # Вывод статистики
        stats = results["stats"]
        print("\n" + "=" * 50)
        print("СТАТИСТИКА ПРОВЕРКИ API:")
        print(f"Всего эндпоинтов: {stats['total']}")
        print(f"Успешных: {stats['successful']}")
        print(f"Ошибок сервера: {stats['errors']}")
        print(f"Ошибок сети: {stats['network_errors']}")
        print(f"Пропущено: {stats['skipped']}")
        print(".1f")
        print("=" * 50)

        # Вывод ошибок
        if stats["errors"] > 0 or stats["network_errors"] > 0:
            print("\nОШИБКИ:")
            for result in results["results"]:
                if result.get("status") in ["error", "network_error"]:
                    print(
                        f"- {result['method']} {result['path']}: {result.get('status_code', 'N/A')} - {result.get('error', 'Unknown error')}"
                    )

    else:
        logger.error("Проверка не удалась")
        sys.exit(1)


if __name__ == "__main__":
    main()
