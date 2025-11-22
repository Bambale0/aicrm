#!/bin/bash

set -e  # Выход при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Базовый URL API
BASE_URL="http://localhost:8000/api"

# Функция для вывода сообщения об успехе
success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Функция для вывода сообщения об ошибке
fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    exit 1
}

# Функция для вывода информационного сообщения
info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

# Проверка наличия curl
check_curl() {
    if ! command -v curl &> /dev/null; then
        fail "curl is required but not installed. Please install curl."
    fi
}

# Функция для выполнения HTTP запроса и проверки кода ответа
# Использование: http_request METHOD URL DATA [AUTH_TOKEN]
http_request() {
    local method=$1
    local url=$2
    local data=$3
    local token=$4

    local curl_cmd="curl -s -o response.txt -w '%{http_code}' -X $method $url"

    if [ ! -z "$data" ]; then
        curl_cmd="$curl_cmd -H 'Content-Type: application/json' -d '$data'"
    fi

    if [ ! -z "$token" ]; then
        curl_cmd="$curl_cmd -H 'Authorization: Bearer $token'"
    fi

    local status_code=$(eval $curl_cmd)
    echo $status_code
}

# Функция для проверки кода ответа
check_status() {
    local expected=$1
    local actual=$2
    local message=$3

    if [ "$actual" == "$expected" ]; then
        success "$message"
        return 0
    else
        fail "$message (expected $expected, got $actual)"
        return 1
    fi
}

# Функция для извлечения данных из ответа
get_response() {
    cat response.txt
}

# Начало тестирования
info "Starting API tests for AI CRM System"

# Проверяем наличие curl
check_curl

# 1. Health Check
info "1. Testing health check..."
status_code=$(http_request "GET" "$BASE_URL/health" "")
check_status 200 $status_code "Health check"

# 2. Получение списка моделей AI (публичный эндпоинт)
info "2. Testing AI models endpoint..."
status_code=$(http_request "GET" "$BASE_URL/ai/models" "")
check_status 200 $status_code "AI models list"

# 3. Аутентификация
info "3. Testing authentication..."
auth_data='{"email": "iloveigor@chillcreative.ru", "password": "25896311Aaa"}'
status_code=$(http_request "POST" "$BASE_URL/auth/login/json" "$auth_data")
check_status 200 $status_code "Authentication"

# Если аутентификация успешна, сохраняем токен
if [ $status_code -eq 200 ]; then
    token=$(get_response | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    if [ -z "$token" ]; then
        fail "Failed to extract access token"
    else
        success "Access token obtained"
    fi
else
    fail "Authentication failed, cannot continue"
fi

# 4. Получение информации о текущем пользователе
info "4. Testing current user endpoint..."
status_code=$(http_request "GET" "$BASE_URL/me" "" "$token")
check_status 200 $status_code "Current user"

# 5. Тестирование CRUD для клиентов
info "5. Testing customers CRUD..."

# 5.1 Создание клиента
info "5.1 Creating customer..."
customer_data='{"name": "Test Customer API", "email": "test.customer.api@example.com", "phone": "+1234567890"}'
status_code=$(http_request "POST" "$BASE_URL/customers/" "$customer_data" "$token")
check_status 200 $status_code "Create customer"

if [ $status_code -eq 200 ]; then
    customer_id=$(get_response | grep -o '"id":[0-9]*' | cut -d: -f2)
    success "Customer created with ID: $customer_id"
else
    fail "Failed to create customer, skipping further customer tests"
fi

# 5.2 Получение списка клиентов
info "5.2 Getting customers list..."
status_code=$(http_request "GET" "$BASE_URL/customers/" "" "$token")
check_status 200 $status_code "Get customers list"

# 5.3 Получение конкретного клиента
if [ ! -z "$customer_id" ]; then
    info "5.3 Getting customer by ID..."
    status_code=$(http_request "GET" "$BASE_URL/customers/$customer_id" "" "$token")
    check_status 200 $status_code "Get customer by ID"
fi

# 6. Тестирование заказов
info "6. Testing orders CRUD..."

# 6.1 Создание заказа
info "6.1 Creating order..."
order_data='{"customer_id": '$customer_id', "items": [{"product_type": "t-shirt", "quantity": 10, "size": "M", "color": "black"}], "requirements": "Test order from API", "source": "api_test"}'
status_code=$(http_request "POST" "$BASE_URL/orders/" "$order_data" "$token")
if [ $status_code -eq 200 ] || [ $status_code -eq 201 ]; then
    success "Create order"
    order_id=$(get_response | grep -o '"id":[0-9]*' | cut -d: -f2)
    success "Order created with ID: $order_id"
else
    fail "Create order (expected 200 or 201, got $status_code)"
fi

# 6.2 Получение списка заказов
info "6.2 Getting orders list..."
status_code=$(http_request "GET" "$BASE_URL/orders/" "" "$token")
check_status 200 $status_code "Get orders list"

# 7. Тестирование задач
info "7. Testing tasks CRUD..."

# 7.1 Создание задачи
info "7.1 Creating task..."
task_data='{"title": "Test Task API", "description": "This is a test task created via API", "priority": "high", "related_order_id": '$order_id'}'
status_code=$(http_request "POST" "$BASE_URL/tasks/" "$task_data" "$token")
check_status 200 $status_code "Create task"

if [ $status_code -eq 200 ]; then
    task_id=$(get_response | grep -o '"id":[0-9]*' | cut -d: -f2)
    success "Task created with ID: $task_id"
else
    fail "Failed to create task, skipping further task tests"
fi

# 7.2 Получение списка задач
info "7.2 Getting tasks list..."
status_code=$(http_request "GET" "$BASE_URL/tasks/" "" "$token")
check_status 200 $status_code "Get tasks list"

# 8. Тестирование AI анализа намерений
info "8. Testing AI intent analysis..."
ai_data='{"message": "I want to order 5 black t-shirts with my logo"}'
status_code=$(http_request "POST" "$BASE_URL/ai/analyze-intent" "$ai_data" "$token")
check_status 200 $status_code "AI intent analysis"

# 9. Тестирование AI чата
info "9. Testing AI chat..."
chat_data='{"messages": [{"role": "user", "content": "Hello, how can I help you?"}], "model": "deepseek/deepseek-chat-v3.1"}'
status_code=$(http_request "POST" "$BASE_URL/ai/chat" "$chat_data" "$token")
check_status 200 $status_code "AI chat"

# 10. Тестирование автоматизации
info "10. Testing automation..."

# 10.1 Получение списка процессов (пропускаем, так как эндпоинт не поддерживает GET)
info "10.1 Automation processes endpoint - GET method not supported (405), skipping..."

# 11. Тестирование email шаблонов
info "11. Testing email templates..."

# 11.1 Получение списка шаблонов
info "11.1 Getting email templates..."
status_code=$(http_request "GET" "$BASE_URL/email-templates/" "" "$token")
check_status 200 $status_code "Get email templates"

# 11.2 Создание шаблона
info "11.2 Creating email template..."
template_data='{"name": "test_template", "display_name": "Test Template", "subject_template": "Test Subject", "html_template": "Test body content", "text_template": "Test body content", "category": "general"}'
status_code=$(http_request "POST" "$BASE_URL/email-templates/" "$template_data" "$token")
check_status 200 $status_code "Create email template"

info "API testing completed successfully!"

# Удаляем временный файл ответа
rm -f response.txt
