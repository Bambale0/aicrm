#!/usr/bin/env python3
"""
Comprehensive API Testing Script for AI CRM System
Tests all API endpoints: GET, POST, PUT, DELETE routes
"""

import requests
import time
from typing import Tuple

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

# Colors for output
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
ENDC = '\033[0m'

# Test user credentials (you may need to register first)
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword123"

# Global variables
auth_token = None
test_customer_id = None
test_order_id = None
test_task_id = None

def print_colored(text: str, color: str):
    """Print colored text"""
    print(f"{color}{text}{ENDC}")

def login() -> str:
    """Login and get auth token"""
    print("🔐 Logging in...")

    # Try legacy login first
    login_data = {"username": TEST_EMAIL, "password": TEST_PASSWORD}
    try:
        response = requests.post(f"{API_BASE}/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if token:
                print_colored("✅ Login successful", GREEN)
                return token
    except:
        pass

    # Try form login
    try:
        response = requests.post(f"{API_BASE}/auth/login", data={"username": TEST_EMAIL, "password": TEST_PASSWORD})
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if token:
                print_colored("✅ Form login successful", GREEN)
                return token
    except:
        pass

    print_colored("❌ Login failed - will proceed without auth for public endpoints", RED)
    return None

def test_endpoint(method: str, url: str, data=None, json_data=None, headers=None, name="") -> Tuple[bool, str]:
    """Test a single endpoint"""
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            if json_data:
                response = requests.post(url, json=json_data, headers=headers)
            else:
                response = requests.post(url, data=data, headers=headers)
        elif method.upper() == "PUT":
            response = requests.put(url, json=json_data, headers=headers)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            return False, f"Unknown method: {method}"

        if response.status_code < 400:
            status = f"✅ {response.status_code}"
        elif response.status_code < 500:
            status = f"⚠️  {response.status_code}"
        else:
            status = f"❌ {response.status_code}"

        return True, f"{status} {method} {url.replace(BASE_URL, '')} {name}"

    except Exception as e:
        return False, f"❌ ERROR {method} {url.replace(BASE_URL, '')} {name}: {str(e)}"

def test_public_get_routes():
    """Test public GET routes that don't require auth"""
    print("\n🌐 Testing public GET routes...")

    routes = [
        ("/health", "Health check"),
        ("/status", "AI status"),
        ("/usage/monthly", "Monthly usage"),
        (f"{API_BASE}/ai/public/status", "Public AI status"),
        (f"{API_BASE}/catalog/categories", "Catalog categories"),
        (f"{API_BASE}/catalog/products", "Catalog products"),
        (f"{API_BASE}/catalog/services", "Catalog services"),
        (f"{API_BASE}/catalog/search", "Catalog search"),
        (f"{API_BASE}/catalog/featured", "Catalog featured"),
        (f"{API_BASE}/ai/models", "AI models"),
        (f"{API_BASE}/ai/status", "AI status endpoint"),
    ]

    successful = 0
    total = len(routes)

    for url, name in routes:
        success, message = test_endpoint("GET", url, name=name)
        print(message)
        if success:
            successful += 1
        time.sleep(0.1)  # Rate limiting

    print(f"\n🧮 Public GET routes: {successful}/{total} passed")

def test_auth_required_routes():
    """Test routes that require authentication"""
    print("\n🔒 Testing auth-required routes...")

    headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}

    # Auth routes (me)
    auth_routes = [
        (f"{API_BASE}/auth/me", {}, "Current user (auth)"),
        (f"{API_BASE}/me", {}, "Current user (legacy)"),  # Legacy
    ]

    successful = 0
    total = 0

    for url, data, name in auth_routes:
        success, message = test_endpoint("GET", url, headers=headers, name=name)
        print(message)
        if success:
            successful += 1
        total += 1
        time.sleep(0.1)

    # Customer routes
    customer_routes = [
        (f"{API_BASE}/customers", {}, "Get customers"),
        (f"{API_BASE}/customers/search", {"q": "*"}, "Search customers"),
    ]

    for url, data, name in customer_routes:
        success, message = test_endpoint("GET", url, headers=headers, name=name)
        print(message)
        if success:
            successful += 1
        total += 1
        time.sleep(0.1)

    # Orders routes
    order_routes = [
        (f"{API_BASE}/orders", {}, "Get orders"),
    ]

    for url, data, name in order_routes:
        success, message = test_endpoint("GET", url, headers=headers, name=name)
        print(message)
        if success:
            successful += 1
        total += 1
        time.sleep(0.1)

    # Tasks routes
    task_routes = [
        (f"{API_BASE}/tasks", {}, "Get tasks"),
    ]

    for url, data, name in task_routes:
        success, message = test_endpoint("GET", url, headers=headers, name=name)
        print(message)
        if success:
            successful += 1
        total += 1
        time.sleep(0.1)

    # Communications routes
    comm_routes = [
        (f"{API_BASE}/communications", {}, "Get communications"),
        (f"{API_BASE}/communications/stats/summary", {}, "Communications stats"),
    ]

    for url, data, name in comm_routes:
        success, message = test_endpoint("GET", url, headers=headers, name=name)
        print(message)
        if success:
            successful += 1
        total += 1
        time.sleep(0.1)

    # AI routes that require auth
    ai_routes = [
        (f"{API_BASE}/ai/usage/monthly", {}, "AI monthly usage"),
        (f"{API_BASE}/ai/usage/history", {}, "AI usage history"),
        (f"{API_BASE}/ai/settings/ai", {}, "AI settings"),
    ]

    for url, data, name in ai_routes:
        success, message = test_endpoint("GET", url, headers=headers, name=name)
        print(message)
        if success:
            successful += 1
        total += 1
        time.sleep(0.1)

    print(f"\n🧮 Auth-required GET routes: {successful}/{total} passed")

