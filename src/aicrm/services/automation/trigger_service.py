"""
Сервис триггеров автоматизации
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ...models.automation import EntityType, Stage, Trigger, TriggerEvent
from ...models.customer import Customer
from ...models.order import Order, OrderStatus
from ...models.production_step import ProductionStep, StepStatus
from ...models.task import Task

logger = logging.getLogger(__name__)


class TriggerService:
    """
    Сервис для обработки триггеров автоматизации
    """

    def __init__(self, db: Session):
        self.db = db

    async def handle_trigger_event(
        self,
        entity_type: EntityType,
        event_type: TriggerEvent,
        entity_id: int,
        event_data: Dict[str, Any] = None,
    ) -> List[Dict[str, Any]]:
        """
        Обработка события триггера - перемещение на целевую стадию
        """
        event_data = event_data or {}
        results = []

        # Находим активные триггеры для этого типа события и сущности
        triggers = (
            self.db.query(Trigger)
            .filter(
                Trigger.entity_type == entity_type,
                Trigger.event_type == event_type,
                Trigger.is_active == True,
            )
            .all()
        )

        for trigger in triggers:
            try:
                # Проверяем условия
                if await self._check_trigger_conditions(trigger, entity_id, event_data):
                    # Перемещаем сущность на целевую стадию
                    move_result = await self._move_to_target_stage(
                        entity_type, entity_id, trigger.target_stage_id
                    )

                    results.append(
                        {
                            "trigger_id": trigger.id,
                            "trigger_name": trigger.name,
                            "entity_type": entity_type.value,
                            "entity_id": entity_id,
                            "target_stage_id": trigger.target_stage_id,
                            "success": True,
                            "move_result": move_result,
                        }
                    )

                    logger.info(f"Trigger {trigger.name} executed successfully")

            except Exception as e:
                logger.error(f"Error executing trigger {trigger.id}: {e}")
                results.append(
                    {"trigger_id": trigger.id, "success": False, "error": str(e)}
                )

        return results

    async def _check_trigger_conditions(
        self, trigger: Trigger, entity_id: int, event_data: Dict[str, Any]
    ) -> bool:
        """Проверка условий срабатывания триггера"""
        if not trigger.conditions:
            return True

        # Получаем данные сущности
        entity_data = await self._get_entity_data(trigger.entity_type, entity_id)
        if not entity_data:
            return False

        # Проверяем условия
        return self._evaluate_conditions(trigger.conditions, entity_data, event_data)

    def _evaluate_conditions(
        self,
        conditions: Dict[str, Any],
        entity_data: Dict[str, Any],
        event_data: Dict[str, Any],
    ) -> bool:
        """Оценка условий"""
        for field, condition in conditions.items():
            if isinstance(condition, dict):
                operator = condition.get("operator", "equals")
                expected_value = condition.get("value")
                actual_value = self._get_nested_value(entity_data, field)

                if not self._check_condition(actual_value, operator, expected_value):
                    return False
            else:
                # Простое равенство
                actual_value = self._get_nested_value(entity_data, field)
                if actual_value != condition:
                    return False

        return True

    def _get_nested_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """Получение вложенного значения по пути field.subfield"""
        keys = field_path.split(".")
        value = data

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None

        return value

    def _check_condition(
        self, actual_value: Any, operator: str, expected_value: Any
    ) -> bool:
        """Проверка условия с оператором"""
        if operator == "equals":
            return actual_value == expected_value
        elif operator == "not_equals":
            return actual_value != expected_value
        elif operator == "greater":
            return actual_value > expected_value if actual_value is not None else False
        elif operator == "less":
            return actual_value < expected_value if actual_value is not None else False
        elif operator == "contains":
            return (
                expected_value in actual_value
                if isinstance(actual_value, (str, list))
                else False
            )
        else:
            return False

    async def _move_to_target_stage(
        self, entity_type: EntityType, entity_id: int, target_stage_id: int
    ) -> Dict[str, Any]:
        """Перемещение сущности на целевую стадию"""
        # Получаем целевую стадию
        target_stage = self.db.query(Stage).filter(Stage.id == target_stage_id).first()
        if not target_stage:
            raise ValueError(f"Target stage {target_stage_id} not found")

        # Перемещаем сущность в зависимости от типа
        if entity_type == EntityType.CUSTOMER:
            return await self._move_customer_to_stage(entity_id, target_stage)
        elif entity_type == EntityType.ORDER:
            return await self._move_order_to_stage(entity_id, target_stage)
        elif entity_type == EntityType.TASK:
            return await self._move_task_to_stage(entity_id, target_stage)
        elif entity_type == EntityType.PRODUCTION_STEP:
            return await self._move_production_step_to_stage(entity_id, target_stage)
        else:
            raise ValueError(f"Unsupported entity type: {entity_type}")

    async def _get_entity_data(
        self, entity_type: EntityType, entity_id: int
    ) -> Optional[Dict[str, Any]]:
        """Получение данных сущности"""
        if entity_type == EntityType.CUSTOMER:
            customer = self.db.query(Customer).filter(Customer.id == entity_id).first()
            return customer.__dict__ if customer else None
        elif entity_type == EntityType.ORDER:
            order = self.db.query(Order).filter(Order.id == entity_id).first()
            return order.__dict__ if order else None
        elif entity_type == EntityType.TASK:
            task = self.db.query(Task).filter(Task.id == entity_id).first()
            return task.__dict__ if task else None
        elif entity_type == EntityType.PRODUCTION_STEP:
            step = (
                self.db.query(ProductionStep)
                .filter(ProductionStep.id == entity_id)
                .first()
            )
            return step.__dict__ if step else None
        return None

    async def _move_customer_to_stage(
        self, customer_id: int, stage: Stage
    ) -> Dict[str, Any]:
        """Перемещение клиента на стадию"""
        # Для клиентов можем обновлять статус или другие поля
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        # Обновляем поле stage или status если есть
        # Пока просто логируем
        logger.info(f"Customer {customer_id} moved to stage {stage.name}")

        return {
            "success": True,
            "entity_type": "customer",
            "entity_id": customer_id,
            "stage_name": stage.name,
        }

    async def _move_order_to_stage(self, order_id: int, stage: Stage) -> Dict[str, Any]:
        """Перемещение заказа на стадию"""
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")

        # Маппинг стадий на статусы заказов
        status_mapping = {
            "новый": OrderStatus.PENDING,
            "в работе": OrderStatus.IN_PROGRESS,
            "завершен": OrderStatus.COMPLETED,
            "отменен": OrderStatus.CANCELLED,
        }

        new_status = status_mapping.get(stage.name.lower())
        if new_status:
            order.status = new_status
            self.db.commit()

        logger.info(
            f"Order {order_id} moved to stage {stage.name}, status: {new_status}"
        )

        return {
            "success": True,
            "entity_type": "order",
            "entity_id": order_id,
            "stage_name": stage.name,
            "new_status": new_status.value if new_status else None,
        }

    async def _move_task_to_stage(self, task_id: int, stage: Stage) -> Dict[str, Any]:
        """Перемещение задачи на стадию"""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError(f"Task {task_id} not found")

        # Маппинг стадий на статусы задач
        status_mapping = {
            "новая": "todo",
            "в работе": "in_progress",
            "на проверке": "review",
            "завершена": "done",
        }

        new_status = status_mapping.get(stage.name.lower())
        if new_status:
            task.status = new_status
            self.db.commit()

        logger.info(f"Task {task_id} moved to stage {stage.name}, status: {new_status}")

        return {
            "success": True,
            "entity_type": "task",
            "entity_id": task_id,
            "stage_name": stage.name,
            "new_status": new_status,
        }

    async def _move_production_step_to_stage(
        self, step_id: int, stage: Stage
    ) -> Dict[str, Any]:
        """Перемещение этапа производства на стадию"""
        step = (
            self.db.query(ProductionStep).filter(ProductionStep.id == step_id).first()
        )
        if not step:
            raise ValueError(f"Production step {step_id} not found")

        # Маппинг стадий на статусы этапов
        status_mapping = {
            "ожидание": StepStatus.PENDING,
            "в работе": StepStatus.IN_PROGRESS,
            "завершен": StepStatus.COMPLETED,
        }

        new_status = status_mapping.get(stage.name.lower())
        if new_status:
            step.status = new_status
            if new_status == StepStatus.IN_PROGRESS and not step.started_at:
                step.started_at = datetime.utcnow()
            elif new_status == StepStatus.COMPLETED and not step.completed_at:
                step.completed_at = datetime.utcnow()
            self.db.commit()

        logger.info(
            f"Production step {step_id} moved to stage {stage.name}, status: {new_status}"
        )

        return {
            "success": True,
            "entity_type": "production_step",
            "entity_id": step_id,
            "stage_name": stage.name,
            "new_status": new_status.value if new_status else None,
        }
