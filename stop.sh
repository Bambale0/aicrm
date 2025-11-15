#!/bin/bash
# Stop script for AI CRM application

echo "🛑 Остановка AI CRM системы..."

# Функция для корректной остановки процесса
stop_process() {
    local pid=$1
    local name=$2

    if [ -n "$pid" ] && kill -0 $pid 2>/dev/null; then
        echo "🔄 Остановка $name (PID: $pid)..."
        kill $pid 2>/dev/null

        # Ожидание завершения процесса
        local count=0
        while kill -0 $pid 2>/dev/null && [ $count -lt 10 ]; do
            sleep 1
            count=$((count + 1))
        done

        if kill -0 $pid 2>/dev/null; then
            echo "⚠️  Принудительная остановка $name..."
            kill -9 $pid 2>/dev/null
        fi

        echo "✅ $name остановлен"
    else
        echo "ℹ️  $name уже остановлен или не найден"
    fi
}

# 1. Остановка frontend (React)
if [ -f /tmp/aicrm_frontend.pid ]; then
    FRONTEND_PID=$(cat /tmp/aicrm_frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        stop_process $FRONTEND_PID "Frontend (React)"
    else
        echo "ℹ️  Frontend PID $FRONTEND_PID не найден, поиск по имени..."
        # Найти и остановить процессы React
        REACT_PIDS=$(ps aux | grep -E "(react-scripts|node.*start.js)" | grep -v grep | awk '{print $2}')
        if [ -n "$REACT_PIDS" ]; then
            echo "🔄 Остановка React процессов: $REACT_PIDS"
            kill -TERM $REACT_PIDS 2>/dev/null || kill -KILL $REACT_PIDS 2>/dev/null
            echo "✅ React процессы остановлены"
        else
            echo "ℹ️  Процессы React не найдены"
        fi
    fi
    rm -f /tmp/aicrm_frontend.pid
else
    echo "🔍 Поиск процессов React..."
    REACT_PIDS=$(ps aux | grep -E "(react-scripts|node.*start.js)" | grep -v grep | awk '{print $2}')
    if [ -n "$REACT_PIDS" ]; then
        echo "🔄 Остановка React процессов: $REACT_PIDS"
        kill -TERM $REACT_PIDS 2>/dev/null || kill -KILL $REACT_PIDS 2>/dev/null
        echo "✅ React процессы остановлены"
    else
        echo "ℹ️  Процессы React не найдены"
    fi
fi

# 2. Остановка backend (FastAPI)
if [ -f /tmp/aicrm_backend.pid ]; then
    BACKEND_PID=$(cat /tmp/aicrm_backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        stop_process $BACKEND_PID "Backend (FastAPI)"
    else
        echo "ℹ️  Backend PID $BACKEND_PID не найден, поиск по имени..."
        # Найти и остановить процессы uvicorn/python
        BACKEND_PIDS=$(ps aux | grep -E "(uvicorn|python.*main.py)" | grep -v grep | awk '{print $2}')
        if [ -n "$BACKEND_PIDS" ]; then
            echo "🔄 Остановка backend процессов: $BACKEND_PIDS"
            kill -TERM $BACKEND_PIDS 2>/dev/null || kill -KILL $BACKEND_PIDS 2>/dev/null
            echo "✅ Backend процессы остановлены"
        else
            echo "ℹ️  Процессы backend не найдены"
        fi
    fi
    rm -f /tmp/aicrm_backend.pid
else
    echo "🔍 Поиск процессов backend..."
    BACKEND_PIDS=$(ps aux | grep -E "(uvicorn|python.*main.py)" | grep -v grep | awk '{print $2}')
    if [ -n "$BACKEND_PIDS" ]; then
        echo "🔄 Остановка backend процессов: $BACKEND_PIDS"
        kill -TERM $BACKEND_PIDS 2>/dev/null || kill -KILL $BACKEND_PIDS 2>/dev/null
        echo "✅ Backend процессы остановлены"
    else
        echo "ℹ️  Процессы backend не найдены"
    fi
fi

# 3. Остановка Nginx (только если он был запущен нами, не системный)
echo "🌐 Проверка Nginx..."
# Nginx обычно является системным сервисом, поэтому не останавливаем его автоматически
# sudo systemctl stop nginx  # Раскомментируйте если нужно останавливать Nginx

# 4. Очистка временных файлов
echo "🧹 Очистка временных файлов..."
rm -f /tmp/aicrm_*.pid

echo ""
echo "🎉 AI CRM система успешно остановлена!"
echo ""
echo "💡 Для запуска используйте: ./start.sh"
