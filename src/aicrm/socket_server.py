"""
Отдельный Socket.IO сервер для real-time коммуникаций
Запускается в отдельном процессе от основного FastAPI приложения
"""

import socketio

from .core.config import settings
from .utils.logging import get_logger

logger = get_logger(__name__)

# Socket.IO интеграция для совместимости с клиентскими библиотеками
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=settings.debug,
    engineio_logger=settings.debug,
    allow_upgrades=True,
    transports=["polling", "websocket"],
    ping_timeout=60000,
    ping_interval=25000,
    upgrade_timeout=10000,
    max_http_buffer_size=1024 * 1024,
)


# Socket.IO обработчики событий
@sio.event
async def connect(sid, environ, auth):
    """Обработка подключения клиента Socket.IO"""
    logger.info(f"Socket.IO client connected: {sid}")
    await sio.emit("welcome", {"message": "Connected to AI CRM WebSocket"}, to=sid)


@sio.event
async def disconnect(sid):
    """Обработка отключения клиента"""
    logger.info(f"Socket.IO client disconnected: {sid}")


@sio.event
async def ping(sid, data):
    """Обработка ping сообщений"""
    await sio.emit("pong", {"timestamp": data.get("timestamp")}, to=sid)


# Создаем Socket.IO ASGI приложение
socket_app = socketio.ASGIApp(sio)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "aicrm.socket_server:socket_app",
        host="0.0.0.0",
        port=8001,  # Отдельный порт для Socket.IO
        reload=settings.debug,
        log_level="info",
    )
