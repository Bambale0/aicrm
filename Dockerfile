FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

WORKDIR /app

COPY backend/pyproject.toml /app/backend/pyproject.toml
COPY backend/src /app/backend/src

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir /app/backend

RUN groupadd --system appuser && useradd --system --gid appuser appuser && \
    chown -R appuser:appuser /app

USER appuser
WORKDIR /app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/ready', timeout=3).read()" || exit 1

CMD ["uvicorn", "aicrm.main:app", "--host", "0.0.0.0", "--port", "8000"]
