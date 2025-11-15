#!/bin/bash
# Status script for AI CRM application

echo "📊 Статус AI CRM системы"
echo "========================"

# Функция для проверки статуса сервиса
check_service() {
    local name=$1
    local command=$2
    local port=$3

    echo -n "$name: "

    if eval "$command" >/dev/null 2>&1; then
        echo "✅ Запущен"
        if [ -n "$port" ]; then
            if nc -z localhost $port 2>/dev/null; then
                echo "   📡 Порт $port доступен"
            else
                echo "   ⚠️  Порт $port недоступен"
            fi
        fi
    else
        echo "❌ Остановлен"
    fi
}

# 1. PostgreSQL
check_service "PostgreSQL" "pg_isready -h localhost -p 5432"

# 2. Redis
check_service "Redis" "redis-cli ping"

# 3. Backend (FastAPI)
if [ -f /tmp/aicrm_backend.pid ]; then
    BACKEND_PID=$(cat /tmp/aicrm_backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo "Backend (FastAPI): ✅ Запущен (PID: $BACKEND_PID)"
        check_service "  " "nc -z localhost 8000" "8000"
    else
        echo "Backend (FastAPI): ❌ PID файл существует, но процесс не найден"
    fi
else
    check_service "Backend (FastAPI)" "pgrep -f uvicorn"
fi

# 4. Frontend (React)
if [ -f /tmp/aicrm_frontend.pid ]; then
    FRONTEND_PID=$(cat /tmp/aicrm_frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "Frontend (React): ✅ Запущен (PID: $FRONTEND_PID)"
        check_service "  " "nc -z localhost 3000" "3000"
    else
        echo "Frontend (React): ❌ PID файл существует, но процесс не найден"
    fi
else
    check_service "Frontend (React)" "pgrep -f 'react-scripts start'"
fi

# 5. Nginx
check_service "Nginx" "sudo systemctl is-active nginx"

echo ""
echo "📁 PID файлы:"
if [ -f /tmp/aicrm_backend.pid ]; then
    echo "   Backend: $(cat /tmp/aicrm_backend.pid)"
else
    echo "   Backend: файл не найден"
fi

if [ -f /tmp/aicrm_frontend.pid ]; then
    echo "   Frontend: $(cat /tmp/aicrm_frontend.pid)"
else
    echo "   Frontend: файл не найден"
fi

echo ""
echo "🌐 Доступные URL:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"

echo ""
echo "💡 Команды управления:"
echo "   Запуск:  ./start.sh"
echo "   Остановка: ./stop.sh"
echo "   Статус:  ./status.sh"
