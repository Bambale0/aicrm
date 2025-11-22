#!/bin/bash
# Stop script for AI CRM application

echo "🛑 Остановка AI CRM системы..."

# Функция для остановки процесса
stop_process() {
    local pid_file=$1
    local name=$2

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 $pid 2>/dev/null; then
            echo "Останавливаю $name (PID: $pid)..."
            kill $pid
            # Ждем завершения процесса
            for i in {1..10}; do
                if ! kill -0 $pid 2>/dev/null; then
                    echo "✅ $name остановлен"
                    rm -f "$pid_file"
                    return 0
                fi
                sleep 1
            done
            # Принудительная остановка
            echo "⚠️  Принудительная остановка $name..."
            kill -9 $pid 2>/dev/null
            rm -f "$pid_file"
            echo "✅ $name принудительно остановлен"
        else
            echo "⚠️  $name уже остановлен (PID файл устарел)"
            rm -f "$pid_file"
        fi
    else
        echo "ℹ️  PID файл $name не найден"
    fi
}

# 1. Останавливаем backend
stop_process "/tmp/aicrm_backend.pid" "Backend (FastAPI)"

# 2. Останавливаем frontend
stop_process "/tmp/aicrm_frontend.pid" "Frontend (React)"

# 3. Проверяем и останавливаем оставшиеся процессы
echo "🔍 Проверка оставшихся процессов..."

# Ищем процессы uvicorn
uvicorn_pids=$(pgrep -f uvicorn)
if [ -n "$uvicorn_pids" ]; then
    echo "Найдены процессы uvicorn: $uvicorn_pids"
    kill $uvicorn_pids 2>/dev/null
    sleep 2
    kill -9 $uvicorn_pids 2>/dev/null
fi

# Ищем процессы react-scripts
react_pids=$(pgrep -f "react-scripts start")
if [ -n "$react_pids" ]; then
    echo "Найдены процессы React: $react_pids"
    kill $react_pids 2>/dev/null
    sleep 2
    kill -9 $react_pids 2>/dev/null
fi

# 4. Останавливаем сервисы системы (опционально)
read -p "Остановить системные сервисы (PostgreSQL, Redis, Nginx)? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🛑 Останавливаю системные сервисы..."

    # PostgreSQL
    if sudo systemctl is-active --quiet postgresql; then
        echo "Останавливаю PostgreSQL..."
        sudo systemctl stop postgresql
    fi

    # Redis
    if sudo systemctl is-active --quiet redis-server; then
        echo "Останавливаю Redis..."
        sudo systemctl stop redis-server
    fi

    # Nginx
    if sudo systemctl is-active --quiet nginx; then
        echo "Останавливаю Nginx..."
        sudo systemctl stop nginx
    fi
fi

echo ""
echo "🎉 AI CRM система остановлена!"
echo ""
echo "💡 Для запуска используйте: ./start.sh"
echo "📊 Для проверки статуса: ./status.sh"
