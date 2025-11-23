#!/bin/bash
# Start script for AI CRM application

set -e  # Exit on any error

echo "🚀 Запуск AI CRM системы..."

# Функция для проверки доступности порта
check_port() {
    local port=$1
    local timeout=30
    local count=0

    while ! nc -z localhost $port 2>/dev/null; do
        if [ $count -ge $timeout ]; then
            echo "❌ Таймаут ожидания порта $port"
            return 1
        fi
        sleep 1
        count=$((count + 1))
    done
    echo "✅ Порт $port доступен"
    return 0
}

# 1. Запуск PostgreSQL (если не запущен)
echo "📊 Проверка PostgreSQL..."
if ! pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
    echo "🔄 Запуск PostgreSQL..."
    sudo systemctl start postgresql
    sleep 2
fi

# 2. Запуск Redis (если не запущен)
echo "🔴 Проверка Redis..."
if ! redis-cli ping >/dev/null 2>&1; then
    echo "🔄 Запуск Redis..."
    sudo systemctl start redis-server
    sleep 2
fi

# Проверка подключения к Redis
echo "🔗 Проверка подключения к Redis..."
if ! redis-cli ping >/dev/null 2>&1; then
    echo "❌ Redis недоступен. Проверьте конфигурацию."
    exit 1
fi
echo "✅ Redis подключен"

# 3. Запуск backend (FastAPI)
echo "🔧 Запуск backend (FastAPI)..."
cd /root/aicrm/backend/src || { echo "❌ Не удалось перейти в директорию /root/aicrm/backend/src"; exit 1; }

# Установка переменных окружения для backend
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-8000}
export PYTHONPATH=/root/aicrm/backend/src:/root/aicrm/backend:$PYTHONPATH
# export DATABASE_URL=${DATABASE_URL:-sqlite:///./aicrm.db}  # Using PostgreSQL from config
export SECRET_KEY=${SECRET_KEY:-your-secret-key-change-in-production}
export DEBUG=${DEBUG:-false}
export OPENROUTER_API_KEY=${OPENROUTER_API_KEY:-}
export AVITO_CLIENT_ID=${AVITO_CLIENT_ID:-}
export AVITO_CLIENT_SECRET=${AVITO_CLIENT_SECRET:-}
export AVITO_USER_ID=${AVITO_USER_ID:-}

# Запуск FastAPI через uvicorn в фоне
uvicorn aicrm.main:app --reload --host $HOST --port $PORT &
BACKEND_PID=$!
echo "📝 Backend PID: $BACKEND_PID"

# Ожидание запуска backend
echo "⏳ Ожидание запуска backend на порту $PORT..."
if ! check_port $PORT; then
    echo "❌ Backend не запустился"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# 4. Запуск frontend (React)
echo "🎨 Запуск frontend (React)..."
cd /root/aicrm/frontend || { echo "❌ Не удалось перейти в директорию /root/aicrm/frontend"; exit 1; }

# Очистка переменных окружения, которые могут конфликтовать с React
unset HOST
export PORT=3000

# Запуск React dev server в фоне
npm run dev &
FRONTEND_PID=$!
echo "📝 Frontend PID: $FRONTEND_PID"

# Ожидание запуска frontend (порт 3000)
echo "⏳ Ожидание запуска frontend на порту 3000..."
if ! check_port 3000; then
    echo "❌ Frontend не запустился"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 1
fi

# 5. Запуск Nginx (если настроен)
echo "🌐 Проверка Nginx..."
if sudo systemctl is-active --quiet nginx; then
    echo "✅ Nginx уже запущен"
else
    echo "🔄 Запуск Nginx..."
    sudo systemctl start nginx
fi

# Сохранение PID процессов
echo $BACKEND_PID > /tmp/aicrm_backend.pid
echo $FRONTEND_PID > /tmp/aicrm_frontend.pid

echo ""
echo "🎉 AI CRM система успешно запущена!"
echo "📊 Backend (FastAPI): http://localhost:$PORT"
echo "🎨 Frontend (React): http://localhost:3000"
echo "📋 API Docs: http://localhost:$PORT/docs"
echo ""
echo "💡 Для остановки используйте: ./stop.sh"
echo ""
echo "📝 PID процессов сохранены в /tmp/aicrm_*.pid"
echo ""
echo "🔄 Для использования Turbopack запустите: ./start_turbo.sh"

# Ожидание завершения (Ctrl+C для остановки)
trap 'echo ""; echo "🛑 Получен сигнал остановки..."; ./stop.sh; exit 0' INT TERM
wait
