#!/bin/bash

echo "🧪 Комплексное тестирование API AI CRM"
echo "======================================"

BASE_URL="http://localhost:8000"
TEST_RESULTS=()

# Функция для тестирования endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local expected_code=${3:-200}
    local description=$4

    echo -n "🔍 Тестирую $description ($method $endpoint)... "

    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "HTTPSTATUS:%{http_code}" "$BASE_URL$endpoint")
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST -H "Content-Type: application/json" "$BASE_URL$endpoint")
    fi

    http_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')

    if [ "$http_code" = "$expected_code" ]; then
        echo "✅ $http_code"
        TEST_RESULTS+=("✅ $description")
    else
        echo "❌ $http_code (ожидался $expected_code)"
        TEST_RESULTS+=("❌ $description - код $http_code")
    fi
}

echo ""
echo "🏥 СИСТЕМНЫЕ ENDPOINTS:"
echo "----------------------"
test_endpoint "GET" "/health" "200" "Системное здоровье"
test_endpoint "GET" "/status" "200" "Статус AI"

echo ""
echo "🔐 АУТЕНТИФИКАЦИЯ:"
echo "------------------"
test_endpoint "POST" "/auth/login" "422" "Логин без данных (ожидается валидационная ошибка)"
test_endpoint "GET" "/auth/me" "401" "Текущий пользователь без токена"

echo ""
echo "👥 ПОЛЬЗОВАТЕЛИ:"
echo "---------------"
test_endpoint "GET" "/users/" "401" "Список пользователей"
test_endpoint "GET" "/users/1" "401" "Пользователь по ID"

echo ""
echo "👨‍💼 КЛИЕНТЫ:"
echo "-------------"
test_endpoint "GET" "/customers/" "401" "Список клиентов"
test_endpoint "GET" "/customers/1" "401" "Клиент по ID"

echo ""
echo "📦 ЗАКАЗЫ:"
echo "----------"
test_endpoint "GET" "/orders/" "401" "Список заказов"
test_endpoint "GET" "/orders/1" "401" "Заказ по ID"

echo ""
echo "📋 ЗАДАЧИ:"
echo "----------"
test_endpoint "GET" "/tasks/" "401" "Список задач"
test_endpoint "GET" "/tasks/1" "401" "Задача по ID"

echo ""
echo "💬 КОММУНИКАЦИИ:"
echo "----------------"
test_endpoint "GET" "/communications/" "401" "История коммуникаций"

echo ""
echo "🤖 AI MANAGER:"
echo "-------------"
test_endpoint "GET" "/ai-manager/prompts" "401" "AI промпты"
test_endpoint "GET" "/models" "200" "AI модели"
test_endpoint "GET" "/usage/monthly" "200" "Использование AI"

echo ""
echo "⚙️ АВТОМАТИЗАЦИЯ:"
echo "----------------"
test_endpoint "GET" "/automation/processes" "401" "Процессы автоматизации"
test_endpoint "GET" "/automation/stages/" "401" "Стадии процессов"
test_endpoint "GET" "/automation/triggers/" "401" "Триггеры"
test_endpoint "GET" "/automation/robots/" "401" "Роботы"

echo ""
echo "📧 EMAIL:"
echo "--------"
test_endpoint "GET" "/email/status" "401" "Статус email"
test_endpoint "GET" "/email/templates" "401" "Email шаблоны"

echo ""
echo "📱 TELEGRAM:"
echo "-----------"
test_endpoint "GET" "/telegram/chats" "401" "Telegram чаты"

echo ""
echo "📄 ДОКУМЕНТАЦИЯ:"
echo "---------------"
test_endpoint "GET" "/docs" "200" "Swagger UI"
test_endpoint "GET" "/openapi.json" "200" "OpenAPI спецификация"

echo ""
echo "📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:"
echo "=========================="

success_count=0
total_count=0

for result in "${TEST_RESULTS[@]}"; do
    echo "$result"
    ((total_count++))
    if [[ $result == ✅* ]]; then
        ((success_count++))
    fi
done

echo ""
echo "📈 СТАТИСТИКА:"
echo "=============="
echo "✅ Успешных тестов: $success_count/$total_count"
echo "❌ Неудачных тестов: $((total_count - success_count))/$total_count"
echo "📊 Процент успеха: $((success_count * 100 / total_count))%"

if [ $success_count -eq $total_count ]; then
    echo ""
    echo "🎉 ВСЕ API ENDPOINTS РАБОТАЮТ КОРРЕКТНО!"
else
    echo ""
    echo "⚠️  ОБНАРУЖЕНЫ ПРОБЛЕМЫ С API ENDPOINTS"
fi
