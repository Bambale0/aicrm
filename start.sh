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

# 3. Запуск backend (FastAPI)
echo "🔧 Запуск backend (FastAPI)..."
cd /root/aicrm/src || { echo "❌ Не удалось перейти в директорию /root/aicrm/src"; exit 1; }

# Установка переменных окружения для backend
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-8000}

# Запуск FastAPI в фоне
python3 -c "from aicrm.main import app; import uvicorn; uvicorn.run(app, host='${HOST}', port=${PORT})" &
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
npm start &
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
echo "📊 Backend: http://localhost:$PORT"
echo "🎨 Frontend: http://localhost:3000"
echo "📋 API Docs: http://localhost:$PORT/docs"
echo ""
echo "💡 Для остановки используйте: ./stop.sh"
echo ""
echo "📝 PID процессов сохранены в /tmp/aicrm_*.pid"

# Ожидание завершения (Ctrl+C для остановки)
trap 'echo ""; echo "🛑 Получен сигнал остановки..."; ./stop.sh; exit 0' INT TERM
wait