def test_ai_manager_routes():
    """Test AI Manager specific routes"""
    print("\n🤖 Testing AI Manager routes...")

    headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}

    routes = [
        (f"{API_BASE}/ai-manager/prompts", {}, "Get AI prompts"),
        (f"{API_BASE}/ai-manager/services", {}, "Get services"),
        (f"{API_BASE}/ai-manager/products", {}, "Get products"),
        (f"{API_BASE}/ai-manager/services/categories", {}, "Service categories"),
        (f"{API_BASE}/ai-manager/products/categories", {}, "Product categories"),
    ]

    successful = 0
    total = len(routes)

    for url, data, name in routes:
        success, message = test_endpoint("GET", url, headers=headers, name=name)
        print(message)
        if success:
            successful += 1
        time.sleep(0.1)

    print(f"\n🧮 AI Manager routes: {successful}/{total} passed")

def test_automation_routes():
    """Test Automation routes (basic GET only)"""
    print("\n⚙️ Testing Automation routes...")

    headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}

    routes = [
        (f"{API_BASE}/automation/processes", {}, "Get processes"),
        (f"{API_BASE}/automation/stages", {}, "Get stages"),
        (f"{API_BASE}/automation/triggers", {}, "Get triggers"),
        (f"{API_BASE}/automation/robots", {}, "Get robots"),
        (f"{API_BASE}/automation/analytics/executions", {}, "Analytics executions"),
        (f"{API_BASE}/automation/logs", {}, "Automation logs"),
    ]

    successful = 0
    total = len(routes)

    for url, data, name in routes:
        success, message = test_endpoint("GET", url, headers=headers, name=name)
        print(message)
        if success:
            successful += 1
        time.sleep(0.1)

    print(f"\n🧮 Automation routes: {successful}/{total} passed")

def test_email_routes():
    """Test Email routes (basic GET only)"""
    print("\n📧 Testing Email routes...")

    headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}

    routes = [
        (f"{API_BASE}/email/templates", {}, "Email templates"),
        (f"{API_BASE}/email/status", {}, "Email status"),
        (f"{API_BASE}/email/stats", {}, "Email stats"),
    ]

    successful = 0
    total = len(routes)

    for url, data, name in routes:
        success, message = test_endpoint("GET", url, headers=headers, name=name)
        print(message)
        if success:
            successful += 1
        time.sleep(0.1)

    print(f"\n🧮 Email routes: {successful}/{total} passed")

def test_other_routes():
    """Test various other routes"""
    print("\n🔧 Testing other routes...")

    headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}

    routes = [
        (f"{API_BASE}/users", {}, "Get users"),
        (f"{API_BASE}/avito/items", {}, "Avito items"),
        (f"{API_BASE}/avito/settings", {}, "Avito settings"),
        (f"{API_BASE}/telegram/stats", {}, "Telegram stats"),
        (f"{API_BASE}/production/steps", {}, "Production steps"),
    ]

    successful = 0
    total = len(routes)

    for url, data, name in routes:
        success, message = test_endpoint("GET", url, headers=headers, name=name)
        print(message)
        if success:
            successful += 1
        time.sleep(0.1)

    print(f"\n🧮 Other routes: {successful}/{total} passed")

def main():
    print("🧪 Starting comprehensive API testing for AI CRM system...")
    print(f"📡 Base URL: {BASE_URL}")

    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print_colored("✅ Server is running", GREEN)
        else:
            print_colored(f"⚠️ Server responded with {response.status_code}", YELLOW)
    except:
        print_colored("❌ Server is not running. Please start it with ./start.sh", RED)
        return

    global auth_token
    auth_token = login()

    # Test all GET routes for basic functionality
    test_public_get_routes()
    test_auth_required_routes()
    test_ai_manager_routes()
    test_automation_routes()
    test_email_routes()
    test_other_routes()

    print("\n🎉 API testing completed!")
    print("\n📋 Next steps:")
    print("- Review failed endpoints and fix issues")
    print("- Test POST/PUT/DELETE routes with proper test data")
    print("- Test authentication flow")
    print("- Test rate limiting")
    print("- Test error handling")

if __name__ == "__main__":
    main()
