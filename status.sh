#!/bin/bash
# Status script for AI CRM application

# Цветовые коды для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo "📊 ${BLUE}СТАТУС AI CRM СИСТЕМЫ${NC}"
echo "====================================="

# Определение режима запуска
check_run_mode() {
    if docker ps --format "table {{.Names}}" 2>/dev/null | grep -q "aicrm_"; then
        echo "🐳 Режим запуска: ${GREEN}Docker Compose${NC}"
        RUN_MODE="docker"
    elif pgrep -f "uvicorn\|react-scripts\|serve" >/dev/null 2>&1; then
        echo "🏠 Режим запуска: ${GREEN}Процессы на хосте${NC}"
        RUN_MODE="host"
    else
        echo "❓ Режим запуска: ${YELLOW}Не определен (система не запущена)${NC}"
        RUN_MODE="none"
    fi
    echo ""
}

# Функция для проверки статуса сервиса (хост режим)
check_service() {
    local name=$1
    local command=$2
    local port=$3

    echo -n "$name: "

    if eval "$command" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Запущен${NC}"
        if [ -n "$port" ]; then
            if timeout 5 bash -c "echo >/dev/tcp/localhost/$port" 2>/dev/null; then
                echo -e "   📡 Порт $port ${GREEN}доступен${NC}"
            else
                echo -e "   ⚠️  Порт $port ${RED}недоступен${NC}"
            fi
        fi
    else
        echo -e "${RED}❌ Остановлен${NC}"
    fi
}

# Проверка Docker контейнера
check_docker_container() {
    local container_name=$1
    local display_name=$2
    local port=$3

    echo -n "$display_name: "

    local status=$(docker ps --filter "name=$container_name" --format "{{.Status}}" 2>/dev/null)
    local health=$(docker inspect $container_name --format "{{.State.Health.Status}}" 2>/dev/null)

    if [ -n "$status" ] && [[ $status != *"Exited"* ]]; then
        echo -e "${GREEN}✅ Запущен${NC}"

        # Показать статус здоровья если есть
        if [ "$health" = "healthy" ]; then
            echo -e "   🏥 Health check: ${GREEN}healthy${NC}"
        elif [ "$health" = "unhealthy" ]; then
            echo -e "   🏥 Health check: ${RED}unhealthy${NC}"
        fi

        if [ -n "$port" ]; then
            if timeout 5 bash -c "echo >/dev/tcp/localhost/$port" 2>/dev/null; then
                echo -e "   📡 Порт $port ${GREEN}доступен${NC}"
            else
                echo -e "   ⚠️  Порт $port ${RED}недоступен${NC}"
            fi
        fi
    else
        echo -e "${RED}❌ Остановлен${NC}"
    fi
}

# Определение режима запуска
check_run_mode

if [ "$RUN_MODE" = "docker" ]; then
    echo "${BLUE}🔍 Проверка Docker контейнеров:${NC}"
    echo "---------------------------------"

    # 1. PostgreSQL
    check_docker_container "aicrm_postgres" "PostgreSQL" ""

    # 2. Redis
    check_docker_container "aicrm_redis" "Redis" ""

    # Проверка Redis подключения через Docker
    if docker exec aicrm_redis redis-cli ping >/dev/null 2>&1; then
        echo "   📊 Redis статистика:"
        docker exec aicrm_redis redis-cli info server | grep -E "(redis_version|uptime_in_days|connected_clients)" | sed 's/^/      /' || true
    fi

    # 3. Backend (FastAPI)
    check_docker_container "aicrm_backend" "Backend (FastAPI)" "8000"

    # Проверка health endpoints для Docker
    if timeout 5 bash -c "echo >/dev/tcp/localhost/8000" 2>/dev/null; then
        echo "   🏥 Health checks:"
        if curl -s -f --max-time 5 http://localhost:8000/health >/dev/null 2>&1; then
            echo -e "      ✅ /health - ${GREEN}OK${NC}"
        else
            echo -e "      ❌ /health - ${RED}FAILED${NC}"
        fi

        if curl -s -f --max-time 5 http://localhost:8000/health/detailed >/dev/null 2>&1; then
            echo -e "      ✅ /health/detailed - ${GREEN}OK${NC}"
        else
            echo -e "      ❌ /health/detailed - ${RED}FAILED${NC}"
        fi

        if curl -s -f --max-time 5 http://localhost:8000/metrics >/dev/null 2>&1; then
            echo -e "      ✅ /metrics - ${GREEN}OK${NC}"
        else
            echo -e "      ❌ /metrics - ${RED}FAILED${NC}"
        fi
    fi

    # 4. Frontend (React)
    check_docker_container "aicrm_frontend" "Frontend (React)" ""

    # 5. Nginx
    check_docker_container "aicrm_nginx" "Nginx" "80 443"

