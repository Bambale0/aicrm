"""
AI CRM Load Testing with Locust

This script simulates real user behavior for load testing the AI CRM system.
It includes authentication, CRUD operations, AI completions, and monitoring endpoints.

Run with: locust -f locustfile.py --host http://localhost:8000
"""

import json
import random
import time
from typing import Dict, List, Optional

from locust import HttpUser, task, between, events
from locust.env import Environment


class AICRMUser(HttpUser):
    """
    Represents a typical AI CRM user for load testing.

    Simulates different user behaviors:
    - Admin users: Create customers, orders, manage system
    - Customer service users: View customers, update orders
    - Analytics users: View reports and statistics
    """

    # Wait time between tasks (realistic user behavior)
    wait_time = between(1, 3)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_token: Optional[str] = None
        self.user_role: str = "user"
        self.customer_ids: List[int] = []
        self.order_ids: List[int] = []

    def on_start(self):
        """Login and setup user session"""
        self.login()

    def on_stop(self):
        """Cleanup user session"""
        if self.auth_token:
            self.logout()

    def login(self):
        """Authenticate user and get JWT token"""
        # Use different user accounts for realistic load distribution
        user_credentials = [
            {"email": "admin@example.com", "password": "password123"},
            {"email": "user@example.com", "password": "password123"},
            {"email": "cs@example.com", "password": "password123"},
            {"email": "analytics@example.com", "password": "password123"},
        ]

        credential = random.choice(user_credentials)

        with self.client.post(
            "/api/auth/login/session",
            json=credential,
            catch_response=True,
            name="login"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.user_role = data.get("role", "user")

                # Set authorization header for subsequent requests
                self.client.headers.update({
                    "Authorization": f"Bearer {self.auth_token}",
                    "Content-Type": "application/json"
                })
                response.success()
            else:
                response.failure(f"Login failed: {response.status_code}")

    def logout(self):
        """Logout user and clear session"""
        with self.client.post("/api/auth/logout", name="logout") as response:
            if response.status_code == 200:
                self.auth_token = None
                self.client.headers.pop("Authorization", None)

    @task(3)  # Higher weight - most common operation
    def view_customers(self):
        """View customers list (high frequency operation)"""
        if not self.auth_token:
            return

        params = {
            "skip": random.randint(0, 100),
            "limit": random.randint(10, 50)
        }

        with self.client.get(
            "/api/customers",
            params=params,
            name="view_customers"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                # Cache some customer IDs for other operations
                if isinstance(data, list) and len(data) > 0:
                    self.customer_ids = [c.get("id") for c in data[:10]]

    @task(2)
    def create_customer(self):
        """Create new customer (admin/manager operations)"""
        if not self.auth_token or self.user_role not in ["admin", "manager"]:
            return

        customer_data = {
            "name": f"Test Customer {random.randint(1000, 9999)}",
            "email": f"test{random.randint(1000, 9999)}@example.com",
            "phone": f"+7 (999) {random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10, 99)}",
            "company": f"Test Company {random.randint(1, 100)}" if random.choice([True, False]) else None
        }

        with self.client.post(
            "/api/customers",
            json=customer_data,
            name="create_customer"
        ) as response:
            if response.status_code == 201:
                data = response.json()
                if "id" in data:
                    self.customer_ids.append(data["id"])
            elif response.status_code == 403:
                # Skip if no permissions
                pass

    @task(3)
    def view_orders(self):
        """View orders list"""
        if not self.auth_token:
            return

        params = {
            "skip": random.randint(0, 100),
            "limit": random.randint(10, 50)
        }

        with self.client.get(
            "/api/orders",
            params=params,
            name="view_orders"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    self.order_ids = [o.get("id") for o in data[:10]]

    @task(2)
    def create_order(self):
        """Create new order"""
        if not self.auth_token or not self.customer_ids:
            return

        customer_id = random.choice(self.customer_ids)
        order_data = {
            "customer_id": customer_id,
            "print_type": random.choice(["screen_print", "dtf", "embroidery", "heat_transfer"]),
            "quantity": random.randint(10, 1000),
            "total_amount": random.randint(5000, 100000),
            "requirements": f"Тестовый заказ на печать логотипа. Номер заказа: {random.randint(1000, 9999)}",
            "deadline": f"2025-{random.randint(12, 12)}-{random.randint(1, 28):02d}T00:00:00Z"
        }

        with self.client.post(
            "/api/orders",
            json=order_data,
            name="create_order"
        ) as response:
            if response.status_code == 201:
                data = response.json()
                if "id" in data:
                    self.order_ids.append(data["id"])
            elif response.status_code in [403, 422]:
                # Skip if no permissions or validation error
                pass

    @task(1)  # Lower weight - less frequent AI operations
    def ai_completion(self):
        """Test AI completion endpoint under load"""
        if not self.auth_token:
            return

        # Simulate different types of AI requests
        prompts = [
            "Проанализируй этот заказ на печать футболок",
            "Как оптимизировать процесс производства?",
            "Какие цвета подходят для корпоративной одежды?",
            "Как рассчитать стоимость печати?",
        ]

        ai_request = {
            "model": "deepseek/deepseek-coder:33b-instruct",
            "messages": [
                {
                    "role": "system",
                    "content": "Ты - помощник специалиста по печати и производству в CRM системе."
                },
                {
                    "role": "user",
                    "content": random.choice(prompts)
                }
            ],
            "temperature": random.uniform(0.1, 0.9),
            "max_tokens": random.randint(100, 500)
        }

        start_time = time.time()
        with self.client.post(
            "/api/ai/completions",
            json=ai_request,
            name="ai_completion"
        ) as response:
            response_time = time.time() - start_time

            if response.status_code == 200:
                # Log AI response time for monitoring
                events.request.fire(
                    request_type="AI",
                    name="ai_completion",
                    response_time=int(response_time * 1000),
                    response_length=len(response.content),
                    exception=None
                )
            elif response.status_code == 429:
                # Rate limited - log but don't mark as error
                events.request.fire(
                    request_type="AI",
                    name="ai_completion_ratelimit",
                    response_time=int(response_time * 1000),
                    response_length=0,
                    exception=None
                )
            else:
                response.failure(f"AI request failed: {response.status_code}")

    @task(2)
    def health_check(self):
        """Regular health checks (important for monitoring)"""
        with self.client.get("/health", name="health_check") as response:
            if response.status_code != 200:
                response.failure("Health check failed")

    @task(1)
    def detailed_health(self):
        """Detailed health check (admin operations)"""
        if self.user_role == "admin":
            with self.client.get("/health/detailed", name="detailed_health") as response:
                if response.status_code != 200:
                    response.failure("Detailed health check failed")

    @task(1)
    def view_analytics(self):
        """View analytics and reports (management operations)"""
        if self.user_role in ["admin", "manager"]:
            with self.client.get("/api/analytics/overview", name="analytics_overview") as response:
                if response.status_code == 403:
                    # No permissions - expected
                    pass
                elif response.status_code != 200:
                    response.failure("Analytics access failed")

    @task(1)
    def update_order_status(self):
        """Update order status (operational workflow)"""
        if not self.auth_token or not self.order_ids:
            return

        order_id = random.choice(self.order_ids)
        status = random.choice(["paid", "in_production", "completed"])

        with self.client.put(
            f"/api/orders/{order_id}/status",
            json={"status": status},
            name="update_order_status"
        ) as response:
            if response.status_code not in [200, 404, 403]:
                response.failure(f"Order update failed: {response.status_code}")


class AdminUser(AICRMUser):
    """Specialized admin user with higher admin operations rate"""

    wait_time = between(2, 5)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def login(self):
        """Admin login"""
        credential = {"email": "admin@example.com", "password": "password123"}

        with self.client.post(
            "/api/auth/login/session",
            json=credential,
            catch_response=True,
            name="admin_login"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.user_role = "admin"

                self.client.headers.update({
                    "Authorization": f"Bearer {self.auth_token}",
                    "Content-Type": "application/json"
                })
                response.success()
            else:
                response.failure(f"Admin login failed: {response.status_code}")

    @task(5)  # High weight for admin operations
    def admin_create_customer(self):
        """Admin creating customers"""
        self.create_customer()

    @task(3)
    def system_monitoring(self):
        """Admin monitoring system"""
        with self.client.get("/api/metrics", name="metrics_endpoint") as response:
            if response.status_code == 404:
                # Metrics endpoint might not be configured
                pass
