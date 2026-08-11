"""
Сервис для работы с логами автоматизации
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.automation_log import AutomationLog


class AutomationLogService:
    """Сервис для управления логами автоматизации"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_log_entry(self, log_data: Dict[str, Any]) -> AutomationLog:
        """
        Создание записи в логе автоматизации

        Args:
            log_data: Данные для записи в лог

        Returns:
            AutomationLog: Созданная запись
        """
        # Адаптируем данные под существующую модель
        log_entry = AutomationLog(
            timestamp=log_data.get("timestamp", datetime.utcnow()),
            level=log_data.get("level", "info"),
            message=log_data.get("message", ""),
            process_id=log_data.get("process_id"),
            stage_id=log_data.get("stage_id"),
            details=log_data.get("details", {}),
        )

        self.db.add(log_entry)
        await self.db.commit()
        await self.db.refresh(log_entry)

        return log_entry

    async def get_logs(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AutomationLog]:
        """
        Получение логов с фильтрами

        Args:
            filters: Фильтры для поиска
            limit: Максимальное количество записей
            offset: Смещение

        Returns:
            List[AutomationLog]: Список записей логов
        """
        query = select(AutomationLog)

        if filters:
            conditions = []

            if "level" in filters:
                conditions.append(AutomationLog.level == filters["level"])

            if "process_id" in filters:
                conditions.append(AutomationLog.process_id == filters["process_id"])

            if "stage_id" in filters:
                conditions.append(AutomationLog.stage_id == filters["stage_id"])

            if "created_at_gte" in filters:
                conditions.append(AutomationLog.timestamp >= filters["created_at_gte"])

            if "created_at_lte" in filters:
                conditions.append(AutomationLog.timestamp <= filters["created_at_lte"])

            if conditions:
                query = query.where(and_(*conditions))

        query = query.order_by(desc(AutomationLog.timestamp))
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_log_by_id(self, log_id: int) -> Optional[AutomationLog]:
        """
        Получение записи лога по ID

        Args:
            log_id: ID записи

        Returns:
            AutomationLog или None
        """
        query = select(AutomationLog).where(AutomationLog.id == log_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_log_entry(
        self, log_id: int, update_data: Dict[str, Any]
    ) -> Optional[AutomationLog]:
        """
        Обновление записи в логе

        Args:
            log_id: ID записи
            update_data: Данные для обновления

        Returns:
            AutomationLog или None
        """
        log_entry = await self.get_log_by_id(log_id)
        if not log_entry:
            return None

        # Обновляем только разрешенные поля
        allowed_fields = ["level", "message", "process_id", "stage_id", "details"]

        for field, value in update_data.items():
            if field in allowed_fields:
                setattr(log_entry, field, value)

        await self.db.commit()
        await self.db.refresh(log_entry)
        return log_entry

    async def delete_log_entry(self, log_id: int) -> bool:
        """
        Удаление записи из лога

        Args:
            log_id: ID записи

        Returns:
            bool: Успешно ли удалено
        """
        log_entry = await self.get_log_by_id(log_id)
        if not log_entry:
            return False

        await self.db.delete(log_entry)
        await self.db.commit()
        return True

    async def get_logs_stats(self, days: int = 7) -> Dict[str, Any]:
        """
        Получение статистики по логам

        Args:
            days: Период в днях

        Returns:
            Dict со статистикой
        """
        since_date = datetime.utcnow() - timedelta(days=days)

        # Получаем логи за период
        logs = await self.get_logs(
            filters={"created_at_gte": since_date},
            limit=10000,  # Большой лимит для статистики
        )

        stats = {
            "total_logs": len(logs),
            "by_level": {},
            "by_process": {},
            "period_days": days,
        }

        for log in logs:
            # Статистика по уровням
            level = log.level or "unknown"
            stats["by_level"][level] = stats["by_level"].get(level, 0) + 1

            # Статистика по процессам
            process_id = log.process_id or "unknown"
            stats["by_process"][process_id] = stats["by_process"].get(process_id, 0) + 1

        return stats

    async def cleanup_old_logs(self, days_to_keep: int = 30) -> int:
        """
        Очистка старых записей логов

        Args:
            days_to_keep: Количество дней для хранения

        Returns:
            int: Количество удаленных записей
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        # Получаем старые логи
        old_logs = await self.get_logs(
            filters={"created_at_lte": cutoff_date}, limit=10000
        )

        deleted_count = 0
        for log in old_logs:
            if await self.delete_log_entry(log.id):
                deleted_count += 1

        return deleted_count
