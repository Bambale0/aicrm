#!/bin/bash

# AI CRM Stop Script
# This script stops all running services (Redis, FastAPI application)

set -e

echo "🛑 Stopping AI CRM Services"
echo "==========================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to kill process by port
kill_process_by_port() {
    local port=$1
    local name=$2

    # Find process using the port
    local pid=$(lsof -ti :$port 2>/dev/null)

    if [ ! -z "$pid" ]; then
        print_status "Stopping $name (PID: $pid) on port $port..."
        kill $pid 2>/dev/null || true
        sleep 2

        # Force kill if still running
        if kill -0 $pid 2>/dev/null; then
            print_warning "Force killing $name..."
            kill -9 $pid 2>/dev/null || true
        fi

        print_status "$name stopped"
    else
        print_warning "No $name process found on port $port"
    fi
}

# Function to kill process by name
kill_process_by_name() {
    local name=$1
    local display_name=$2

    # Find processes by name
    local pids=$(pgrep -f "$name")

    if [ ! -z "$pids" ]; then
        print_status "Stopping $display_name processes..."
        echo "$pids" | xargs kill 2>/dev/null || true
        sleep 2

        # Force kill if still running
        for pid in $pids; do
            if kill -0 $pid 2>/dev/null; then
                print_warning "Force killing $display_name (PID: $pid)..."
                kill -9 $pid 2>/dev/null || true
            fi
        done

        print_status "$display_name stopped"
    else
        print_warning "No $display_name processes found"
    fi
}

# Stop FastAPI application
print_status "Stopping FastAPI application..."
kill_process_by_port 8000 "FastAPI"

# Stop Redis server (if started by local_run.sh)
print_status "Stopping Redis server..."
kill_process_by_name "redis-server" "Redis server"

# Stop any uvicorn processes
print_status "Stopping any remaining uvicorn processes..."
kill_process_by_name "uvicorn" "Uvicorn"

# Stop any python processes running the app
print_status "Stopping any Python application processes..."
kill_process_by_name "aicrm.main:app" "AI CRM application"

# Final cleanup check
print_status "Performing final cleanup check..."

# Check if port 8000 is still in use
if lsof -i :8000 >/dev/null 2>&1; then
    print_warning "Port 8000 still in use. Forcing cleanup..."
    kill_process_by_port 8000 "remaining process"
fi

# Check if Redis is still running
if pgrep -x "redis-server" > /dev/null; then
    print_warning "Redis server still running. You may need to stop it manually:"
    echo "  sudo systemctl stop redis-server"
    echo "  or: redis-cli shutdown"
fi

print_status "AI CRM services stopped successfully"
print_status "All processes have been terminated"
