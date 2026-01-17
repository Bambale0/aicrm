"""
Сервис для управления AI Workflows - создание из промпта, выполнение, тестирование
"""

import json
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..core.ai_config import ai_config
from ..models.token_accounting import ActionExecution, Workflow, WorkflowExecution
from ..services.ai.client import UnifiedAIClient
from ..services.notification_service import NotificationService
from ..services.token_accounting_service import TokenAccountingService


class WorkflowService:
    """Сервис для управления AI workflows"""

    def __init__(self, db: Session):
        self.db = db
        self.ai_client = UnifiedAIClient()
        self.token_service = TokenAccountingService(db)
        self.notification_service = NotificationService(db)

    async def create_workflow_from_prompt(
        self,
        prompt: str,
        name: Optional[str] = None,
        created_by: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> Workflow:
        """
        Создание workflow из текстового описания с помощью AI

        Args:
            prompt: Текстовое описание сценария
            name: Название workflow (если не указано, сгенерирует AI)
            created_by: ID пользователя-создателя
            user_id: ID пользователя для учета токенов

        Returns:
            Workflow: Созданный workflow
        """
        # Генерируем workflow с помощью AI
        workflow_data = await self._generate_workflow_from_prompt(prompt, user_id)

        # Создаем workflow в БД
        workflow = Workflow(
            name=name or workflow_data.get("name", "AI Generated Workflow"),
            description_ai=workflow_data.get("description"),
            trigger=workflow_data["trigger"],
            conditions=workflow_data["conditions"],
            actions=workflow_data["actions"],
            created_by=created_by,
        )

        self.db.add(workflow)
        self.db.commit()
        self.db.refresh(workflow)

        return workflow

    async def execute_workflow(
        self,
        workflow_id: int,
        trigger_event: Dict[str, Any],
        user_id: Optional[int] = None,
    ) -> WorkflowExecution:
        """
        Выполнение workflow по событию

        Args:
            workflow_id: ID workflow
            trigger_event: Событие-триггер
            user_id: ID пользователя для учета токенов

        Returns:
            WorkflowExecution: Результат выполнения
        """
        # Получаем workflow
        workflow = self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow or not workflow.is_active:
            raise ValueError(f"Workflow {workflow_id} not found or inactive")

        # Создаем запись выполнения
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            trigger_event=trigger_event,
            execution_status="running",
            started_at=datetime.utcnow(),
        )
        self.db.add(execution)
        self.db.commit()

        try:
            # Проверяем условия
            if not self._check_conditions(workflow.conditions, trigger_event):
                execution.execution_status = "completed"
                execution.execution_result = {"status": "conditions_not_met"}
                execution.completed_at = datetime.utcnow()
                self.db.commit()
                return execution

            # Выполняем действия
            results = []
            for action_data in workflow.actions:
                action_result = await self._execute_action(
                    action_data, trigger_event, execution.id, user_id
                )
                results.append(action_result)

            execution.execution_status = "completed"
            execution.execution_result = {
                "actions_executed": len(results),
                "results": results,
            }
            execution.completed_at = datetime.utcnow()

        except Exception as e:
            execution.execution_status = "failed"
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()

        self.db.commit()
        return execution

    async def test_workflow(
        self,
        workflow_id: int,
        test_event: Dict[str, Any],
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Тестирование workflow на тестовых данных

        Args:
            workflow_id: ID workflow
            test_event: Тестовое событие
            user_id: ID пользователя

        Returns:
            Dict: Результаты тестирования
        """
        start_time = time.time()

        workflow = self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        # Проверяем триггер
        triggered = workflow.trigger.get("event_type") == test_event.get("event_type")

        # Проверяем условия
        conditions_met = (
            self._check_conditions(workflow.conditions, test_event)
            if triggered
            else False
        )

        # Выполняем действия (в тестовом режиме)
        actions_executed = []
        if conditions_met:
            for action_data in workflow.actions:
                # Имитируем выполнение без реальных вызовов
                action_result = {
                    "action_name": action_data["name"],
                    "action_type": action_data["type"],
                    "status": "simulated",
                    "config": action_data["config"],
                }
                actions_executed.append(action_result)

        execution_time = time.time() - start_time

        return {
            "workflow_id": workflow_id,
            "triggered": triggered,
            "conditions_met": conditions_met,
            "actions_executed": actions_executed,
            "execution_time": execution_time,
        }

    def get_workflow_executions(
        self,
        workflow_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Получение истории выполнений workflow

        Args:
            workflow_id: ID workflow (опционально)
            status: Статус выполнения (опционально)
            limit: Максимальное количество записей
            offset: Смещение

        Returns:
            List[Dict]: Список выполнений
        """
        query = self.db.query(
            WorkflowExecution, Workflow.name.label("workflow_name")
        ).join(Workflow)

        if workflow_id:
            query = query.filter(WorkflowExecution.workflow_id == workflow_id)
        if status:
            query = query.filter(WorkflowExecution.execution_status == status)

        query = (
            query.order_by(WorkflowExecution.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        results = []
        for execution, workflow_name in query.all():
            results.append(
                {
                    "id": execution.id,
                    "workflow_id": execution.workflow_id,
                    "workflow_name": workflow_name,
                    "trigger_event": execution.trigger_event,
                    "execution_status": execution.execution_status,
                    "started_at": execution.started_at,
                    "completed_at": execution.completed_at,
                    "error_message": execution.error_message,
                }
            )

        return results

    def get_workflows(
        self,
        is_active: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Workflow]:
        """
        Получение списка workflow

        Args:
            is_active: Фильтр по активности
            limit: Максимальное количество
            offset: Смещение

        Returns:
            List[Workflow]: Список workflow
        """
        query = self.db.query(Workflow)

        if is_active is not None:
            query = query.filter(Workflow.is_active == is_active)

        return (
            query.order_by(Workflow.created_at.desc()).offset(offset).limit(limit).all()
        )

    async def _generate_workflow_from_prompt(
        self, prompt: str, user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Генерация структуры workflow из промпта с помощью AI

        Args:
            prompt: Текстовое описание
            user_id: ID пользователя для учета токенов

        Returns:
            Dict: Структура workflow
        """
        system_prompt = """
Ты - эксперт по автоматизации бизнес-процессов. Твоя задача - проанализировать текстовое описание бизнес-сценария и преобразовать его в структурированный workflow.

Workflow состоит из:
1. trigger (триггер) - событие, которое запускает workflow
2. conditions (условия) - дополнительные проверки после триггера
3. actions (действия) - что делать при выполнении условий

Доступные типы событий-триггеров:
- ON_ORDER_CREATED: создание заказа
- ON_LEAD_ADD: добавление лида
- ON_PRODUCTION_STEP_COMPLETE: завершение этапа производства
- ON_CUSTOMER_CREATED: создание клиента
- ON_DEAL_STATUS_CHANGED: изменение статуса сделки

Доступные действия:
- send_notification: отправить уведомление (telegram, email)
- create_task: создать задачу пользователю
- update_entity: обновить поле сущности
- call_ai: вызвать AI для анализа/генерации
- make_http_request: выполнить HTTP запрос

Верни JSON с ключами: name, description, trigger, conditions, actions
"""

        user_message = f"Создай workflow из этого описания: {prompt}"

        # Учитываем токены
        if user_id:
            entity_type = "user"
            entity_id = user_id
        else:
            entity_type = None
            entity_id = None

        response = await self.ai_client.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            model="deepseek/deepseek-chat-v3.1",
            temperature=0.1,  # Низкая креативность для структурированного вывода
        )

        # Учет токенов
        if entity_type and entity_id:
            await self.token_service.check_quota_and_record_transaction(
                entity_type=entity_type,
                entity_id=entity_id,
                ai_provider="openrouter",
                ai_model="deepseek/deepseek-chat-v3.1",
                prompt_tokens=int(len(user_message.split()) * 1.2),
                completion_tokens=int(len(response.split()) * 1.3),
                estimated_cost=0.001
                * (len(user_message.split()) + len(response.split())),
            )

        # Парсим JSON из ответа
        try:
            # Ищем JSON в ответе
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            else:
                # Fallback: пытаемся распарсить весь ответ
                return json.loads(response)
        except json.JSONDecodeError:
            # Если не удалось распарсить, создаем базовую структуру
            return {
                "name": "Generated Workflow",
                "description": f"Workflow generated from: {prompt[:100]}...",
                "trigger": {"event_type": "ON_ORDER_CREATED"},
                "conditions": [],
                "actions": [
                    {
                        "name": "Send notification",
                        "type": "send_notification",
                        "config": {},
                    }
                ],
            }

    def _check_conditions(
        self, conditions: List[Dict[str, Any]], event: Dict[str, Any]
    ) -> bool:
        """
        Проверка выполнения условий

        Args:
            conditions: Список условий
            event: Событие

        Returns:
            bool: Выполнены ли все условия
        """
        payload = event.get("payload", {})

        for condition in conditions:
            field_path = condition["field_path"]
            operator = condition["operator"]
            expected_value = condition["value"]

            # Получаем значение поля (простая реализация без вложенных путей)
            actual_value = payload.get(field_path)

            if not self._evaluate_condition(actual_value, operator, expected_value):
                return False

        return True

    def _evaluate_condition(self, actual: Any, operator: str, expected: Any) -> bool:
        """
        Оценка отдельного условия

        Args:
            actual: Фактическое значение
            operator: Оператор сравнения
            expected: Ожидаемое значение

        Returns:
            bool: Результат сравнения
        """
        if operator == "eq":
            return actual == expected
        elif operator == "gt":
            return actual > expected if isinstance(actual, (int, float)) else False
        elif operator == "lt":
            return actual < expected if isinstance(actual, (int, float)) else False
        elif operator == "contains":
            return expected in str(actual) if actual else False
        elif operator == "exists":
            return actual is not None
        else:
            return True  # Неизвестный оператор - считаем выполненным

    async def _execute_action(
        self,
        action_data: Dict[str, Any],
        event: Dict[str, Any],
        execution_id: int,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Выполнение отдельного действия

        Args:
            action_data: Данные действия
            event: Событие
            execution_id: ID выполнения
            user_id: ID пользователя

        Returns:
            Dict: Результат выполнения
        """
        # Создаем запись выполнения действия
        action_execution = ActionExecution(
            execution_id=execution_id,
            action_name=action_data["name"],
            action_type=action_data["type"],
            action_config=action_data["config"],
            execution_status="running",
            started_at=datetime.utcnow(),
        )
        self.db.add(action_execution)
        self.db.commit()

        try:
            # Выполняем действие в зависимости от типа
            result = await self._perform_action(action_data, event, user_id)

            action_execution.execution_status = "completed"
            action_execution.execution_result = result
            action_execution.completed_at = datetime.utcnow()

        except Exception as e:
            action_execution.execution_status = "failed"
            action_execution.error_message = str(e)
            action_execution.completed_at = datetime.utcnow()
            result = {"error": str(e)}

        self.db.commit()
        return {
            "action_name": action_data["name"],
            "action_type": action_data["type"],
            "status": action_execution.execution_status,
            "result": result,
        }

    async def _perform_action(
        self,
        action_data: Dict[str, Any],
        event: Dict[str, Any],
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Выполнение действия конкретного типа

        Args:
            action_data: Данные действия
            event: Событие
            user_id: ID пользователя

        Returns:
            Dict: Результат выполнения
        """
        action_type = action_data["type"]
        config = action_data["config"]

        if action_type == "send_notification":
            return await self._send_notification(config, event)
        elif action_type == "create_task":
            return await self._create_task(config, event)
        elif action_type == "update_entity":
            return await self._update_entity(config, event)
        elif action_type == "call_ai":
            return await self._call_ai(config, event, user_id)
        elif action_type == "make_http_request":
            return await self._make_http_request(config, event)
        else:
            raise ValueError(f"Unknown action type: {action_type}")

    async def _send_notification(
        self, config: Dict[str, Any], event: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Отправка уведомления"""
        # Имитация отправки уведомления
        channel = config.get("channel", "telegram")
        message = config.get("message", "Notification from workflow")

        # Здесь должна быть реальная отправка через NotificationService
        return {"channel": channel, "message": message, "status": "sent"}

    async def _create_task(
        self, config: Dict[str, Any], event: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Создание задачи"""
        # Имитация создания задачи
        assignee_id = config.get("assignee_id")
        title = config.get("title", "Task from workflow")
        description = config.get("description", "")

        return {"assignee_id": assignee_id, "title": title, "status": "created"}

    async def _update_entity(
        self, config: Dict[str, Any], event: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Обновление сущности"""
        # Имитация обновления
        entity_type = config.get("entity_type")
        entity_id = config.get("entity_id")
        field = config.get("field")
        value = config.get("value")

        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "field": field,
            "value": value,
            "status": "updated",
        }

    async def _call_ai(
        self,
        config: Dict[str, Any],
        event: Dict[str, Any],
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Вызов AI"""
        prompt = config.get("prompt", "")
        model = config.get("model", "deepseek/deepseek-chat-v3.1")

        response = await self.ai_client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model=model,
        )

        # Учет токенов
        if user_id:
            await self.token_service.check_quota_and_record_transaction(
                entity_type="user",
                entity_id=user_id,
                ai_provider="openrouter",
                ai_model=model,
                prompt_tokens=int(len(prompt.split()) * 1.2),
                completion_tokens=int(len(response.split()) * 1.3),
                estimated_cost=0.001 * (len(prompt.split()) + len(response.split())),
                workflow_execution_id=str(uuid.uuid4()),  # Заглушка
            )

        return {"response": response, "model": model}

    async def _make_http_request(
        self, config: Dict[str, Any], event: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Выполнение HTTP запроса"""
        # Имитация HTTP запроса
        url = config.get("url")
        method = config.get("method", "GET")

        return {"url": url, "method": method, "status": "executed"}
