#!/bin/bash
# Script to create ngrok tunnel for backend access from external devices

echo "🚀 Запуск ngrok туннеля для backend..."

# Check if backend is running
if ! nc -z localhost 8000 2>/dev/null; then
    echo "❌ Backend не запущен на порту 8000"
    echo "Сначала запустите backend: ./start.sh"
    exit 1
fi

echo "✅ Backend доступен на localhost:8000"

# Start ngrok tunnel
echo "🌐 Запуск ngrok туннеля..."
./ngrok http 8000

echo ""
echo "💡 Используйте предоставленный ngrok URL для доступа к backend с других устройств"
echo "💡 Для авторизации добавьте ngrok URL в CORS_ORIGINS в .env файле"
echo "   Пример: CORS_ORIGINS=http://localhost:3000,https://abc123.ngrok.io"
