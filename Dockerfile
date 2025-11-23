# Многоступенчатый Dockerfile для оптимизации размера образа

# Этап 1: Сборка зависимостей
FROM python:3.11-slim as builder

# Установка системных зависимостей для сборки
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Создание виртуального окружения
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Копирование и установка зависимостей Python
WORKDIR /app
COPY backend/pyproject.toml .
RUN pip install --upgrade pip && \
    pip install -e . && \
    pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Этап 2: Финальный образ
FROM python:3.11-slim as runtime

# Установка системных зависимостей для runtime
RUN apt-get update && apt-get install -y \
    # Для работы с SQLite
    #sqlite3 \
    # Для работы с PostgreSQL (если понадобится)
    libpq-dev \
    # Для работы с изображениями (если понадобится)
    libjpeg-dev libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Создание непривилегированного пользователя
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Копирование виртуального окружения из этапа сборки
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Создание директории приложения
WORKDIR /app

# Копирование исходного кода (из backend/src)
COPY backend/src/ ./src/

# Создание директории для данных
RUN mkdir -p /app/data && \
    chown -R appuser:appuser /app

# Переключение на непривилегированного пользователя
USER appuser

# Настройка переменных окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONHASHSEED=random

# Экспорт порта
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Запуск приложения
CMD ["uvicorn", "src.aicrm.main:app", "--host", "0.0.0.0", "--port", "8000"]
