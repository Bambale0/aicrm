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
    pass


class AvitoAPIError(Exception):
    """Ошибка API Avito"""
    pass


class AvitoRateLimitError(Exception):
    """Превышен лимит запросов Avito"""
    pass


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
