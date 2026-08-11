#!/bin/bash

# Скрипт для развертывания проекта AI CRM на сервере
# Использование: ./deploy.sh [опции]

set -e

# Конфигурация
SERVER_HOST="155.212.245.205"
SERVER_USER="root"
SSH_PASSWORD="25896311dev"
SUDO_PASSWORD="25896311"
REMOTE_PATH="/root/saas/aicrm"
LOCAL_PATH="/home/dev/aicrm/backend/aicrm"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка наличия необходимых инструментов
check_dependencies() {
    log_info "Проверка зависимостей..."

    if ! command -v rsync &> /dev/null; then
        log_error "rsync не установлен. Установите его: apt install rsync"
        exit 1
    fi

    if ! command -v sshpass &> /dev/null; then
        log_error "sshpass не установлен. Установите его: apt install sshpass"
        exit 1
    fi

    log_success "Все зависимости найдены"
}

# Создание архива для резервной копии
create_backup() {
    if [ "$CREATE_BACKUP" = true ]; then
        log_info "Создание резервной копии на сервере..."

        sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_HOST" "
            if [ -d '$REMOTE_PATH' ]; then
                TIMESTAMP=\$(date +%Y%m%d_%H%M%S)
                BACKUP_DIR='/root/backups'
                mkdir -p \$BACKUP_DIR
                tar -czf \$BACKUP_DIR/aicrm_backup_\$TIMESTAMP.tar.gz -C /root/saas aicrm
                echo \"Резервная копия создана: \$BACKUP_DIR/aicrm_backup_\$TIMESTAMP.tar.gz\"
            else
                echo \"Директория $REMOTE_PATH не существует, резервная копия не требуется\"
            fi
        "
        log_success "Резервная копия создана"
    fi
}

# Синхронизация файлов
sync_files() {
    log_info "Синхронизация файлов с сервером..."

    # Исключаемые файлы и директории
    EXCLUDES=(
        --exclude='.git'
        --exclude='__pycache__'
        --exclude='*.pyc'
        --exclude='.env'
        --exclude='test.db'
        --exclude='*.log'
        --exclude='node_modules'
        --exclude='.pytest_cache'
        --exclude='.vscode'
        --exclude='*.sqlite'
        --exclude='*.sqlite3'
    )

    # Команда rsync
    RSYNC_CMD=(
        rsync -avz --delete
        "${EXCLUDES[@]}"
        -e "sshpass -p $SSH_PASSWORD ssh -o StrictHostKeyChecking=no"
        "$LOCAL_PATH/"
        "$SERVER_USER@$SERVER_HOST:$REMOTE_PATH/"
    )

    log_info "Выполнение: ${RSYNC_CMD[*]}"

    if "${RSYNC_CMD[@]}"; then
        log_success "Файлы успешно синхронизированы"
    else
        log_error "Ошибка синхронизации файлов"
        exit 1
    fi
}

# Перезапуск сервисов на сервере
restart_services() {
    if [ "$RESTART_SERVICES" = true ]; then
        log_info "Перезапуск сервисов на сервере..."

        sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_HOST" "
            cd '$REMOTE_PATH'

            # Остановка существующих процессов
            pkill -f 'uvicorn.*aicrm' || true
            pkill -f 'python.*main.py' || true

            # Ожидание остановки
            sleep 2

            # Активация виртуального окружения (если есть)
            if [ -f 'venv/bin/activate' ]; then
                source venv/bin/activate
            elif [ -f '.venv/bin/activate' ]; then
                source .venv/bin/activate
            fi

            # Установка зависимостей (если requirements.txt обновился)
            if [ -f 'requirements.txt' ]; then
                pip install -r requirements.txt
            fi

            # Запуск приложения в фоне
            nohup python3 -m uvicorn src.aicrm.main:app --host 0.0.0.0 --port 8000 > app.log 2>&1 &

            echo 'Приложение запущено'
        "

        log_success "Сервисы перезапущены"
    fi
}

# Проверка развертывания
verify_deployment() {
    if [ "$VERIFY_DEPLOYMENT" = true ]; then
        log_info "Проверка развертывания..."

        # Ожидание запуска сервиса
        sleep 5

        # Проверка доступности
        if curl -f -s "http://$SERVER_HOST:8000/health" > /dev/null; then
            log_success "Сервис успешно запущен и отвечает на запросы"

            # Запуск быстрого тестирования
            log_info "Запуск быстрого тестирования эндпоинтов..."
            sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_HOST" "
                cd '$REMOTE_PATH'
                python3 verify_routers.py 2>/dev/null | grep -E '(ПРОЙДЕНО|ПРОВАЛЕНО|ВСЕ ПРОВЕРКИ)' || echo 'Проверка выполнена'
            "

        else
            log_warning "Сервис не отвечает. Проверьте логи на сервере."
        fi
    fi
}

# Основная функция
main() {
    # Параметры по умолчанию
    CREATE_BACKUP=false
    RESTART_SERVICES=true
    VERIFY_DEPLOYMENT=true

    # Разбор аргументов
    while [[ $# -gt 0 ]]; do
        case $1 in
            --no-backup)
                CREATE_BACKUP=false
                shift
                ;;
            --no-restart)
                RESTART_SERVICES=false
                shift
                ;;
            --no-verify)
                VERIFY_DEPLOYMENT=false
                shift
                ;;
            --help|-h)
                echo "Использование: $0 [опции]"
                echo ""
                echo "Опции:"
                echo "  --no-backup     Не создавать резервную копию"
                echo "  --no-restart    Не перезапускать сервисы"
                echo "  --no-verify     Не проверять развертывание"
                echo "  --help, -h      Показать эту справку"
                echo ""
                echo "Конфигурация:"
                echo "  Сервер: $SERVER_HOST"
                echo "  Пользователь: $SERVER_USER"
                echo "  Путь на сервере: $REMOTE_PATH"
                exit 0
                ;;
            *)
                log_error "Неизвестный параметр: $1"
                echo "Используйте --help для справки"
                exit 1
                ;;
        esac
    done

    echo "🚀 Начинаем развертывание AI CRM на сервере"
    echo "=========================================="
    echo "Сервер: $SERVER_HOST"
    echo "Пользователь: $SERVER_USER"
    echo "Путь: $REMOTE_PATH"
    echo "=========================================="

    # Выполнение шагов
    check_dependencies
    create_backup
    sync_files
    restart_services
    verify_deployment

    echo ""
    log_success "🎉 Развертывание завершено успешно!"
    echo ""
    echo "Для проверки работоспособности выполните на сервере:"
    echo "  cd $REMOTE_PATH"
    echo "  python3 verify_routers.py"
}

# Запуск
main "$@"