#!/bin/bash

# AI CRM Local Development Runner (No Docker)
# This script sets up and runs the AI CRM application with native Redis for local development

set -e

echo "🚀 Starting AI CRM Local Development Environment (No Docker)"
echo "============================================================"

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

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    print_status "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
fi

# Check if redis-server is available (native only, no Docker)
if ! command -v redis-server &> /dev/null; then
    print_error "redis-server not found. Please install Redis:"
    echo "  apt update && apt install redis-server"
    echo "  Then start with: systemctl start redis-server"
    exit 1
fi

print_status "Using native Redis server..."

# Check if Redis is already running
if pgrep -x "redis-server" > /dev/null; then
    print_warning "Redis server already running"
else
    # Start Redis server (assuming default config)
    print_status "Starting Redis server..."
    redis-server &
    REDIS_PID=$!
    print_status "Redis server started (PID: $REDIS_PID)"

    # Wait for Redis to be ready
    print_status "Waiting for Redis to be ready..."
    for i in {1..30}; do
        if redis-cli ping 2>/dev/null | grep -q PONG; then
            print_status "Redis is ready!"
            break
        fi
        sleep 1
    done
fi

# Set PYTHONPATH for the project
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"

# Check Python environment
if ! command -v python3 &> /dev/null; then
    print_error "Python3 not found. Please install Python 3.11+"
    exit 1
fi

# Check if virtual environment exists
if [ -d "venv" ]; then
    print_status "Activating virtual environment..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    print_status "Activating virtual environment (.venv)..."
    source .venv/bin/activate
else
    print_warning "No virtual environment found. Using system Python."
    print_warning "Consider creating a virtual environment:"
    echo "  python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
fi

# Install/update dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    print_status "Installing/updating Python dependencies..."
    pip install -r requirements.txt
elif [ -f "pyproject.toml" ]; then
    print_status "Installing from pyproject.toml..."
    pip install -e .
fi

# Check database connectivity (optional)
print_status "Checking database connectivity..."
python3 -c "
import sys
sys.path.insert(0, 'src')
try:
    from aicrm.core.database import SessionLocal
    from sqlalchemy import text
    db = SessionLocal()
    db.execute(text('SELECT 1'))
    db.close()
    print('✅ Database connection OK')
except Exception as e:
    print(f'⚠️  Database connection issue: {e}')
    print('   Make sure PostgreSQL is running and configured')
"

# Set environment variables for development
export AICRM_ENV=development

# Ensure Redis URL is set (fallback if not in .env)
export REDIS_URL=${REDIS_URL:-redis://localhost:6379/0}

# Function to cleanup on exit
cleanup() {
    print_status "Shutting down..."

    # Kill FastAPI process
    if [ ! -z "$FASTAPI_PID" ]; then
        print_status "Stopping FastAPI application..."
        kill $FASTAPI_PID 2>/dev/null || true
    fi

    # Kill Socket.IO process
    if [ ! -z "$SOCKET_PID" ]; then
        print_status "Stopping Socket.IO server..."
        kill $SOCKET_PID 2>/dev/null || true
    fi

    # Kill Redis server if started by this script
    if [ ! -z "$REDIS_PID" ]; then
        print_status "Stopping Redis server..."
        kill $REDIS_PID 2>/dev/null || true
    fi

    print_status "Cleanup complete"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

print_status "Starting AI CRM application..."
print_status "FastAPI will be available at: http://localhost:8000"
print_status "Socket.IO will be available at: http://localhost:8001"
print_status "API documentation at: http://localhost:8000/docs"
print_status "Press Ctrl+C to stop all services"

# Set default ports
FASTAPI_PORT=${FASTAPI_PORT:-8000}
SOCKET_PORT=${SOCKET_PORT:-8001}

# Start FastAPI application in background
print_status "Starting FastAPI application on port ${FASTAPI_PORT}..."
PYTHONPATH="$(pwd)/src:$PYTHONPATH" python3 -m uvicorn aicrm.main:app \
    --host 0.0.0.0 \
    --port ${FASTAPI_PORT} \
    --reload \
    --log-level info \
    --access-log \
    --env-file .env &
FASTAPI_PID=$!

# Start Socket.IO server in background
print_status "Starting Socket.IO server on port ${SOCKET_PORT}..."
PYTHONPATH="$(pwd)/src:$PYTHONPATH" python3 -m uvicorn aicrm.socket_server:socket_app \
    --host 0.0.0.0 \
    --port ${SOCKET_PORT} \
    --reload \
    --log-level info &
SOCKET_PID=$!

print_status "FastAPI PID: ${FASTAPI_PID}"
print_status "Socket.IO PID: ${SOCKET_PID}"

# Wait for both processes
wait ${FASTAPI_PID} ${SOCKET_PID}

# This point should not be reached due to processes running in foreground
cleanup
