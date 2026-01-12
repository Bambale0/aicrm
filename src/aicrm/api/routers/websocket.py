"""
WebSocket роутеры для real-time коммуникаций с безопасностью
"""

import asyncio
import json
from typing import Dict, Set

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy.orm import Session

from ...core.database import get_master_db
from ...models.user import User
from ...services.auth import auth_service
from ...services.rate_limiter import rate_limiter
from ...utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["websockets"])


@router.get("/ping")
async def ping():
    """Ping endpoint"""
    return "pong"


# Глобальные структуры для управления подключениями
class WebSocketManager:
    """Менеджер WebSocket подключений для real-time уведомлений"""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.user_connections: Dict[int, WebSocket] = {}

    async def connect(
        self, websocket: WebSocket, room: str = "general", user_id: int = None
    ):
        """Подключить WebSocket к комнате"""
        await websocket.accept()

        if room not in self.active_connections:
            self.active_connections[room] = set()

        self.active_connections[room].add(websocket)

        if user_id:
            self.user_connections[user_id] = websocket

        logger.info(f"WebSocket connected to room: {room}, user: {user_id}")

    def disconnect(
        self, websocket: WebSocket, room: str = "general", user_id: int = None
    ):
        """Отключить WebSocket от комнаты"""
        if room in self.active_connections:
            self.active_connections[room].discard(websocket)

            # Если комната пуста, удалим её
            if not self.active_connections[room]:
                del self.active_connections[room]

        if user_id and user_id in self.user_connections:
            del self.user_connections[user_id]

        logger.info(f"WebSocket disconnected from room: {room}, user: {user_id}")

    async def send_message(self, message: dict, room: str = "general"):
        """Отправить сообщение всем в комнате"""
        if room in self.active_connections:
            dead_connections = set()
            for connection in self.active_connections[room]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message: {e}")
                    dead_connections.add(connection)

            # Удалить мертвые подключения
            for dead in dead_connections:
                self.active_connections[room].discard(dead)

    async def send_to_user(self, user_id: int, message: dict):
        """Отправить сообщение конкретному пользователю"""
        if user_id in self.user_connections:
            try:
                await self.user_connections[user_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending to user {user_id}: {e}")
                del self.user_connections[user_id]

    async def broadcast(self, message: dict):
        """Отправить сообщение всем подключенным клиентам"""
        dead_connections = set()
        for room, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting: {e}")
                    dead_connections.add(connection)

        # Очистить мертвые подключения
        for room in self.active_connections:
            self.active_connections[room] -= dead_connections


# Глобальный менеджер подключений
ws_manager = WebSocketManager()


async def check_chat_access(user: User, chat_id: str, db: Session) -> bool:
    """
    Проверка доступа пользователя к чату на основе RBAC

    Args:
        user: Пользователь
        chat_id: ID чата
        db: Сессия базы данных

    Returns:
        bool: True если доступ разрешен
    """
    # Администраторы имеют доступ ко всем чатам
    if user.role == "admin":
        return True

    # Разбор chat_id для определения типа и владельца
    if chat_id.startswith("org_"):
        # Организационные чаты - только для менеджеров и выше
        return user.role in ["manager", "admin"]
    elif chat_id.startswith("telegram_"):
        # Telegram чаты - только для пользователей с ролью user или выше
        return user.is_active
    elif chat_id.startswith("avito_"):
        # Avito чаты - только для пользователей с ролью user или выше
        return user.is_active
    elif chat_id.startswith("customer_"):
        # Чаты клиентов - доступ имеют менеджеры и администраторы
        return user.role in ["manager", "admin"]
    else:
        # Неизвестный тип чата - доступ запрещен
        logger.warning(f"Unknown chat type for chat_id: {chat_id}")
        return False


def validate_chat_message(message_data: dict) -> bool:
    """
    Валидация содержимого сообщения чата

    Args:
        message_data: Данные сообщения

    Returns:
        bool: True если сообщение валидно
    """
    if not isinstance(message_data, dict):
        return False

    # Обязательные поля
    required_fields = ["content"]
    if not all(field in message_data for field in required_fields):
        return False

    # Валидация типов
    if not isinstance(message_data.get("content"), str):
        return False

    content = message_data.get("content", "")
    if len(content.strip()) == 0:
        return False

    # Ограничение длины сообщения
    if len(content) > 5000:  # Максимум 5000 символов
        return False

    # Проверка типа сообщения
    allowed_types = ["text", "system", "notification"]
    message_type = message_data.get("message_type", "text")
    if message_type not in allowed_types:
        return False

    return True


async def get_websocket_user(token: str, db: Session) -> User:
    """Верификация JWT токена для WebSocket"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token required"
        )

    # Rate limiting для WebSocket подключений
    client_id = f"ws_auth_{hash(token)}"
    if not await rate_limiter.check_rate_limit(client_id, limit=10, window_seconds=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded"
        )

    user = auth_service.get_current_user(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User not active"
        )

    return user


@router.websocket("/chat/{chat_id}")
async def chat_websocket(
    websocket: WebSocket,
    chat_id: str,
    token: str = None,
    db: Session = Depends(get_master_db),
):
    """
    WebSocket эндпоинт для чатов с JWT верификацией и RBAC

    Args:
        chat_id: ID чата (например, 'org_123', 'telegram_456', 'avito_789')
        token: Аутентификационный токен пользователя
    """
    user = None
    try:
        user = await get_websocket_user(token, db)
    except HTTPException as e:
        await websocket.close(code=e.status_code)
        return

    # RBAC: проверки доступа к чату
    if not await check_chat_access(user, chat_id, db):
        await websocket.close(code=status.HTTP_403_FORBIDDEN)
        return

    # Rate limiting для подключения к чату
    connection_key = f"ws_chat_{user.id}_{chat_id}"
    if not await rate_limiter.check_rate_limit(
        connection_key, limit=5, window_seconds=300
    ):
        await websocket.close(code=status.HTTP_429_TOO_MANY_REQUESTS)
        return

    # Подключаемся к комнате чата
    room = f"chat_{chat_id}"
    await ws_manager.connect(websocket, room, user.id)

    logger.info(f"User {user.id} connected to chat {chat_id}")

    try:
        while True:
            # Ждем сообщения от клиента
            data = await websocket.receive_text()

            # Rate limiting для сообщений
            message_key = f"ws_msg_{user.id}_{chat_id}"
            if not await rate_limiter.check_rate_limit(
                message_key, limit=20, window_seconds=60
            ):
                # Отправляем предупреждение вместо отключения
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": "Message rate limit exceeded. Please slow down.",
                        "timestamp": asyncio.get_event_loop().time(),
                    }
                )
                continue

            try:
                message_data = json.loads(data)

                # Валидация сообщения
                if not validate_chat_message(message_data):
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": "Invalid message format",
                            "timestamp": asyncio.get_event_loop().time(),
                        }
                    )
                    continue

                # Распространяем сообщение всем в чате
                notification = {
                    "type": "chat_message",
                    "chat_id": chat_id,
                    "user_id": user.id,
                    "user_email": user.email,
                    "user_role": user.role,
                    "content": message_data.get("content"),
                    "timestamp": message_data.get(
                        "timestamp", asyncio.get_event_loop().time()
                    ),
                    "message_type": message_data.get("message_type", "text"),
                }

                await ws_manager.send_message(notification, room)

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from user {user.id}: {data}")
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": "Invalid JSON format",
                        "timestamp": asyncio.get_event_loop().time(),
                    }
                )

    except WebSocketDisconnect:
        logger.info(f"User {user.id} disconnected from chat {chat_id}")
        ws_manager.disconnect(websocket, room, user.id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user.id}: {e}")
        ws_manager.disconnect(websocket, room, user.id)


@router.websocket("/notifications/{target_user_id}")
async def notifications_websocket(
    websocket: WebSocket,
    target_user_id: int,
    token: str = None,
    db: Session = Depends(get_master_db),
):
    """
    WebSocket эндпоинт для персональных уведомлений с безопасностью

    Args:
        target_user_id: ID пользователя, которому предназначены уведомления
        token: Аутентификационный токен
    """
    user = None
    try:
        user = await get_websocket_user(token, db)
    except HTTPException as e:
        await websocket.close(code=e.status_code)
        return

    # RBAC: проверка что пользователь может подписываться только на свои уведомления,
    # или админ может подписываться на любые
    if user.id != target_user_id and user.role != "admin":
        await websocket.close(code=status.HTTP_403_FORBIDDEN)
        return

    # Rate limiting для персональных уведомлений
    notify_key = f"ws_notifications_{user.id}"
    if not await rate_limiter.check_rate_limit(notify_key, limit=3, window_seconds=300):
        await websocket.close(code=status.HTTP_429_TOO_MANY_REQUESTS)
        return

    # Подключаемся к персональной комнате
    room = f"notifications_{target_user_id}"
    await ws_manager.connect(websocket, room, target_user_id)

    logger.info(f"User {user.id} connected to notifications for user {target_user_id}")

    try:
        while True:
            data = await websocket.receive_text()

            # Rate limiting для heartbeat сообщений
            heartbeat_key = f"ws_heartbeat_{user.id}"
            if data == "ping":
                if await rate_limiter.check_rate_limit(
                    heartbeat_key, limit=10, window_seconds=60
                ):
                    await websocket.send_json({"type": "pong"})
                else:
                    await websocket.send_json(
                        {"type": "error", "message": "Heartbeat rate limit exceeded"}
                    )
            else:
                # Неожиданные сообщения игнорируем
                logger.warning(f"Unexpected message in notifications WS: {data[:100]}")

    except WebSocketDisconnect:
        logger.info(
            f"User {user.id} disconnected from notifications for user {target_user_id}"
        )
        ws_manager.disconnect(websocket, room, target_user_id)
    except Exception as e:
        logger.error(f"Notifications WebSocket error for user {user.id}: {e}")
        ws_manager.disconnect(websocket, room, target_user_id)


@router.websocket("/global")
async def global_notifications_websocket(
    websocket: WebSocket, token: str = None, db: Session = Depends(get_master_db)
):
    """
    WebSocket для глобальных уведомлений с безопасностью
    Только активные пользователи могут подключаться
    """
    user = None
    try:
        user = await get_websocket_user(token, db)
    except HTTPException as e:
        await websocket.close(code=e.status_code)
        return

    # Rate limiting для глобальных уведомлений (более строгий лимит)
    global_key = f"ws_global_{user.id}"
    if not await rate_limiter.check_rate_limit(
        global_key, limit=2, window_seconds=600
    ):  # 2 подключения за 10 минут
        await websocket.close(code=status.HTTP_429_TOO_MANY_REQUESTS)
        return

    await ws_manager.connect(websocket, "global", user.id)

    logger.info(f"User {user.id} connected to global notifications")

    try:
        while True:
            data = await websocket.receive_text()

            # Rate limiting для heartbeat в глобальных уведомлениях
            global_heartbeat_key = f"ws_global_heartbeat_{user.id}"
            if data == "ping":
                if await rate_limiter.check_rate_limit(
                    global_heartbeat_key, limit=5, window_seconds=60
                ):
                    await websocket.send_json({"type": "pong"})
                else:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": "Global heartbeat rate limit exceeded",
                        }
                    )

    except WebSocketDisconnect:
        logger.info(f"User {user.id} disconnected from global notifications")
        ws_manager.disconnect(websocket, "global", user.id)
    except Exception as e:
        logger.error(f"Global notifications WebSocket error for user {user.id}: {e}")
        ws_manager.disconnect(websocket, "global", user.id)


# REST API для отправки уведомлений через WebSocket
@router.post("/notify/chat/{chat_id}")
async def send_chat_notification(
    chat_id: str, notification: dict, db: Session = Depends(get_master_db)
):
    """
    Отправить уведомление в чат через REST API
    """
    room = f"chat_{chat_id}"
    await ws_manager.send_message(notification, room)
    return {"status": "sent", "room": room}


@router.post("/notify/user/{user_id}")
async def send_user_notification(
    user_id: int, notification: dict, db: Session = Depends(get_master_db)
):
    """
    Отправить персональное уведомление пользователю
    """
    await ws_manager.send_to_user(user_id, notification)
    return {"status": "sent", "user_id": user_id}


@router.post("/broadcast")
async def broadcast_notification(
    notification: dict, db: Session = Depends(get_master_db)
):
    """
    Отправить глобальное уведомление всем подключенным клиентам
    """
    await ws_manager.broadcast(notification)
    return {
        "status": "broadcast",
        "recipients": sum(
            len(conns) for conns in ws_manager.active_connections.values()
        ),
    }


@router.get("/stats")
async def websocket_stats():
    """Получить статистику WebSocket подключений"""
    return {
        "active_rooms": len(ws_manager.active_connections),
        "total_connections": sum(
            len(conns) for conns in ws_manager.active_connections.values()
        ),
        "rooms": list(ws_manager.active_connections.keys()),
        "user_connections": len(ws_manager.user_connections),
    }


# Функция для отправки уведомлений из других модулей
async def notify_chat(chat_id: str, message: dict):
    """Вспомогательная функция для отправки сообщений в чат"""
    room = f"chat_{chat_id}"
    await ws_manager.send_message(message, room)


async def notify_user(user_id: int, message: dict):
    """Вспомогательная функция для отправки персонального уведомления"""
    await ws_manager.send_to_user(user_id, message)


async def broadcast_system_message(message: dict):
    """Вспомогательная функция для системных уведомлений"""
    await ws_manager.broadcast(message)


# Экспортируем менеджер для использования в других модулях
__all__ = [
    "WebSocketManager",
    "ws_manager",
    "notify_chat",
    "notify_user",
    "broadcast_system_message",
]