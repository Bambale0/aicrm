#!/bin/bash
# Test script for nginx configuration

echo "🧪 Тестирование nginx конфигурации AI CRM"
echo "=========================================="

# Тестирование локально (через nginx на порту 80)
echo "📍 Тестирование локального nginx (порт 80):"
BASE_URL_HTTP="http://localhost"

echo "1. Тестирование главной страницы (frontend):"
curl -s -o /dev/null -w "   HTTP %{http_code} - %{size_download} bytes\n" "$BASE_URL_HTTP/"

echo ""
echo "2. Тестирование API health (backend):"
curl -s -o /dev/null -w "   HTTP %{http_code} - %{size_download} bytes\n" "$BASE_URL_HTTP/health"

echo ""
echo "3. Тестирование API docs (backend):"
curl -s -o /dev/null -w "   HTTP %{http_code} - %{size_download} bytes\n" "$BASE_URL_HTTP/docs"

echo ""
echo "4. Тестирование AI endpoints (backend):"
curl -s -o /dev/null -w "   HTTP %{http_code} - %{size_download} bytes\n" "$BASE_URL_HTTP/ai/models"

echo ""
echo "5. Тестирование Telegram webhook (backend):"
curl -s -o /dev/null -w "   HTTP %{http_code} - %{size_download} bytes\n" "$BASE_URL_HTTP/telegram/webhook"

echo ""
echo "🔒 Тестирование HTTPS редиректа:"
curl -s -I "http://localhost/" | grep -E "(HTTP|Location)" || echo "   Редирект не настроен или сервер не отвечает"

echo ""
echo "✅ Тестирование завершено!"
echo ""
echo "🌐 Доступ к системе:"
echo "   Локальный frontend: http://localhost:3000 (React dev server)"
echo "   Через nginx: http://localhost (прокси к frontend/backend)"
echo "   HTTPS: https://dev.chilcreative.ru (с редиректом)"
echo ""
echo "📊 Статус компонентов:"
./status.sh
