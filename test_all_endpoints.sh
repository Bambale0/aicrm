#!/bin/bash

# Тестирование всех API эндпоинтов

TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJpbG92ZWlnb3JAY2hpbGxjcmVhdGl2ZS5ydSIsImV4cCI6MTc2ODMwMjc1MX0.c2To5JRYcAkbo4Z4PiOOynXYOY_9y5qx1sQtzE7ZKH4"
BASE_URL="http://127.0.0.1:8000"

echo "🔍 Начинаем тестирование всех эндпоинтов..."
echo "========================================"

# Функция для тестирования эндпоинта
test_endpoint() {
    local method=$1
    local url=$2
    local data=$3
    local expected_code=${4:-200}

    echo -n "Тестируем $method $url ... "

    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "%{http_code}" -H "Authorization: Bearer $TOKEN" "$BASE_URL$url")
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "%{http_code}" -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "$data" "$BASE_URL$url")
    elif [ "$method" = "PUT" ]; then
        response=$(curl -s -w "%{http_code}" -X PUT -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "$data" "$BASE_URL$url")
    fi

    http_code=$(echo "$response" | tail -c 4)
    response_body=$(echo "$response" | head -n -1)

    if [ "$http_code" = "$expected_code" ]; then
        echo "✅ OK ($http_code)"
    else
        echo "❌ FAIL ($http_code) - ожидалось $expected_code"
        echo "Response: $response_body"
    fi
}

# Тестирование основных эндпоинтов
echo "🏥 Здоровье системы:"
test_endpoint "GET" "/health" "" 200
test_endpoint "GET" "/api/health" "" 200
test_endpoint "GET" "/health/detailed" "" 200

echo ""
echo "🔐 Аутентификация:"
test_endpoint "GET" "/auth/me" "" 200

echo ""
echo "👤 Пользователи:"
test_endpoint "GET" "/users" "" 200

echo ""
echo "⚙️ Личный кабинет:"
test_endpoint "GET" "/api/user/settings" "" 200
test_endpoint "GET" "/api/user/profile" "" 200
test_endpoint "PUT" "/api/user/settings" '{"theme":"light"}' 200

echo ""
echo "🤖 AI:"
test_endpoint "GET" "/ai/status" "" 200
test_endpoint "POST" "/ai/chat" '{"messages":[{"role":"user","content":"Hello"}]}' 200

echo ""
echo "📊 Аналитика:"
test_endpoint "GET" "/ai/usage" "" 200
test_endpoint "GET" "/ai/usage/history" "" 200

echo ""
echo "👥 Клиенты:"
test_endpoint "GET" "/customers" "" 200
test_endpoint "POST" "/customers" '{"name":"Test Customer","email":"test@example.com"}' 201

echo ""
echo "📋 Задачи:"
test_endpoint "GET" "/tasks" "" 200
test_endpoint "POST" "/tasks" '{"title":"Test Task","description":"Test description"}' 201

echo ""
echo "💬 Коммуникации:"
test_endpoint "GET" "/communications" "" 200

echo ""
echo "🛒 Заказы:"
test_endpoint "GET" "/orders" "" 200

echo ""
echo "🏭 Производство:"
test_endpoint "GET" "/production/steps" "" 200

echo ""
echo "📦 Каталог:"
test_endpoint "GET" "/catalog/categories" "" 200
test_endpoint "GET" "/catalog/products" "" 200
test_endpoint "GET" "/catalog/services" "" 200

echo ""
echo "🤖 Автоматизация:"
test_endpoint "GET" "/automation/processes" "" 200
test_endpoint "GET" "/automation/triggers" "" 200

echo ""
echo "📧 Email:"
test_endpoint "GET" "/email/templates" "" 200

echo ""
echo "✈️ Telegram:"
test_endpoint "GET" "/telegram/settings" "" 200

echo ""
echo "🏠 Avito:"
test_endpoint "GET" "/avito/settings" "" 200

echo ""
echo "🏢 Организации:"
test_endpoint "GET" "/organizations" "" 200

echo ""
echo "📈 Кампании:"
test_endpoint "GET" "/campaigns" "" 200

echo ""
echo "🔌 Плагины:"
test_endpoint "GET" "/api/plugins" "" 200

echo ""
echo "⚙️ Системные настройки:"
test_endpoint "GET" "/settings/system/general" "" 200

echo ""
echo "========================================"
echo "🎉 Тестирование завершено!"