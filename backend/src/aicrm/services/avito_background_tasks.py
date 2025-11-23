"""
Background задачи для Avito операций
"""
from typing import Dict, Any, List
import asyncio
from datetime import datetime, timedelta

from ..core.database import get_async_db
from ..utils.logging import get_logger
from .avito_service import AvitoService, AvitoAPIError, AvitoNetworkError, AvitoTimeoutError
from .avito_handler import AvitoCommunicationHandler

logger = get_logger(__name__)


class AvitoBackgroundTasks:
    """
    Background задачи для тяжелых операций Avito
    """

    def __init__(self):
        self.running_tasks = set()

    async def sync_chats_history_background(
        self,
        chat_ids: List[str],
        limit_per_chat: int = 100,
        force_full_sync: bool = False
    ) -> Dict[str, Any]:
        """
        Background задача для синхронизации истории чатов

        Args:
            chat_ids: Список ID чатов для синхронизации
            limit_per_chat: Максимальное количество сообщений для загрузки на чат
            force_full_sync: Принудительная полная синхронизация (игнорировать существующие сообщения)

        Returns:
            Результат синхронизации
        """
        task_id = f"sync_chats_{datetime.utcnow().isoformat()}"
        self.running_tasks.add(task_id)

        try:
            logger.info(f"Запуск background синхронизации чатов: {len(chat_ids)} чатов", task_id=task_id)

            total_synced = 0
            total_errors = 0
            results = []

            async with AvitoService() as avito_service:
                for chat_id in chat_ids:
                    try:
                        # Синхронизируем историю чата
                        async for db_session in get_async_db():
                            await avito_service.sync_avito_chats_with_db(
                                db_session=db_session,
                                limit=limit_per_chat
                            )

                            # Получаем историю сообщений
                            messages_result = await avito_service.get_avito_messages(
                                chat_id=chat_id,
                                limit=limit_per_chat
                            )

                            # Синхронизируем сообщения с БД
                            handler = AvitoCommunicationHandler(db_session)
                        synced_messages = await handler._sync_messages_from_api(
                            chat_id, messages_result
                        )

                        results.append({
                            "chat_id": chat_id,
                            "synced_messages": synced_messages,
                            "status": "success"
                        })

                        total_synced += synced_messages
                        logger.info(f"Чат {chat_id} синхронизирован: {synced_messages} сообщений", task_id=task_id)

                    except Exception as e:
                        logger.error(f"Ошибка синхронизации чата {chat_id}: {e}", task_id=task_id)
                        results.append({
                            "chat_id": chat_id,
                            "error": str(e),
                            "status": "error"
                        })
                        total_errors += 1

                    # Небольшая пауза между чатами
                    await asyncio.sleep(0.5)

            logger.info(
                f"Завершена background синхронизация чатов: {total_synced} сообщений, {total_errors} ошибок",
                task_id=task_id
            )

            return {
                "task_id": task_id,
                "status": "completed",
                "total_chats": len(chat_ids),
                "total_synced_messages": total_synced,
                "total_errors": total_errors,
                "results": results
            }

        except Exception as e:
            logger.error(f"Критическая ошибка в background задаче синхронизации: {e}", task_id=task_id)
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(e)
            }
        finally:
            self.running_tasks.discard(task_id)

    async def bulk_send_messages_background(
        self,
        messages: List[Dict[str, Any]],
        delay_between_messages: float = 1.0
    ) -> Dict[str, Any]:
        """
        Background задача для массовой отправки сообщений

        Args:
            messages: Список сообщений в формате [{"chat_id": str, "message": str, "use_ai": bool}]
            delay_between_messages: Задержка между отправкой сообщений в секундах

        Returns:
            Результат отправки
        """
        task_id = f"bulk_send_{datetime.utcnow().isoformat()}"
        self.running_tasks.add(task_id)

        try:
            logger.info(f"Запуск background отправки сообщений: {len(messages)} сообщений", task_id=task_id)

            total_sent = 0
            total_errors = 0
            results = []

            async for db_session in get_async_db():
                handler = AvitoCommunicationHandler(db_session)

                for i, message_data in enumerate(messages):
                    try:
                        chat_id = message_data["chat_id"]
                        message_text = message_data["message"]
                        use_ai = message_data.get("use_ai", False)

                        if use_ai:
                            # Генерируем AI ответ
                            await handler.get_chat_history(chat_id, limit=5)
                            # Здесь можно добавить логику генерации AI ответа
                            # Пока просто отправляем как есть
                            success = await handler.send_message(chat_id, message_text)
                        else:
                            success = await handler.send_message(chat_id, message_text)

                        if success:
                            total_sent += 1
                            results.append({
                                "index": i,
                                "chat_id": chat_id,
                                "status": "sent"
                            })
                            logger.info(f"Сообщение {i+1}/{len(messages)} отправлено в чат {chat_id}", task_id=task_id)
                        else:
                            total_errors += 1
                            results.append({
                                "index": i,
                                "chat_id": chat_id,
                                "status": "error",
                                "error": "Failed to send"
                            })

                    except Exception as e:
                        logger.error(f"Ошибка отправки сообщения {i+1}: {e}", task_id=task_id)
                        total_errors += 1
                        results.append({
                            "index": i,
                            "chat_id": message_data.get("chat_id"),
                            "status": "error",
                            "error": str(e)
                        })

                    # Задержка между сообщениями
                    if i < len(messages) - 1:  # Не ждем после последнего сообщения
                        await asyncio.sleep(delay_between_messages)

            logger.info(
                f"Завершена background отправка сообщений: {total_sent} отправлено, {total_errors} ошибок",
                task_id=task_id
            )

            return {
                "task_id": task_id,
                "status": "completed",
                "total_messages": len(messages),
                "total_sent": total_sent,
                "total_errors": total_errors,
                "results": results
            }

        except Exception as e:
            logger.error(f"Критическая ошибка в background задаче отправки: {e}", task_id=task_id)
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(e)
            }
        finally:
            self.running_tasks.discard(task_id)

    async def update_items_performance_background(
        self,
        item_ids: List[int],
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Background задача для обновления производительности объявлений

        Args:
            item_ids: Список ID объявлений
            days: Период анализа в днях

        Returns:
            Результат обновления
        """
        task_id = f"update_performance_{datetime.utcnow().isoformat()}"
        self.running_tasks.add(task_id)

        try:
            logger.info(f"Запуск background обновления производительности: {len(item_ids)} объявлений", task_id=task_id)

            total_updated = 0
            total_errors = 0
            results = []

            async with AvitoService() as avito_service:
                for item_id in item_ids:
                    try:
                        # Обновляем производительность (кэш будет автоматически обновлен)
                        performance = await avito_service.get_item_performance(item_id, days)

                        results.append({
                            "item_id": item_id,
                            "status": "updated",
                            "performance": performance
                        })

                        total_updated += 1
                        logger.info(f"Производительность объявления {item_id} обновлена", task_id=task_id)

                    except Exception as e:
                        logger.error(f"Ошибка обновления производительности объявления {item_id}: {e}", task_id=task_id)
                        results.append({
                            "item_id": item_id,
                            "status": "error",
                            "error": str(e)
                        })
                        total_errors += 1

                    # Небольшая пауза между запросами
                    await asyncio.sleep(0.2)

            logger.info(
                f"Завершено background обновление производительности: {total_updated} обновлено, {total_errors} ошибок",
                task_id=task_id
            )

            return {
                "task_id": task_id,
                "status": "completed",
                "total_items": len(item_ids),
                "total_updated": total_updated,
                "total_errors": total_errors,
                "results": results
            }

        except Exception as e:
            logger.error(f"Критическая ошибка в background задаче обновления производительности: {e}", task_id=task_id)
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(e)
            }
        finally:
            self.running_tasks.discard(task_id)

    async def cleanup_old_data_background(self, days_to_keep: int = 90) -> Dict[str, Any]:
        """
        Background задача для очистки старых данных

        Args:
            days_to_keep: Количество дней для хранения данных

        Returns:
            Результат очистки
        """
        task_id = f"cleanup_{datetime.utcnow().isoformat()}"
        self.running_tasks.add(task_id)

        try:
            logger.info(f"Запуск background очистки данных старше {days_to_keep} дней", task_id=task_id)

            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            async for db_session in get_async_db():
                # Очистка старых коммуникаций (кроме важных)
                from ..models.communication import Communication

                deleted_communications = db_session.query(Communication).filter(
                    Communication.created_at < cutoff_date,
                    Communication.intent.is_(None),  # Удаляем только сообщения без intent
                    Communication.channel == "avito"
                ).delete()

                # Очистка старых логов (если есть)
                # Здесь можно добавить очистку других типов данных

                db_session.commit()

            logger.info(f"Удалено {deleted_communications} старых коммуникаций", task_id=task_id)

            return {
                "task_id": task_id,
                "status": "completed",
                "deleted_communications": deleted_communications,
                "cutoff_date": cutoff_date.isoformat()
            }

        except Exception as e:
            logger.error(f"Ошибка в background задаче очистки: {e}", task_id=task_id)
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(e)
            }
        finally:
            self.running_tasks.discard(task_id)

    async def health_check_background(self) -> Dict[str, Any]:
        """
        Background задача для проверки здоровья Avito интеграции

        Returns:
            Результат проверки здоровья
        """
        task_id = f"health_check_{datetime.utcnow().isoformat()}"
        self.running_tasks.add(task_id)

        try:
            logger.info("Запуск background проверки здоровья Avito", task_id=task_id)

            health_status = {
                "api_available": False,
                "webhook_working": False,
                "database_ok": False,
                "cache_ok": False,
                "rate_limiter_ok": False
            }

            # Проверка API доступности
            try:
                async with AvitoService() as avito_service:
                    # Пробуем получить активные объявления
                    await avito_service.get_active_items(use_cache_fallback=False)
                    health_status["api_available"] = True
                    logger.info("Avito API доступен", task_id=task_id)
            except (AvitoNetworkError, AvitoTimeoutError):
                logger.warning("Avito API недоступен (сеть/таймаут)", task_id=task_id)
            except AvitoAPIError as e:
                if e.error_subtype == "server_error":
                    logger.warning("Avito API недоступен (серверная ошибка)", task_id=task_id)
                else:
                    health_status["api_available"] = True  # API отвечает, но с ошибкой
            except Exception as e:
                logger.error(f"Ошибка проверки API: {e}", task_id=task_id)

            # Проверка базы данных
            try:
                async for db_session in get_async_db():
                    # Простой запрос для проверки
                    from ..models.avito_chat import AvitoChatSettings
                    count = db_session.query(AvitoChatSettings).count()
                    health_status["database_ok"] = True
                    logger.info(f"База данных OK, чатов: {count}", task_id=task_id)
            except Exception as e:
                logger.error(f"Ошибка базы данных: {e}", task_id=task_id)

            # Проверка кэша
            try:
                from .avito_service import AvitoCache
                cache = AvitoCache()
                test_key = f"health_check_{datetime.utcnow().isoformat()}"
                await cache.set_cached(test_key, {"test": True}, ttl_seconds=10)
                cached_data = await cache.get_cached(test_key)
                health_status["cache_ok"] = cached_data is not None
                logger.info("Кэш Redis OK", task_id=task_id)
            except Exception as e:
                logger.error(f"Ошибка кэша: {e}", task_id=task_id)

            # Проверка rate limiter
            try:
                from .rate_limiter import get_avito_rate_limiter
                rate_limiter = await get_avito_rate_limiter()
                allowed, _, _ = await rate_limiter.check_rate_limit("read", "health_check")
                health_status["rate_limiter_ok"] = True
                logger.info("Rate limiter OK", task_id=task_id)
            except Exception as e:
                logger.error(f"Ошибка rate limiter: {e}", task_id=task_id)

            overall_health = all(health_status.values())

            result = {
                "task_id": task_id,
                "status": "completed",
                "overall_health": overall_health,
                "checks": health_status,
                "timestamp": datetime.utcnow().isoformat()
            }

            logger.info(f"Проверка здоровья завершена: {'OK' if overall_health else 'ПРОБЛЕМЫ'}", task_id=task_id)
            return result

        except Exception as e:
            logger.error(f"Критическая ошибка в проверке здоровья: {e}", task_id=task_id)
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(e)
            }
        finally:
            self.running_tasks.discard(task_id)

    def get_running_tasks(self) -> List[str]:
        """Получение списка выполняющихся задач"""
        return list(self.running_tasks)

    def is_task_running(self, task_id: str) -> bool:
        """Проверка, выполняется ли задача"""
        return task_id in self.running_tasks


# Глобальный экземпляр для background задач
avito_background_tasks = AvitoBackgroundTasks()
