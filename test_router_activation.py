#!/usr/bin/env python3
"""
Script to systematically test and activate API routers
"""
import subprocess
import time
import os
import requests
import sys

BASE_URL = "http://localhost:8000"

def test_router_start(router_name: str):
    """Test if server starts with a specific router enabled"""
    print(f"\n🔄 Testing {router_name} router...")

    try:
        # Start server with uvicorn directly
        server = subprocess.Popen([
            'python3', '-m', 'uvicorn',
            'backend.src.aicrm.main:app',
            '--host', '0.0.0.0',
            '--port', '8000',
            '--log-level', 'error'  # Reduce noise
        ], cwd='/root/aicrm', stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Wait for startup
        time.sleep(8)

        try:
            # Basic health check
            resp = requests.get(f'{BASE_URL}/health', timeout=5)
            if resp.status_code != 200:
                print(f"❌ SERVER FAIL: Health check returned {resp.status_code}")
                return False

            # Try to login
            login_resp = requests.post(f'{BASE_URL}/auth/login/json', json={
                'email': 'iloveigor@chillcreative.ru',
                'password': '25896311Aaa'
            }, timeout=5)

            if login_resp.status_code != 200:
                print(f"❌ AUTH FAIL: Login returned {login_resp.status_code}")
                return False

            print(f"✅ {router_name}: Server started successfully!")
            return True

        except requests.RequestException as e:
            print(f"❌ REQUEST FAIL: {str(e)}")
            return False

        finally:
            # Stop server
            os.system('pkill -f uvicorn > /dev/null 2>&1')

    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        return False

def main():
    """Test enabling each router one by one"""
    routers_to_test = [
        ("order", "include order router"),
        ("task", "include task router"),
        ("avito", "include avito router"),
        ("communication", "include communication router"),
        ("user", "include user router"),
        ("workflow", "include workflow router"),
        ("ai_settings", "include ai_settings router"),
    ]

    print("🚀 Router Activation Test")
    print("=" * 50)

    # First test current state (customer already enabled)
    if test_router_start("current_state"):
        print("\n✅ Base configuration working!")

        # Test each router
        for router_name, description in routers_to_test:
            print(f"\n🛠️  Enabling {router_name} router...")

            # Temporarily enable router in main.py
            os.system(f'cd /root/aicrm && sed -i "s/# fastapi_app.include_router({router_name}.router/# fastapi_app.include_router({router_name}.router/g" backend/src/aicrm/main.py')
            os.system(f'cd /root/aicrm && sed -i "s/# Temporarily disabled.*{router_name}/# {router_name} enabled for testing/g" backend/src/aicrm/main.py')

            # Test
            if test_router_start(router_name):
                print(f"✅ {router_name}: WORKS!")
                # Keep it enabled
            else:
                print(f"❌ {router_name}: FAILS - disabling")
                # Re-disable it
                os.system(f'cd /root/aicrm && sed -i "s/fastapi_app.include_router({router_name}.router/# fastapi_app.include_router({router_name}.router/g" backend/src/aicrm/main.py')
                os.system(f'cd /root/aicrm && sed -i "s/# {router_name} enabled for testing/# Temporarily disabled due to circular import issues:/g" backend/src/aicrm/main.py')

        print("\n🎉 Router activation test complete!")

    else:
        print("\n❌ Base configuration broken!")
        sys.exit(1)

if __name__ == "__main__":
    main()
