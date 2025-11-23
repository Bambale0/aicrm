"""
Кешированный сервис управления клиентами для улучшения производительности
"""
from typing import List, Optional
import json
from sqlalchemy.orm import Session

from ..services.customer import CustomerService as BaseCustomerService
from ..services.cache_service import cache_service
from ..utils.logging import get_logger

logger = get_logger(__name__)


class CachedCustomerService(BaseCustomerService):
    """Расширенный сервис клиентов с Redis кешированием"""

    CACHE_TTL_CUSTOMER = 1800  # 30 минут для индивидуальных клиентов
    CACHE_TTL_CUSTOMERS_LIST = 600  # 10 минут для списков
    CACHE_TTL_SEARCH = 300  # 5 минут для поиска
    CACHE_TTL_STATS = 900  # 15 минут для статистики

    @staticmethod
    async def get_customer_cached(db: Session, customer_id: int) -> Optional[dict]:
        """Получение клиента с кешированием"""
        cache_key = f"customer:{customer_id}"

        # Проверяем кеш
        cached_data = await cache_service.get(cache_key)
        if cached_data:
            logger.debug("Customer cache hit", customer_id=customer_id)
            return cached_data

        # Получаем из БД
        customer = BaseCustomerService.get_customer(db, customer_id)
        if customer:
            # Кешируем
            customer_dict = {
                'id': customer.id,
                'name': customer.name,
                'email': customer.email,
                'phone': customer.phone,
                'company': customer.company,
                'contact_info': customer.contact_info,
                'address': customer.address,
                'total_orders': customer.total_orders,
                'total_spent': float(customer.total_spent) if customer.total_spent else 0,
                'loyalty_level': customer.loyalty_level,
                'notes': customer.notes,
                'is_deleted': customer.is_deleted,
                'created_at': customer.created_at.isoformat() if customer.created_at else None,
                'updated_at': customer.updated_at.isoformat() if customer.updated_at else None
            }

            await cache_service.set(cache_key, customer_dict, CachedCustomerService.CACHE_TTL_CUSTOMER)
            logger.debug("Customer cached", customer_id=customer_id)

            return customer_dict

        return None

    @staticmethod
    async def get_customers_cached(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None
    ) -> List[dict]:
        """Получение списка клиентов с кешированием"""

        # Создаем уникальный ключ для кеша на основе параметров
        cache_key = f"customers:list:{skip}:{limit}:{search or 'none'}"

        # Проверяем кеш
        cached_data = await cache_service.get(cache_key)
        if cached_data:
            logger.debug("Customers list cache hit", skip=skip, limit=limit, search=search)
            return cached_data

        # Получаем из БД
        customers = BaseCustomerService.get_customers(db, skip, limit, search)

        # Конвертируем в словари для кеширования
        customers_list = []
        for customer in customers:
            customers_list.append({
                'id': customer.id,
                'name': customer.name,
                'email': customer.email,
                'phone': customer.phone,
                'company': customer.company,
                'total_orders': customer.total_orders,
                'total_spent': float(customer.total_spent) if customer.total_spent else 0,
                'loyalty_level': customer.loyalty_level,
                'created_at': customer.created_at.isoformat() if customer.created_at else None,
                'updated_at': customer.updated_at.isoformat() if customer.updated_at else None
            })

        # Кешируем
        await cache_service.set(cache_key, customers_list, CachedCustomerService.CACHE_TTL_CUSTOMERS_LIST)
        logger.debug("Customers list cached", count=len(customers_list), skip=skip, limit=limit, search=search)

        return customers_list

    @staticmethod
    async def search_customers_cached(
        db: Session,
        query: str,
        limit: int = 50
    ) -> List[dict]:
        """Поиск клиентов с кешированием"""
        cache_key = f"customers:search:{query}:{limit}"

        # Проверяем кеш
        cached_data = await cache_service.get(cache_key)
        if cached_data:
            logger.debug("Customer search cache hit", query=query, limit=limit)
            return cached_data

        # Ищем в БД
        customers = BaseCustomerService.search_customers(db, query, limit)

        # Конвертируем в словари
        customers_list = []
        for customer in customers:
            customers_list.append({
                'id': customer.id,
                'name': customer.name,
                'email': customer.email,
                'phone': customer.phone,
                'company': customer.company,
                'total_orders': customer.total_orders,
                'updated_at': customer.updated_at.isoformat() if customer.updated_at else None
            })

        # Кешируем
        await cache_service.set(cache_key, customers_list, CachedCustomerService.CACHE_TTL_SEARCH)
        logger.debug("Customer search cached", query=query, count=len(customers_list))

        return customers_list

    @staticmethod
    async def get_customer_stats_cached(db: Session, customer_id: int) -> Optional[dict]:
        """Получение статистики клиента с кешированием"""
        cache_key = f"customer:stats:{customer_id}"

        # Проверяем кеш
        cached_data = await cache_service.get(cache_key)
        if cached_data:
            logger.debug("Customer stats cache hit", customer_id=customer_id)
            return cached_data

        # Получаем из БД
        stats = BaseCustomerService.get_customer_stats(db, customer_id)
        if stats:
            # Кешируем
            await cache_service.set(cache_key, stats, CachedCustomerService.CACHE_TTL_STATS)
            logger.debug("Customer stats cached", customer_id=customer_id)

        return stats

    @staticmethod
    async def create_customer_cached(db: Session, customer_data: dict) -> dict:
        """Создание клиента с инвалидацией кеша"""

        # Создаем клиента через базовый сервис
        customer = BaseCustomerService.create_customer(db, customer_data)

        # Инвалидируем релевантные кеши
        customer_dict = {
            'id': customer.id,
            'name': customer.name,
            'email': customer.email,
            'phone': customer.phone,
            'company': customer.company,
            'created_at': customer.created_at.isoformat() if customer.created_at else None
        }

        # Кешируем нового клиента
        cache_key = f"customer:{customer.id}"
        await cache_service.set(cache_key, customer_dict, CachedCustomerService.CACHE_TTL_CUSTOMER)

        # Инвалидируем списки клиентов (сложно инвалидировать все комбинации, поэтому инвалидируем паттерн)
        await cache_service.clear_pattern("customers:list:*")
        await cache_service.clear_pattern("customers:search:*")

        logger.debug("Customer created and cache updated", customer_id=customer.id)

        return customer_dict

    @staticmethod
    async def update_customer_cached(
        db: Session,
        customer_id: int,
        update_data: dict
    ) -> Optional[dict]:
        """Обновление клиента с инвалидацией кеша"""

        # Обновляем в БД
        customer = BaseCustomerService.update_customer(db, customer_id, update_data)
        if not customer:
            return None

        # Обновляем кеш индивидуального клиента
        customer_dict = {
            'id': customer.id,
            'name': customer.name,
            'email': customer.email,
            'phone': customer.phone,
            'company': customer.company,
            'contact_info': customer.contact_info,
            'address': customer.address,
            'total_orders': customer.total_orders,
            'total_spent': float(customer.total_spent) if customer.total_spent else 0,
            'loyalty_level': customer.loyalty_level,
            'notes': customer.notes,
            'is_deleted': customer.is_deleted,
            'created_at': customer.created_at.isoformat() if customer.created_at else None,
            'updated_at': customer.updated_at.isoformat() if customer.updated_at else None
        }

        cache_key = f"customer:{customer_id}"
        await cache_service.set(cache_key, customer_dict, CachedCustomerService.CACHE_TTL_CUSTOMER)

        # Инвалидируем связанные кеши
        await cache_service.delete(f"customer:stats:{customer_id}")
        await cache_service.clear_pattern("customers:list:*")
        await cache_service.clear_pattern("customers:search:*")

        logger.debug("Customer updated and cache invalidated", customer_id=customer_id)

        return customer_dict

    @staticmethod
    async def delete_customer_cached(db: Session, customer_id: int) -> bool:
        """Удаление клиента с инвалидацией кеша"""

        # Удаляем из БД
        success = BaseCustomerService.delete_customer(db, customer_id)
        if not success:
            return False

        # Инвалидируем кеш
        await cache_service.delete(f"customer:{customer_id}")
        await cache_service.delete(f"customer:stats:{customer_id}")
        await cache_service.clear_pattern("customers:list:*")
        await cache_service.clear_pattern("customers:search:*")

        logger.debug("Customer deleted and cache invalidated", customer_id=customer_id)

        return True

    @staticmethod
    async def invalidate_customer_cache(customer_id: int) -> None:
        """Инвалидация всего кеша для клиента (вспомогательный метод)"""
        await cache_service.delete(f"customer:{customer_id}")
        await cache_service.delete(f"customer:stats:{customer_id}")

        # Инвалидируем все связанные кеши
        await cache_service.clear_pattern("customers:*")

        logger.debug("Customer cache fully invalidated", customer_id=customer_id)


# Экземпляр сервиса
cached_customer_service = CachedCustomerService()
