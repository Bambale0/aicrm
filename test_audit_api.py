#!/usr/bin/env python3
"""
Comprehensive API audit script for AI CRM system
Tests all major endpoints for functionality and completeness
"""
import requests
import json
import time
import os
from typing import Dict, List

BASE_URL = "http://localhost:8000"

def get_auth_token(email: str = "iloveigor@chillcreative.ru", password: str = "25896311Aaa") -> str:
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/auth/login/json", json={
        "email": email,
        "password": password
    })

    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"❌ Authentication failed: {response.status_code} - {response.text}")
        return None

def test_endpoint(method: str, url: str, headers: Dict = None, data: Dict = None, auth_required: bool = True) -> Dict:
    """Test a single endpoint"""
    full_url = f"{BASE_URL}{url}"
    headers = headers or {}

    if auth_required and "Authorization" not in headers:
        token = get_auth_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        else:
            return {"success": False, "status_code": 401, "error": "No auth token"}

    try:
        if method.upper() == "GET":
            response = requests.get(full_url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(full_url, headers=headers, json=data)
        elif method.upper() == "PUT":
            response = requests.put(full_url, headers=headers, json=data)
        elif method.upper() == "DELETE":
            response = requests.delete(full_url, headers=headers)
        else:
            return {"success": False, "status_code": 0, "error": f"Unsupported method: {method}"}

        if response.status_code in [200, 201, 204]:
            return {"success": True, "status_code": response.status_code, "data": response.json() if response.text else None}
        else:
            return {"success": False, "status_code": response.status_code, "error": response.text}

    except Exception as e:
        return {"success": False, "status_code": 0, "error": str(e)}

def get_openapi_endpoints() -> List[str]:
    """Get all available endpoints from OpenAPI spec"""
    try:
        response = requests.get(f"{BASE_URL}/openapi.json")
        if response.status_code == 200:
            spec = response.json()
            return list(spec.get("paths", {}).keys())
        return []
    except:
        return []

def audit_api_comprehensive():
    """Comprehensive API audit"""
    print("🔍 Starting comprehensive API audit...")
    print("=" * 60)

    # Health check
    print("🏥 Health Check Endpoints:")
    health_tests = [
        ("/health", "Basic health check"),
        ("/health/detailed", "Detailed health check"),
        ("/api/health", "API health check"),
        ("/metrics", "Prometheus metrics"),
        ("/api/status", "AI status"),
    ]

    for endpoint, description in health_tests:
        result = test_endpoint("GET", endpoint, auth_required=False)
        status = "✅" if result["success"] else "❌"
        print(f"  {status} {endpoint} - {description}")

    # Authentication endpoints
    print("\n🔐 Authentication Endpoints:")
    auth_tests = [
        ("/auth/login", "Legacy login"),
        ("/auth/login/json", "JSON login"),
        ("/auth/me", "Current user info"),
        ("/api/me", "Legacy current user"),
    ]

    for endpoint, description in auth_tests:
        result = test_endpoint("GET" if endpoint.endswith("/me") else "POST", endpoint,
                             data={"email": "iloveigor@chillcreative.ru", "password": "25896311Aaa"} if "login" in endpoint else None,
                             auth_required="login" not in endpoint)
        status = "✅" if result["success"] else "❌"
        print(f"  {status} {endpoint} - {description}")

    # CRUD endpoints to test
    crud_entities = [
        ("customers", "/api/customers", {
            "name": "Test Customer",
            "email": "test@example.com",
            "phone": "+7-999-123-45-67"
        }),
        ("products", "/api/products", {
            "name": "Test Product",
            "price": 1000.0,
            "category": "test"
        }),
        ("services", "/api/services", {
            "name": "Test Service",
            "price": 500.0,
            "category": "test"
        }),
        ("tasks", "/api/tasks", {
            "title": "Test Task",
            "description": "Test description",
            "priority": "medium"
        }),
    ]

    print("\n📋 CRUD Operations Test:")
    for entity_name, base_url, test_data in crud_entities:
        try:
            # Test LIST
            list_result = test_endpoint("GET", base_url)
            list_status = "✅" if list_result["success"] else "❌"
            print(f"  {list_status} {entity_name}: LIST {base_url}")

            # Test CREATE
            create_result = test_endpoint("POST", base_url, data=test_data)
            if create_result["success"]:
                create_status = "✅"
                if create_result.get("data") and "id" in create_result["data"]:
                    entity_id = create_result["data"]["id"]

                    # Test GET single
                    get_result = test_endpoint("GET", f"{base_url}/{entity_id}")
                    get_status = "✅" if get_result["success"] else "❌"

                    # Test UPDATE
                    update_result = test_endpoint("PUT", f"{base_url}/{entity_id}",
                                                data={**test_data, "name": f"Updated {test_data['name']}"})
                    update_status = "✅" if update_result["success"] else "❌"

                    # Test DELETE
                    delete_result = test_endpoint("DELETE", f"{base_url}/{entity_id}")
                    delete_status = "✅" if delete_result["success"] else "❌"

                    print(f"    ✅ CREATE/GET/UPDATE/DELETE {entity_name}")
                else:
                    create_status = "❌"
                    print(f"    ❌ CREATE {entity_name}")
            else:
                create_status = "❌"
                print(f"  {entity_name}: LIST = {list_result['status_code']}, CREATE = {create_result['status_code']}")

        except Exception as e:
            print(f"  ❌ Error testing {entity_name}: {str(e)}")

    # AI endpoints
    print("\n🤖 AI Endpoints:")
    ai_tests = [
        ("/api/models", "Available AI models"),
        ("/api/usage/monthly", "Monthly AI usage"),
        ("/api/usage/history", "AI usage history"),
        ("/api/ai-manager/prompts", "AI prompts management"),
        ("/api/ai-settings", "AI settings"),
    ]

    for endpoint, description in ai_tests:
        result = test_endpoint("GET", endpoint)
        status = "✅" if result["success"] else "❌"
        print(f"  {status} {endpoint} - {description}")

    # Order & Production
    print("\n📦 Orders & Production:")
    order_tests = [
        ("/api/orders", "Orders list"),
        ("/api/catalog/products", "Product catalog"),
        ("/api/catalog/services", "Service catalog"),
    ]

    for endpoint, description in order_tests:
        result = test_endpoint("GET", endpoint)
        status = "✅" if result["success"] else "❌"
        print(f"  {status} {endpoint} - {description}")

    # Communication
    print("\n💬 Communication Endpoints:")
    comm_tests = [
        ("/api/communications", "Communications history"),
        ("/api/email/test-imap", "Email IMAP test"),
    ]

    for endpoint, description in comm_tests:
        result = test_endpoint("GET" if "communications" in endpoint else "POST", endpoint)
        status = "✅" if result["success"] else "❌"
        print(f"  {status} {endpoint} - {description}")

    # Automation
    print("\n⚙️ Automation Endpoints:")
    auto_tests = [
        ("/api/automation/processes", "Automation processes"),
        ("/api/automation/stages", "Automation stages"),
        ("/api/automation/triggers", "Automation triggers"),
        ("/api/automation/robots", "Automation robots"),
    ]

    for endpoint, description in auto_tests:
        result = test_endpoint("GET", endpoint)
        status = "✅" if result["success"] else "❌"
        print(f"  {status} {endpoint} - {description}")


    # External integrations
    print("\n🔗 External Integrations:")
    ext_tests = [
        ("/api/avito/items", "Avito items"),
        ("/api/telegram/chats", "Telegram chats"),
    ]

    for endpoint, description in ext_tests:
        result = test_endpoint("GET", endpoint)
        status = "✅" if result["success"] else "❌"
        print(f"  {status} {endpoint} - {description}")

    print("\n" + "=" * 60)
    print("🎉 API audit completed!")

if __name__ == "__main__":
    audit_api_comprehensive()
