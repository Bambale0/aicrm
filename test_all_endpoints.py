#!/usr/bin/env python3
"""
Тестирование всех API эндпоинтов
"""

import json
import sys
from typing import Dict, List, Optional

import requests


class EndpointTester:
    def __init__(
        self, base_url: str = "http://127.0.0.1:8000", token: Optional[str] = None
    ):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})

    def test_endpoint(self, endpoint: Dict) -> Dict:
        """Тестирование одного эндпоинта"""
        path = endpoint["path"]
        method = endpoint["method"]
        url = f"{self.base_url}{path}"

        try:
            # Для POST/PUT/PATCH используем пустое тело, для остальных GET
            if method in ["POST", "PUT", "PATCH"]:
                response = self.session.request(method, url, json={})
            else:
                response = self.session.get(url)

            result = {
                "path": path,
                "method": method,
                "status_code": response.status_code,
                "success": response.status_code < 500,
                "response_time": response.elapsed.total_seconds(),
                "content_length": len(response.content),
            }

            # Для ошибок добавляем детали
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    result["error"] = error_data
                except:
                    result["error"] = response.text[:200]

            return result

        except Exception as e:
            return {
                "path": path,
                "method": method,
                "success": False,
                "error": str(e),
            }


def main():
    # Получаем токен
    login_url = "http://127.0.0.1:8000/login/json"
    login_data = {"email": "iloveigor@chillcreative.ru", "password": "123"}

    try:
        response = requests.post(login_url, json=login_data)
        response.raise_for_status()
        token = response.json()["access_token"]
        print("✅ Авторизация успешна")
    except Exception as e:
        print(f"❌ Ошибка авторизации: {e}")
        sys.exit(1)

    # Загружаем эндпоинты и исправляем пути для auth
    try:
        with open("api_check_results.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            endpoints = []
            for result in data.get("results", []):
                if result.get("status") == "available":
                    path = result["path"]
                    # Исправляем пути auth эндпоинтов
                    if path.startswith("/auth/"):
                        if path == "/auth/login/json":
                            path = "/login/json"
                        elif path == "/auth/login":
                            path = "/login"
                        elif path == "/auth/login/session":
                            path = "/login/session"
                        elif path == "/auth/logout":
                            path = "/logout"
                        elif path == "/auth/logout/all":
                            path = "/logout/all"
                        elif path == "/auth/me":
                            path = "/me"
                        elif path == "/auth/register":
                            path = "/register"
                        elif path == "/auth/verify-email":
                            path = "/verify-email"
                        elif path == "/auth/resend-verification":
                            path = "/resend-verification"
                        result["path"] = path
                    endpoints.append(result)
        print(f"📋 Загружено {len(endpoints)} эндпоинтов для тестирования")
    except Exception as e:
        print(f"❌ Ошибка загрузки эндпоинтов: {e}")
        sys.exit(1)

    # Тестируем эндпоинты
    tester = EndpointTester(token=token)
    results = []

    for i, endpoint in enumerate(endpoints, 1):
        print(
            f"🔍 Тестирование {i}/{len(endpoints)}: {endpoint['method']} {endpoint['path']}"
        )
        result = tester.test_endpoint(endpoint)
        results.append(result)

        # Показываем результат
        if result["success"]:
            print(f"  ✅ {result['status_code']}")
        else:
            print(f"  ❌ Ошибка: {result.get('error', 'Unknown')}")

    # Статистика
    successful = len([r for r in results if r.get("success")])
    total = len(results)
    success_rate = successful / total * 100 if total > 0 else 0

    print("\n" + "=" * 50)
    print("СТАТИСТИКА ТЕСТИРОВАНИЯ API:")
    print(f"Всего эндпоинтов: {total}")
    print(f"Успешных: {successful}")
    print(f"Ошибок: {total - successful}")
    print(".1f")
    print("=" * 50)

    # Сохраняем результаты
    output = {
        "stats": {
            "total": total,
            "successful": successful,
            "errors": total - successful,
            "success_rate": success_rate,
        },
        "results": results,
    }

    with open("endpoint_test_results.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("📄 Результаты сохранены в endpoint_test_results.json")

    if total - successful > 0:
        print("\n❌ ОШИБКИ:")
        for result in results:
            if not result.get("success"):
                print(
                    f"- {result['method']} {result['path']}: {result.get('error', 'Unknown error')}"
                )


if __name__ == "__main__":
    main()