"""
Сервис интеграции с Avito API
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
import httpx
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..core.config import settings
from ..utils.logging import get_logger

logger = get_logger(__name__)


class AvitoAuthError(Exception):
    """Ошибка авторизации Avito"""

    def __init__(self, message: str = "Ошибка авторизации Avito", details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AvitoAPIError(Exception):
    """Ошибка API Avito"""

    def __init__(self, message: str = "Ошибка API Avito", status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}


class AvitoRateLimitError(Exception):
    """Превышен лимит запросов Avito"""

    def __init__(self, message: str = "Превышен лимит запросов Avito", retry_after: int = None):
        super().__init__(message)
        self.message = message
        self.retry_after = retry_after  # секунды до следующего запроса


class AvitoClient:
    """
    HTTP клиент для работы с Avito API
    """

    def __init__(self):
        self.base_url = "https://api.avito.ru"
        self.client_id = settings.avito_client_id
        self.client_secret = settings.avito_client_secret
        self.access_token = None
        self.token_expires_at = None
        self.user_id = settings.avito_user_id

        # HTTP клиент с настройками
        self.http_client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "AI-CRM/1.0"
            }
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.http_client.aclose()

    async def _ensure_token(self) -> str:
        """Обеспечение валидного access token"""
        if not self._is_token_valid():
            await self._refresh_token()
        return self.access_token

    def _is_token_valid(self) -> bool:
        """Проверка валидности токена"""
        if not self.access_token or not self.token_expires_at:
            return False
        # Добавляем 5 минут буфера
        return datetime.utcnow() < (self.token_expires_at - timedelta(minutes=5))

    async def _refresh_token(self):
        """Обновление access token через Client Credentials"""
        try:
            response = await self.http_client.post(
                "/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                }
            )
            response.raise_for_status()
            token_data = response.json()

            self.access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

            logger.info("Avito access token обновлен")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AvitoAuthError("Неверные учетные данные Avito")
            raise AvitoAPIError(f"Ошибка авторизации: {e.response.text}")
        except Exception as e:
            raise AvitoAPIError(f"Ошибка получения токена: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError))
    )
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Выполнение HTTP запроса с обработкой ошибок"""
        token = await self._ensure_token()

        headers = kwargs.get('headers', {})
        headers['Authorization'] = f'Bearer {token}'
        kwargs['headers'] = headers

        try:
            response = await self.http_client.request(method, endpoint, **kwargs)
            response.raise_for_status()

            # Проверка на rate limit
            if response.status_code == 429:
                raise AvitoRateLimitError("Превышен лимит запросов Avito")

            return response.json() if response.content else {}

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                # Токен истек, попробуем обновить
                self.access_token = None
                token = await self._ensure_token()
                headers['Authorization'] = f'Bearer {token}'
                kwargs['headers'] = headers
                response = await self.http_client.request(method, endpoint, **kwargs)
                response.raise_for_status()
                return response.json() if response.content else {}
            elif e.response.status_code == 429:
                raise AvitoRateLimitError("Превышен лимит запросов Avito")
            else:
                raise AvitoAPIError(f"API ошибка: {e.response.status_code} - {e.response.text}")
        except httpx.TimeoutException:
            raise AvitoAPIError("Таймаут запроса к Avito API")
        except Exception as e:
            raise AvitoAPIError(f"Неизвестная ошибка: {str(e)}")

    # Методы API

    async def get_items(self, **params) -> List[Dict[str, Any]]:
        """Получение списка объявлений"""
        response = await self._make_request(
            "GET",
            "/core/v1/items",
            params=params
        )
        return response.get("resources", [])

    async def get_item_info(self, item_id: int) -> Dict[str, Any]:
        """Получение информации об объявлении"""
        return await self._make_request(
            "GET",
            f"/core/v1/accounts/{self.user_id}/items/{item_id}/"
        )

    async def get_item_stats(
        self,
        item_ids: List[int],
        date_from: date,
        date_to: date,
        fields: List[str] = None,
        period_grouping: str = "day"
    ) -> Dict[str, Any]:
        """Получение статистики объявлений"""
        if fields is None:
            fields = ["uniqViews", "uniqContacts", "uniqFavorites"]

        data = {
            "itemIds": item_ids,
            "dateFrom": date_from.isoformat(),
            "dateTo": date_to.isoformat(),
            "fields": fields,
            "periodGrouping": period_grouping
        }

        return await self._make_request(
            "POST",
            f"/stats/v1/accounts/{self.user_id}/items",
            json=data
        )

    async def get_analytics(
        self,
        date_from: date,
        date_to: date,
        metrics: List[str],
        grouping: str = "item",
        **filters
    ) -> Dict[str, Any]:
        """Получение аналитики по профилю"""
        data = {
            "dateFrom": date_from.isoformat(),
            "dateTo": date_to.isoformat(),
            "metrics": metrics,
            "grouping": grouping,
            "limit": 1000,
            "offset": 0
        }

        if filters:
            data["filter"] = filters

        return await self._make_request(
            "POST",
            f"/stats/v2/accounts/{self.user_id}/items",
            json=data
        )

    async def get_vas_prices(self, item_ids: List[int]) -> List[Dict[str, Any]]:
        """Получение цен на услуги продвижения"""
        return await self._make_request(
            "POST",
            f"/core/v1/accounts/{self.user_id}/vas/prices",
            json={"itemIds": item_ids}
        )

    async def apply_vas(self, item_id: int, slugs: List[str], stickers: List[int] = None) -> Dict[str, Any]:
        """Применение услуг продвижения"""
        data = {"slugs": slugs}
        if stickers:
            data["stickers"] = stickers

        return await self._make_request(
            "PUT",
            f"/core/v2/items/{item_id}/vas/",
            json=data
        )

    async def update_price(self, item_id: int, price: int) -> Dict[str, Any]:
        """Обновление цены объявления"""
        return await self._make_request(
            "POST",
            f"/core/v1/items/{item_id}/update_price",
            json={"price": price}
        )

    async def get_calls_stats(
        self,
        date_from: date,
        date_to: date,
        item_ids: List[int] = None
    ) -> Dict[str, Any]:
        """Получение статистики звонков"""
        data = {
            "dateFrom": date_from.isoformat(),
            "dateTo": date_to.isoformat()
        }
        if item_ids:
            data["itemIds"] = item_ids

        return await self._make_request(
            "POST",
            f"/core/v1/accounts/{self.user_id}/calls/stats/",
            json=data
        )

    # Messenger API методы

    async def get_chats(
        self,
        item_ids: Optional[str] = None,
        unread_only: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Получение списка чатов"""
        params = {
            "limit": limit,
            "offset": offset
        }
        if item_ids:
            params["itemIds"] = item_ids
        if unread_only is not None:
            params["unreadOnly"] = str(unread_only).lower()

        return await self._make_request(
            "GET",
            f"/messenger/v1/accounts/{self.user_id}/chats",
            params=params
        )

    async def get_chat_by_id(self, chat_id: str) -> Dict[str, Any]:
        """Получение информации по чату"""
        return await self._make_request(
            "GET",
            f"/messenger/v1/accounts/{self.user_id}/chats/{chat_id}"
        )

    async def get_messages(
        self,
        chat_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Получение списка сообщений (v1)"""
        params = {
            "limit": limit,
            "offset": offset
        }

        return await self._make_request(
            "GET",
            f"/messenger/v1/accounts/{self.user_id}/chats/{chat_id}/messages/",
            params=params
        )

    async def get_messages_v2(
        self,
        chat_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Получение списка сообщений (v2)"""
        params = {
            "limit": limit,
            "offset": offset
        }

        return await self._make_request(
            "GET",
            f"/messenger/v2/accounts/{self.user_id}/chats/{chat_id}/messages/",
            params=params
        )

    async def send_message(
        self,
        chat_id: str,
        message: str
    ) -> Dict[str, Any]:
        """Отправка сообщения"""
        data = {
            "message": {
                "text": message
            }
        }

        return await self._make_request(
            "POST",
            f"/messenger/v1/accounts/{self.user_id}/chats/{chat_id}/messages",
            json=data
        )

    async def mark_chat_read(self, chat_id: str) -> Dict[str, Any]:
        """Отметка чата как прочитанного"""
        return await self._make_request(
            "POST",
            f"/messenger/v1/accounts/{self.user_id}/chats/{chat_id}/read"
        )

    async def delete_message(
        self,
        chat_id: str,
        message_id: str
    ) -> Dict[str, Any]:
        """Удаление сообщения"""
        return await self._make_request(
            "POST",
            f"/messenger/v1/accounts/{self.user_id}/chats/{chat_id}/messages/{message_id}"
        )

    async def add_to_blacklist(
        self,
        user_id: str,
        reason: Optional[str] = None
    ) -> None:
        """Добавление пользователя в черный список"""
        data = {"userId": user_id}
        if reason:
            data["reason"] = reason

        await self._make_request(
            "POST",
            f"/messenger/v1/accounts/{self.user_id}/blacklist",
            json=data
        )

    async def subscribe_webhook(
        self,
        url: str,
        events: List[str] = None
    ) -> Dict[str, Any]:
        """Подписка на webhook уведомления"""
        if events is None:
            events = ["message"]

        data = {
            "url": url,
            "events": events
        }

        return await self._make_request(
            "POST",
            "/messenger/v1/webhook",
            json=data
        )

    async def unsubscribe_webhook(
        self,
        url: str
    ) -> Dict[str, Any]:
        """Отписка от webhook уведомлений"""
        data = {"url": url}

        return await self._make_request(
            "POST",
            "/messenger/v1/webhook/unsubscribe",
            json=data
        )

    async def subscribe_webhook_v2(
        self,
        url: str,
        events: List[str] = None
    ) -> Dict[str, Any]:
        """Подписка на webhook уведомления (v2)"""
        if events is None:
            events = ["message"]

        data = {
            "url": url,
            "events": events
        }

        return await self._make_request(
            "POST",
            "/messenger/v2/webhook",
            json=data
        )


class AvitoService:
    """
    Бизнес-логика интеграции с Avito
    """

    def __init__(self):
        self.client = AvitoClient()

    async def __aenter__(self):
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def get_active_items(self) -> List[Dict[str, Any]]:
        """Получение активных объявлений"""
        try:
            items = await self.client.get_items(status="active", per_page=100)
            logger.info(f"Получено {len(items)} активных объявлений")
            return items
        except Exception as e:
            logger.error(f"Ошибка получения объявлений: {e}")
            raise

    async def get_item_performance(
        self,
        item_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Получение производительности объявления"""
        try:
            date_to = date.today()
            date_from = date_to - timedelta(days=days)

            # Статистика просмотров
            stats = await self.client.get_item_stats(
                item_ids=[item_id],
                date_from=date_from,
                date_to=date_to
            )

            # Статистика звонков
            calls_stats = await self.client.get_calls_stats(
                date_from=date_from,
                date_to=date_to,
                item_ids=[item_id]
            )

            # Информация об объявлении
            item_info = await self.client.get_item_info(item_id)

            return {
                "item_id": item_id,
                "title": item_info.get("title"),
                "status": item_info.get("status"),
                "url": item_info.get("url"),
                "stats": stats.get("result", {}),
                "calls": calls_stats.get("result", {}),
                "vas_active": item_info.get("vas", [])
            }

        except Exception as e:
            logger.error(f"Ошибка получения статистики объявления {item_id}: {e}")
            raise

    async def optimize_ad_pricing(self, item_id: int) -> Dict[str, Any]:
        """Оптимизация цены объявления на основе статистики"""
        try:
            # Получаем статистику за последние 30 дней
            performance = await self.get_item_performance(item_id, days=30)

            # Анализируем эффективность
            stats = performance.get("stats", {}).get("items", [])
            if not stats:
                return {"recommendation": "Недостаточно данных для анализа"}

            total_views = sum(day.get("uniqViews", 0) for day in stats[0].get("stats", []))
            total_contacts = sum(day.get("uniqContacts", 0) for day in stats[0].get("stats", []))

            if total_views == 0:
                conversion_rate = 0
            else:
                conversion_rate = total_contacts / total_views

            # Простая логика оптимизации
            if conversion_rate < 0.01:  # Менее 1% конверсии
                recommendation = "Увеличить цену на 5-10% для повышения качества трафика"
            elif conversion_rate > 0.05:  # Более 5% конверсии
                recommendation = "Цена оптимальна, рассмотреть применение VAS услуг"
            else:
                recommendation = "Цена в оптимальном диапазоне"

            return {
                "item_id": item_id,
                "current_conversion": conversion_rate,
                "total_views": total_views,
                "total_contacts": total_contacts,
                "recommendation": recommendation
            }

        except Exception as e:
            logger.error(f"Ошибка оптимизации цены для {item_id}: {e}")
            raise

    async def apply_promotion_service(
        self,
        item_id: int,
        service_slug: str,
        stickers: List[int] = None
    ) -> Dict[str, Any]:
        """Применение услуги продвижения"""
        try:
            result = await self.client.apply_vas(
                item_id=item_id,
                slugs=[service_slug],
                stickers=stickers
            )

            logger.info(f"Применена услуга {service_slug} к объявлению {item_id}")
            return result

        except Exception as e:
            logger.error(f"Ошибка применения услуги {service_slug} к {item_id}: {e}")
            raise

    async def get_promotion_options(self, item_ids: List[int]) -> List[Dict[str, Any]]:
        """Получение доступных услуг продвижения"""
        try:
            return await self.client.get_vas_prices(item_ids)
        except Exception as e:
            logger.error(f"Ошибка получения цен VAS для {item_ids}: {e}")
            raise

    async def update_item_price(self, item_id: int, new_price: int) -> Dict[str, Any]:
        """Обновление цены объявления"""
        try:
            result = await self.client.update_price(item_id, new_price)
            logger.info(f"Цена объявления {item_id} обновлена на {new_price}")
            return result
        except Exception as e:
            logger.error(f"Ошибка обновления цены для {item_id}: {e}")
            raise

    # Messenger API бизнес-методы

    async def get_avito_chats(
        self,
        item_ids: Optional[str] = None,
        unread_only: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Получение списка чатов из Avito"""
        try:
            return await self.client.get_chats(item_ids, unread_only, limit, offset)
        except Exception as e:
            logger.error(f"Ошибка получения списка чатов: {e}")
            raise

    async def get_avito_chat_info(self, chat_id: str) -> Dict[str, Any]:
        """Получение информации о чате из Avito"""
        try:
            return await self.client.get_chat_by_id(chat_id)
        except Exception as e:
            logger.error(f"Ошибка получения информации о чате {chat_id}: {e}")
            raise

    async def get_avito_messages(
        self,
        chat_id: str,
        limit: int = 100,
        offset: int = 0,
        use_v2: bool = True
    ) -> Dict[str, Any]:
        """Получение сообщений из чата Avito"""
        try:
            if use_v2:
                return await self.client.get_messages_v2(chat_id, limit, offset)
            else:
                return await self.client.get_messages(chat_id, limit, offset)
        except Exception as e:
            logger.error(f"Ошибка получения сообщений чата {chat_id}: {e}")
            raise

    async def send_avito_message(self, chat_id: str, message: str) -> Dict[str, Any]:
        """Отправка сообщения в чат Avito"""
        try:
            result = await self.client.send_message(chat_id, message)
            logger.info(f"Сообщение отправлено в чат {chat_id}")
            return result
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения в чат {chat_id}: {e}")
            raise

    async def mark_avito_chat_read(self, chat_id: str) -> Dict[str, Any]:
        """Отметка чата как прочитанного в Avito"""
        try:
            result = await self.client.mark_chat_read(chat_id)
            logger.info(f"Чат {chat_id} отмечен как прочитанный")
            return result
        except Exception as e:
            logger.error(f"Ошибка отметки чата {chat_id} как прочитанного: {e}")
            raise

    async def delete_avito_message(self, chat_id: str, message_id: str) -> Dict[str, Any]:
        """Удаление сообщения в Avito"""
        try:
            result = await self.client.delete_message(chat_id, message_id)
            logger.info(f"Сообщение {message_id} удалено из чата {chat_id}")
            return result
        except Exception as e:
            logger.error(f"Ошибка удаления сообщения {message_id} из чата {chat_id}: {e}")
            raise

    async def subscribe_avito_webhook(
        self,
        webhook_url: str,
        events: List[str] = None,
        use_v2: bool = False
    ) -> Dict[str, Any]:
        """Подписка на webhook уведомления Avito"""
        try:
            if use_v2:
                result = await self.client.subscribe_webhook_v2(webhook_url, events)
            else:
                result = await self.client.subscribe_webhook(webhook_url, events)
            
            logger.info(f"Подписка на webhook создана: {webhook_url}")
            return result
        except Exception as e:
            logger.error(f"Ошибка создания подписки на webhook {webhook_url}: {e}")
            raise

    async def unsubscribe_avito_webhook(self, webhook_url: str) -> Dict[str, Any]:
        """Отписка от webhook уведомлений Avito"""
        try:
            result = await self.client.unsubscribe_webhook(webhook_url)
            logger.info(f"Подписка на webhook отменена: {webhook_url}")
            return result
        except Exception as e:
            logger.error(f"Ошибка отмены подписки на webhook {webhook_url}: {e}")
            raise

    async def add_user_to_blacklist(self, user_id: str, reason: Optional[str] = None) -> None:
        """Добавление пользователя в черный список Avito"""
        try:
            await self.client.add_to_blacklist(user_id, reason)
            logger.info(f"Пользователь {user_id} добавлен в черный список")
        except Exception as e:
            logger.error(f"Ошибка добавления пользователя {user_id} в черный список: {e}")
            raise

    async def sync_avito_chats_with_db(self, db_session, limit: int = 100) -> Dict[str, Any]:
        """Синхронизация чатов из Avito с базой данных"""
        try:
            from ..models.avito_chat import AvitoChatSettings
            from ..models.customer import Customer

            # Получаем чаты из Avito
            avito_chats = await self.get_avito_chats(limit=limit)
            synced_count = 0
            created_count = 0

            if "chats" in avito_chats:
                for chat_data in avito_chats["chats"]:
                    chat_id = chat_data.get("id")
                    if not chat_id:
                        continue

                    # Проверяем существование чата в базе
                    existing_chat = db_session.query(AvitoChatSettings).filter(
                        AvitoChatSettings.chat_id == chat_id
                    ).first()

                    if not existing_chat:
                        # Создаем новый чат
                        chat_settings = AvitoChatSettings(
                            chat_id=chat_id,
                            ai_enabled=True,
                            notifications_enabled=True
                        )
                        db_session.add(chat_settings)
                        created_count += 1
                    
                    synced_count += 1

                db_session.commit()
                logger.info(f"Синхронизировано {synced_count} чатов, создано {created_count} новых")

            return {
                "synced_chats": synced_count,
                "created_chats": created_count,
                "total_chats": len(avito_chats.get("chats", []))
            }

        except Exception as e:
            logger.error(f"Ошибка синхронизации чатов: {e}")
            raise