elif [ "$RUN_MODE" = "host" ]; then
    echo "${BLUE}🔍 Проверка процессов на хосте:${NC}"
    echo "----------------------------------"

    # 1. PostgreSQL
    check_service "PostgreSQL" "pg_isready -h localhost -p 5432"

    # 2. Redis
    check_service "Redis" "redis-cli ping"

    # Проверка Redis подключения
    if redis-cli ping >/dev/null 2>&1; then
        echo "   📊 Redis статистика:"
        redis-cli info server | grep -E "(redis_version|uptime_in_days|connected_clients)" | sed 's/^/      /' || true
    fi

    # 3. Backend (FastAPI)
    if [ -f /tmp/aicrm_backend.pid ]; then
        BACKEND_PID=$(cat /tmp/aicrm_backend.pid)
        if kill -0 $BACKEND_PID 2>/dev/null; then
            echo -e "Backend (FastAPI): ${GREEN}✅ Запущен${NC} (PID: $BACKEND_PID)"
            check_service "  " "timeout 5 bash -c 'echo >/dev/tcp/localhost/8000'" "8000"

            # Проверка health endpoints
            echo "   🏥 Health checks:"
            if curl -s -f --max-time 5 http://localhost:8000/health >/dev/null 2>&1; then
                echo -e "      ✅ /health - ${GREEN}OK${NC}"
            else
                echo -e "      ❌ /health - ${RED}FAILED${NC}"
            fi

            if curl -s -f --max-time 5 http://localhost:8000/health/detailed >/dev/null 2>&1; then
                echo -e "      ✅ /health/detailed - ${GREEN}OK${NC}"
            else
                echo -e "      ❌ /health/detailed - ${RED}FAILED${NC}"
            fi

            if curl -s -f --max-time 5 http://localhost:8000/metrics >/dev/null 2>&1; then
                echo -e "      ✅ /metrics - ${GREEN}OK${NC}"
            else
                echo -e "      ❌ /metrics - ${RED}FAILED${NC}"
            fi
        else
            echo -e "Backend (FastAPI): ${RED}❌ PID файл существует, но процесс не найден${NC}"
        fi
    else
        check_service "Backend (FastAPI)" "pgrep -f uvicorn"
    fi

    # 4. Frontend (React)
    if [ -f /tmp/aicrm_frontend.pid ]; then
        FRONTEND_PID=$(cat /tmp/aicrm_frontend.pid)
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            echo -e "Frontend (React): ${GREEN}✅ Запущен${NC} (PID: $FRONTEND_PID)"
            check_service "  " "timeout 5 bash -c 'echo >/dev/tcp/localhost/3000'" "3000"
        else
            echo -e "Frontend (React): ${RED}❌ PID файл существует, но процесс не найден${NC}"
        fi
    else
        check_service "Frontend (React)" "pgrep -f 'react-scripts start\|vite'"
    fi

    # 5. Nginx
    check_service "Nginx" "sudo systemctl is-active nginx"

    echo ""
    echo "${BLUE}📁 PID файлы:${NC}"
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
fi

echo ""
echo "${BLUE}🔗 Доступные URL:${NC}"
echo "   Frontend:    http://localhost:3000"
echo "   Backend:     http://localhost:8000"
echo "   API Docs:    http://localhost:8000/docs"
echo "   Health:      http://localhost:8000/health"
echo "   Metrics:     http://localhost:8000/metrics"
echo "   Workflow:    http://localhost:8000/api/workflow/workflows"

echo ""
echo "${BLUE}🔧 Интеграции и сервисы:${NC}"

# Проверка Telegram бота
echo -n "Telegram Bot: "
if stats=$(curl -s --max-time 5 http://localhost:8000/api/telegram/stats 2>/dev/null); then
    if echo "$stats" | grep -q '"bot_running":true'; then
        echo -e "${GREEN}✅ Запущен${NC}"
    elif echo "$stats" | grep -q '"bot_running":false'; then
        echo -e "${YELLOW}⚠️  Настроен, но не запущен${NC}"
    else
        echo -e "${BLUE}ℹ️  Настроен${NC}"
    fi
else
    echo -e "${RED}❌ Не настроен или недоступен${NC}"
fi

# Проверка Email сервиса
echo -n "Email Service: "
if health_data=$(curl -s --max-time 5 http://localhost:8000/health/detailed 2>/dev/null); then
    if echo "$health_data" | grep -q '"email_service":"configured"'; then
        echo -e "${GREEN}✅ Настроен${NC}"
    else
        echo -e "${YELLOW}⚠️  Не настроен${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Недоступен${NC}"
fi

# Проверка Avito интеграции
echo -n "Avito Integration: "
if curl -s -f --max-time 5 http://localhost:8000/api/avito/background/tasks >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Доступна${NC}"
else
    echo -e "${YELLOW}⚠️  Не настроена или недоступна${NC}"
fi

echo ""
echo "${BLUE}💡 Команды управления:${NC}"
echo "   Запуск (хост):   ./start.sh"
echo "   Запуск (Turbo):  ./start_turbo.sh"
echo "   Запуск (Docker): docker-compose -f docker-compose.prod.yml up -d"
echo "   Остановка:       ./stop.sh"
echo "   Статус:          ./status.sh"
echo ""
echo "${CYAN}📊 Тестирование:${NC}"
echo "   API тесты:       ./test_api.sh"
echo "   Комплексные:     python3 test_api_comprehensive.py"
echo ""
echo "${PURPLE}🛠️  Мониторинг:${NC}"
echo "   Логи Backend:    tail -f /var/log/aicrm/backend.log"
echo "   Логи Frontend:   tail -f /var/log/aicrm/frontend.log"
echo "   Системные логи:  journalctl -u aicrm -f"
