"""
Сервис роботов автоматизации
"""
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime
import asyncio
import logging

from ...models.automation import (
    Robot, RobotAction, RobotActionConfig, EntityType
)
from ...models.customer import Customer
from ...models.order import Order, OrderStatus
from ...models.task import Task
from ...models.production_step import ProductionStep, StepStatus
from ...services.task import TaskService
from ...services.production import ProductionService
from ...services.sms_service import sms_service
from ...services.external_api_service import external_api_service
from ...services.calendar_service import calendar_service
from ...services.automation.error_handler import AutomationErrorHandler

logger = logging.getLogger(__name__)


class RobotService:
    """
    Сервис для выполнения действий роботов
    """

    def __init__(self, db: Session):
        self.db = db
        self.error_handler = AutomationErrorHandler(db)
        self.action_executors = {
            RobotAction.SEND_EMAIL: self._execute_send_email,
            RobotAction.SEND_SMS: self._execute_send_sms,
            RobotAction.SEND_TELEGRAM: self._execute_send_telegram,
            RobotAction.CREATE_MESSAGE: self._execute_create_message,
            RobotAction.CREATE_TASK: self._execute_create_task,
            RobotAction.UPDATE_TASK_STATUS: self._execute_update_task_status,
            RobotAction.CREATE_PRODUCTION_STEP: self._execute_create_production_step,
            RobotAction.UPDATE_ORDER_STATUS: self._execute_update_order_status,
            RobotAction.NOTIFY_USER: self._execute_notify_user,
            RobotAction.NOTIFY_GROUP: self._execute_notify_group,
            RobotAction.UPDATE_FIELD: self._execute_update_field,
            RobotAction.CREATE_COMMUNICATION: self._execute_create_communication,
            RobotAction.ANALYZE_INTENT: self._execute_analyze_intent,
            RobotAction.GENERATE_RESPONSE: self._execute_generate_response,
            # Новые действия
            RobotAction.CALL_EXTERNAL_API: self._execute_call_external_api,
            RobotAction.CALL_WEBHOOK: self._execute_call_webhook,
            RobotAction.CALL_GRAPHQL: self._execute_call_graphql,
            RobotAction.CALL_SOAP: self._execute_call_soap,
            RobotAction.CREATE_CALENDAR_EVENT: self._execute_create_calendar_event,
            RobotAction.UPDATE_CALENDAR_EVENT: self._execute_update_calendar_event,
            RobotAction.SEND_CALENDAR_INVITE: self._execute_send_calendar_invite,
            # Новые действия для Avito автоматизации
            RobotAction.GENERATE_RESPONSE: self._execute_generate_response,
            RobotAction.SEND_STANDARD_RESPONSE: self._execute_send_standard_response,
            RobotAction.ESCALATE_COMPLEX_QUERY: self._execute_escalate_complex_query,
        }

    async def execute_stage_robots(
        self,
        entity_type: EntityType,
        entity_id: int,
        stage_id: int
    ) -> List[Dict[str, Any]]:
        """
        Выполнение всех роботов, привязанных к стадии
        """
        results = []

        # Находим активных роботов для этой стадии
        robots = self.db.query(Robot).filter(
            Robot.entity_type == entity_type,
            Robot.stage_id == stage_id,
            Robot.is_active == True
        ).all()

        for robot in robots:
            try:
                robot_result = await self._execute_robot_sequence(
                    robot, entity_type, entity_id
                )
                results.append({
                    "robot_id": robot.id,
                    "robot_name": robot.name,
                    "entity_type": entity_type.value,
                    "entity_id": entity_id,
                    "success": True,
                    "actions_executed": robot_result
                })

            except Exception as e:
                logger.error(f"Error executing robot {robot.id}: {e}")
                results.append({
                    "robot_id": robot.id,
                    "robot_name": robot.name,
                    "success": False,
                    "error": str(e)
                })

        return results

    async def _execute_robot_sequence(
        self,
        robot: Robot,
        entity_type: EntityType,
        entity_id: int
    ) -> List[Dict[str, Any]]:
        """
        Последовательное выполнение действий робота
        """
        executed_actions = []

        # Сортируем действия по порядку выполнения
        sorted_actions = sorted(robot.actions, key=lambda a: a.execution_order)

        for action_config in sorted_actions:
            try:
                # Задержка выполнения если указана
                if action_config.delay_seconds > 0:
                    await asyncio.sleep(action_config.delay_seconds)

                # Выполняем действие
                result = await self._execute_robot_action(
                    action_config, entity_type, entity_id
                )

                executed_actions.append({
                    "action_id": action_config.id,
                    "action_type": action_config.action_type.value,
                    "success": True,
                    "result": result
                })

            except Exception as e:
                error_message = str(e)
                logger.error(f"Error executing robot action {action_config.id}: {error_message}")

                # Обрабатываем ошибку через error handler
                error_result = await self.error_handler.handle_error(
                    automation_execution_id=0,  # TODO: передать реальный execution_id
                    robot_id=robot.id,
                    trigger_id=None,  # Для действий робота триггер не указан
                    error_type="robot_action",
                    error_message=error_message,
                    error_details={
                        "action_config": action_config.config,
                        "robot_name": robot.name,
                        "entity_type": entity_type.value,
                        "entity_id": entity_id
                    },
                    entity_type=entity_type,
                    entity_id=entity_id,
                    action_type=action_config.action_type
                )

                executed_actions.append({
                    "action_id": action_config.id,
                    "action_type": action_config.action_type.value,
                    "success": False,
                    "error": error_message,
                    "error_handled": error_result.get("error_logged", False),
                    "retry_scheduled": error_result.get("retry_scheduled", False)
                })

                # В линейной логике можно прервать выполнение при критических ошибках
                # TODO: Добавить логику определения критичности ошибки
                break

        return executed_actions

    async def execute_robot_action(
        self,
        robot_id: int,
        action_config: Dict[str, Any],
        entity_type: EntityType,
        entity_id: int
    ) -> Dict[str, Any]:
        """
        Выполнение отдельного действия робота

        Args:
            robot_id: ID робота
            action_config: Конфигурация действия
            entity_type: Тип сущности
            entity_id: ID сущности

        Returns:
            Dict с результатом выполнения
        """
        try:
            # Создаем объект RobotActionConfig из словаря
            from ...models.automation import RobotActionConfig, RobotAction

            config_obj = RobotActionConfig(
                action_type=RobotAction(action_config["action_type"]),
                config=action_config.get("config", {}),
                execution_order=action_config.get("execution_order", 1),
                delay_seconds=action_config.get("delay_seconds", 0)
            )

            # Выполняем действие
            result = await self._execute_robot_action(config_obj, entity_type, entity_id)
            return {
                "success": True,
                "result": result
            }

        except Exception as e:
            logger.error(f"Error executing robot action: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _execute_robot_action(
        self,
        action_config: RobotActionConfig,
        entity_type: EntityType,
        entity_id: int
    ) -> Any:
        """Выполнение конкретного действия робота"""
        executor = self.action_executors.get(action_config.action_type)
        if not executor:
            raise ValueError(f"No executor for action type: {action_config.action_type}")

        return await executor(action_config, entity_type, entity_id)

    # Реализации конкретных действий

    async def _execute_send_email(
        self,
        action_config: RobotActionConfig,
        entity_type: EntityType,
        entity_id: int
    ) -> Dict[str, Any]:
        """Отправка email через робота"""
        config = action_config.config or {}

        # Получаем данные сущности для подстановки в шаблон
        entity_data = await self._get_entity_data(entity_type, entity_id)

        # Генерация содержимого email
        template_name = config.get("template")
        email_content = await self._render_email_template(template_name, entity_data)

        # Получаем email получателя
        recipient_email = await self._get_recipient_email(entity_type, entity_id, config)

        # TODO: Интеграция с email сервисом
        logger.info(f"Email would be sent to {recipient_email} with template {template_name}")

        return {
            "status": "email_queued",
            "template": template_name,
            "recipient": recipient_email,
            "subject": email_content.get("subject")
        }

    async def _execute_send_sms(
        self,
        action_config: RobotActionConfig,
        entity_type: EntityType,
        entity_id: int
    ) -> Dict[str, Any]:
        """Отправка SMS через робота"""
        config = action_config.config or {}

        # Получаем номер телефона
        phone = await self._get_recipient_phone(entity_type, entity_id, config)
        message = config.get("message", "Уведомление от системы")

        # Получаем данные сущности для подстановки в сообщение
        entity_data = await self._get_entity_data(entity_type, entity_id)
        message = self._replace_placeholders(message, entity_data)

        # Отправляем SMS через сервис
        result = await sms_service.send_sms(phone, message)

        return {
            "status": "sms_sent" if result.get("success") else "sms_failed",
            "phone": phone,
            "message": message[:50] + "..." if len(message) > 50 else message,
            "provider": result.get("provider"),
            "message_id": result.get("message_id"),
            "cost": result.get("cost"),
            "error": result.get("error")
        }

    async def _execute_send_telegram(
        self,
        action_config: RobotActionConfig,
        entity_type: EntityType,
        entity_id: int
    ) -> Dict[str, Any]:
        """Отправка Telegram сообщения через робота"""
        config = action_config.config or {}

        # Получаем Telegram ID
        telegram_id = config.get("telegram_id")
        message = config.get("message", "Уведомление от системы")

        # TODO: Интеграция с Telegram Bot API
        logger.info(f"Telegram message would be sent to {telegram_id}: {message}")

        return {
            "status": "telegram_queued",
            "telegram_id": telegram_id,
            "message": message
        }

    async def _execute_create_message(
        self,
        action_config: RobotActionConfig,
        entity_type: EntityType,
        entity_id: int
    ) -> Dict[str, Any]:
        """Создание сообщения в системе коммуникаций"""
        config = action_config.config or {}

        message_data = {
            "entity_type": entity_type.value,
            "entity_id": entity_id,
            "message_type": config.get("message_type", "notification"),
            "content": config.get("content", "Автоматическое сообщение"),
            "priority": config.get("priority", "normal")
        }

        # TODO: Создание сообщения в системе коммуникаций
        logger.info(f"Message created: {message_data}")

        return {
            "status": "message_created",
            "message_data": message_data
        }

    async def _execute_create_task(
        self,
        action_config: RobotActionConfig,
        entity_type: EntityType,
        entity_id: int
    ) -> Dict[str, Any]:
        """Создание задачи через робота"""
        config = action_config.config or {}

        task_data = {
            "title": config.get("title", "Автоматическая задача"),
            "description": config.get("description", ""),
            "assigned_to": config.get("assigned_to"),
            "priority": config.get("priority", "medium"),
            "deadline": config.get("deadline")
        }

        # Создаем задачу через сервис
        task_service = TaskService(self.db)
        created_task = await task_service.create_task(
            self.db,
            task_data,
            created_by=config.get("created_by", 1)  # Системный пользователь
        )

        return {
            "status": "task_created",
            "task_id": created_task.id,
            "task_title": created_task.title
        }

    async def _execute_update_task_status(
        self,
        action_config: RobotActionConfig,
        entity_type: EntityType,
        entity_id: int
    ) -> Dict[str, Any]:
        """Обновление статуса задачи"""
        config = action_config.config or {}

        task_id = config.get("task_id") or entity_id  # Если не указан, используем текущую сущность
        new_status = config.get("status")

        if not new_status:
            raise ValueError("Status not specified for task update")

        # Обновляем задачу
        task_service = TaskService(self.db)
        updated_task = await task_service.update_task(
            self.db,
            task_id,
            {"status": new_status}
        )

        return {
            "status": "task_updated",
            "task_id": task_id,
            "new_status": new_status
        }

    async def _execute_create_production_step(
        self,
        action_config: RobotActionConfig,
        entity_type: EntityType,
        entity_id: int
    ) -> Dict[str, Any]:
        """Создание этапа производства"""
        config = action_config.config or {}

        step_data = {
            "order_id": config.get("order_id") or entity_id,
            "name": config.get("name", "Автоматический этап"),
            "description": config.get("description", ""),
            "estimated_hours": config.get("estimated_hours", 1),
            "assigned_user_id": config.get("assigned_user_id")
        }

        # Создаем этап через сервис производства
        production_service = ProductionService(self.db)
        # TODO: Добавить метод создания отдельного этапа

        logger.info(f"Production step would be created: {step_data}")

        return {
            "status": "production_step_created",
            "step_data": step_data
        }

    async def _execute_update_order_status(
        self,
        action_config: RobotActionConfig,
        entity_type: EntityType,
        entity_id: int
    ) -> Dict[str, Any]:
        """Обновление статуса заказа"""
        config = action_config.config or {}

        order_id = config.get("order_id") or entity_id
        new_status = config.get("status")

        if not new_status:
            raise ValueError("Status not specified for order update")

        # Обновляем заказ
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if order:
            order.status = OrderStatus(new_status)
            self.db.commit()

        return {
            "status": "order_updated",
            "order_id": order_id,
            "new_status": new_status
        }

    async def _execute_notify_user(
        self,
        action_config: RobotActionConfig,
        entity_type: EntityType,
        entity_id: int
    ) -> Dict[str, Any]:
        """Уведомление пользователя"""
        config = action_config.config or {}

        user_id = config.get("user_id")
        message = config.get("message", "Системное уведомление")
        notification_type = config.get("type", "info")

        # TODO: Система уведомлений пользователей
        logger.info(f"User {user_id} would be notified: {message}")

        return {
            "status": "user_notified",
            "user_id": user_id,
            "message": message,
            "type": notification_type
        }

    async def _execute_notify_group(
        self,
        action_config: RobotActionConfig,
        entity_type: EntityType,
        entity_id: int
    ) -> Dict[str, Any]:
        """Уведомление группы пользователей"""
        config = action_config.config or {}

        group_id = config.get("group_id")
        message = config.get("message", "Системное уведомление группы")
        notification_type = config.get("type", "info")

        # TODO: Система групповых уведомлений
        logger.info(f"Group {group_id} would be notified: {message}")

        return {
            "status": "group_notified",
            "group_id": group_id,
            "message": message,
            "type": notification_type
        }

    async def _execute_update_field(
        self,
        action_config: RobotActionConfig,
        entity_type: EntityType,
        entity_id: int
    ) -> Dict[str, Any]:
        """Обновление поля сущности"""
        config = action_config.config or {}

        field_name = config.get("field")
        field_value = config.get("value")

        if not field_name:
            raise ValueError("Field name not specified")

        # Обновляем поле в зависимости от типа сущности
        if entity_type == EntityType.CUSTOMER:
            customer = self.db.query(Customer).filter(Customer.id == entity_id).first()
            if customer and hasattr(customer, field_name):
                setattr(customer, field_name, field_value)
                self.db.commit()
        elif entity_type == EntityType.ORDER:
            order = self.db.query(Order).filter(Order.id == entity_id).first()
            if order and hasattr(order, field_name):
                setattr(order, field_name, field_value)
                self.db.commit()
        elif entity_type == EntityType.TASK:
            task = self.db.query(Task).filter(Task.id == entity_id).first()
            if task and hasattr(task, field_name):
                setattr(task, field_name, field_value)
                self.db.commit()

        return {
            "status": "field_updated",
            "entity_type": entity_type.value,
            "entity_id": entity_id,
            "field": field_name,
            "value": field_value
        }

    async def _execute_create_communication(
        self,
        action_config: RobotActionConfig,
        entity_type: EntityType,
        entity_id: int
    ) -> Dict[str, Any]:
        """Создание записи коммуникации"""
        config = action_config.config or {}

        communication_data = {
            "entity_type": entity_type.value,
            "entity_id": entity_id,
            "type": config.get("type", "system"),
            "direction": config.get("direction", "outbound"),
            "content": config.get("content", "Автоматическая коммуникация"),
            "status": config.get("status", "sent")
        }

        # TODO: Создание записи в таблице коммуникаций
        logger.info(f"Communication created: {communication_data}")

        return {
            "status": "communication_created",
            "communication_data": communication_data
        }

    async def _execute_analyze_intent(
        self,
        action_config: RobotActionConfig,
        entity_type: EntityType,
        entity_id: int
    ) -> Dict[str, Any]:
        """Анализ намерения через AI"""
        config = action_config.config or {}

        # Получаем текст для анализа
        text_to_analyze = config.get("text") or await self._get_entity_text(entity_type, entity_id)

        # TODO: Интеграция с AI сервисом для анализа намерения
        logger.info(f"Intent analysis would be performed on: {text_to_analyze[:100]}...")

        return {
            "status": "intent_analyzed",
            "text_length": len(text_to_analyze),
            "analysis_result": "placeholder"  # Результат анализа
        }

    async def _execute_generate_response(
        self,
        action_config: RobotActionConfig,
        entity_type: EntityType,
        entity_id: int
    ) -> Dict[str, Any]:
        """Генерация ответа через AI"""
        config = action_config.config or {}

        # Получаем контекст для генерации
        context = config.get("context") or await self._get_entity_context(entity_type, entity_id)

        # TODO: Интеграция с AI сервисом для генерации ответа
        logger.info(f"Response generation would be performed with context: {context[:100]}...")

        return {
            "status": "response_generated",
            "context_length": len(context),
            "generated_response": "placeholder"  # Сгенерированный ответ
        }

    async def _execute_send_standard_response(
        self,
        action_config: RobotActionConfig,
        entity_type: EntityType,
        entity_id: int
    ) -> Dict[str, Any]:
        """Отправка стандартного ответа"""
        config = action_config.config or {}

        response_text = config.get("response_text", "Спасибо за обращение. Мы свяжемся с вами в ближайшее время.")
        channel = config.get("channel", "email")  # email, telegram, sms

        # Получаем данные сущности для подстановки
        entity_data = await self._get_entity_data(entity_type, entity_id)
        response_text = self._replace_placeholders(response_text, entity_data)

        # TODO: Отправка через соответствующий канал
        logger.info(f"Standard response would be sent via {channel}: {response_text}")

        return {
            "status": "standard_response_sent",
            "channel": channel,
            "response_text": response_text
        }

    async def _execute_escalate_complex_query(
        self,
        action_config: RobotActionConfig,
        entity_type: EntityType,
        entity_id: int
    ) -> Dict[str, Any]:
        """Эскалация сложного запроса"""
        config = action_config.config or {}

        escalation_reason = config.get("reason", "Сложный запрос требует ручной обработки")
        target_user_id = config.get("target_user_id")
        priority = config.get("priority", "high")

        # Создаем задачу для эскалации
        task_data = {
            "title": f"Эскалация: {escalation_reason}",
            "description": f"Автоматическая эскалация для сущности {entity_type.value} ID {entity_id}",
            "assigned_to": target_user_id,
            "priority": priority
        }

        # Создаем задачу
        task_service = TaskService(self.db)
        created_task = await task_service.create_task(
            self.db,
            task_data,
            created_by=1  # Системный пользователь
        )

        return {
            "status": "query_escalated",
            "task_id": created_task.id,
            "reason": escalation_reason,
            "priority": priority
        }

    # Новые действия для расширенной автоматизации

    async def _execute_call_external_api(
        self,
        action_config: RobotActionConfig,
        entity_type: EntityType,
        entity_id: int
    ) -> Dict[str, Any]:
        """Вызов внешнего API"""
        config = action_config.config or {}

        method = config.get("method", "GET")
        url = config.get("url")
        headers = config.get("headers", {})
        params = config.get("params", {})
        data = config.get("data")
        json_data = config.get("json_data")
        auth = config.get("auth")  # [username, password]
        api_key = config.get("api_key")
        bearer_token = config.get("bearer_token")

        if not url:
            raise ValueError("URL not specified for external API call")

        # Получаем данные сущности для подстановки в запрос
        entity_data = await self._get_entity_data(entity_type, entity_id)

        # Заменяем плейсхолдеры в URL и данных
        url = self._replace_placeholders(url, entity_data)
        if json_data:
            json_data = self._replace_placeholders_in_dict(json_data, entity_data)
        if data:
            data = self._replace_placeholders_in_dict(data, entity_data)

        # Выполняем вызов API
        result = await external_api_service.call_api(
            method=method,
            url=url,
            headers=headers,
            params=params,
            data=data,
            json_data=json_data,
            auth=tuple(auth) if auth else None,
            api_key=api_key,
            bearer_token=bearer_token
        )

        return {
            "status": "api_called",
            "method": method,
            "url": url,
            "success": result.get("success", False),
            "status_code": result.get("status_code"),
            "response": result.get("json") or result.get("text", "")[:500]
        }

    async def _execute_call_webhook(
        self,
        action_config: RobotActionConfig,
        entity_type: EntityType,
        entity_id: int
    ) -> Dict[str, Any]:
        """Вызов webhook с данными события"""
        config = action_config.config or {}

        url = config.get("url")
        event_type = config.get("event_type", "automation_event")
        secret = config.get("secret")

        if not url:
            raise ValueError("Webhook URL not specified")

        # Получаем данные сущности
        entity_data = await self._get_entity_data(entity_type, entity_id)
        payload = {
            "event_type": event_type,
            "entity_type": entity_type.value,
            "entity_id": entity_id,
            "entity_data": entity_data,
            "timestamp": datetime.utcnow().isoformat(),
            "automation_triggered": True
        }

        # Выполняем вызов webhook
        result = await external_api_service.call_webhook(
            url=url,
            event_type=event_type,
            payload=payload,
            secret=secret
        )

        return {
            "status": "webhook_called",
            "url": url,
            "event_type": event_type,
            "success": result.get("success", False),
            "status_code": result.get("status_code")
        }

    async def _execute_call_graphql(
        self,
        action_config: RobotActionConfig,
        entity_type: EntityType,
        entity_id: int
    ) -> Dict[str, Any]:
        """Вызов GraphQL API"""
        config = action_config.config or {}

        url = config.get("url")
        query = config.get("query")
        variables = config.get("variables", {})
        headers = config.get("headers", {})

        if not url or not query:
            raise ValueError("GraphQL URL and query are required")

        # Получаем данные сущности для подстановки в переменные
        entity_data = await self._get_entity_data(entity_type, entity_id)
        variables = self._replace_placeholders_in_dict(variables, entity_data)

        # Выполняем GraphQL запрос
        result = await external_api_service.call_graphql(
            url=url,
            query=query,
            variables=variables,
            headers=headers
        )

        return {
            "status": "graphql_called",
            "url": url,
            "success": result.get("success", False),
            "status_code": result.get("status_code"),
            "data": result.get("json", {}).get("data"),
            "errors": result.get("json", {}).get("errors")
        }

    async def _execute_call_soap(
        self,
        action_config: RobotActionConfig,
        entity_type: EntityType,
        entity_id: int
    ) -> Dict[str, Any]:
        """Вызов SOAP API"""
        config = action_config.config or {}

        url = config.get("url")
        soap_action = config.get("soap_action")
        soap_body = config.get("soap_body")
        headers = config.get("headers", {})

        if not url or not soap_action or not soap_body:
            raise ValueError("SOAP URL, action and body are required")

        # Получаем данные сущности для подстановки в SOAP body
        entity_data = await self._get_entity_data(entity_type, entity_id)
        soap_body = self._replace_placeholders(soap_body, entity_data)

        # Выполняем SOAP запрос
        result = await external_api_service.call_soap_api(
            url=url,
            soap_action=soap_action,
            soap_body=soap_body,
            headers=headers
        )

        return {
            "status": "soap_called",
            "url": url,
            "soap_action": soap_action,
            "success": result.get("success", False),
            "status_code": result.get("status_code"),
            "response_length": len(result.get("text", ""))
        }

    async def _execute_create_calendar_event(
        self,
        action_config: RobotActionConfig,
        entity_type: EntityType,
        entity_id: int
    ) -> Dict[str, Any]:
        """Создание события в календаре"""
        config = action_config.config or {}

        title = config.get("title", "Автоматическое событие")
        description = config.get("description", "")
        start_time = config.get("start_time")
        end_time = config.get("end_time")
        attendees = config.get("attendees", [])
        calendar_id = config.get("calendar_id", "primary")
        provider = config.get("provider")

        # Получаем данные сущности для подстановки
        entity_data = await self._get_entity_data(entity_type, entity_id)
        title = self._replace_placeholders(title, entity_data)
        description = self._replace_placeholders(description, entity_data)

        # Создаем событие через calendar сервис
        result = await calendar_service.create_event(
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            attendees=attendees,
            calendar_id=calendar_id,
            provider=provider
        )

        return {
            "status": "calendar_event_created" if result.get("success") else "calendar_event_failed",
            "title": title,
            "start_time": start_time,
            "end_time": end_time,
            "attendees_count": len(attendees),
            "event_id": result.get("event_id"),
            "provider": result.get("provider"),
            "success": result.get("success", False),
            "error": result.get("error")
        }

    async def _execute_update_calendar_event(
        self,
        action_config: RobotActionConfig,
        entity_type: EntityType,
        entity_id: int
    ) -> Dict[str, Any]:
        """Обновление события в календаре"""
        config = action_config.config or {}

        event_id = config.get("event_id")
        updates = config.get("updates", {})
        calendar_id = config.get("calendar_id", "primary")
        provider = config.get("provider")

        if not event_id:
            raise ValueError("Event ID not specified for calendar update")

        # Получаем данные сущности для подстановки
        entity_data = await self._get_entity_data(entity_type, entity_id)
        updates = self._replace_placeholders_in_dict(updates, entity_data)

        # Обновляем событие через calendar сервис
        result = await calendar_service.update_event(
            event_id=event_id,
            updates=updates,
            calendar_id=calendar_id,
            provider=provider
        )

        return {
            "status": "calendar_event_updated" if result.get("success") else "calendar_event_update_failed",
            "event_id": event_id,
            "updates": updates,
            "provider": result.get("provider"),
            "success": result.get("success", False),
            "error": result.get("error")
        }

    async def _execute_send_calendar_invite(
        self,
        action_config: RobotActionConfig,
        entity_type: EntityType,
        entity_id: int
    ) -> Dict[str, Any]:
        """Отправка приглашения в календарь"""
        config = action_config.config or {}

        event_id = config.get("event_id")
        attendees = config.get("attendees", [])
        calendar_id = config.get("calendar_id", "primary")
        provider = config.get("provider")

        if not event_id:
            raise ValueError("Event ID not specified for calendar invite")

        # Отправляем приглашения через calendar сервис
        result = await calendar_service.send_invite(
            event_id=event_id,
            attendees=attendees,
            calendar_id=calendar_id,
            provider=provider
        )

        return {
            "status": "calendar_invites_sent" if result.get("success") else "calendar_invites_failed",
            "event_id": event_id,
            "attendees_count": len(attendees),
            "provider": result.get("provider"),
            "success": result.get("success", False),
            "error": result.get("error")
        }

    # Вспомогательные методы

    async def _get_entity_data(self, entity_type: EntityType, entity_id: int) -> Dict[str, Any]:
        """Получение данных сущности для шаблонов"""
        if entity_type == EntityType.CUSTOMER:
            customer = self.db.query(Customer).filter(Customer.id == entity_id).first()
            return customer.__dict__ if customer else {}
        elif entity_type == EntityType.ORDER:
            order = self.db.query(Order).filter(Order.id == entity_id).first()
            return order.__dict__ if order else {}
        elif entity_type == EntityType.TASK:
            task = self.db.query(Task).filter(Task.id == entity_id).first()
            return task.__dict__ if task else {}
        return {}

    async def _render_email_template(self, template_name: str, data: Dict[str, Any]) -> Dict[str, str]:
        """Рендеринг шаблона email"""
        # TODO: Система шаблонов
        templates = {
            "welcome": {
                "subject": "Добро пожаловать!",
                "body": f"Здравствуйте, {data.get('name', 'Клиент')}!"
            },
            "order_confirmation": {
                "subject": "Заказ подтвержден",
                "body": f"Ваш заказ #{data.get('id', 'N/A')} подтвержден."
            }
        }

        return templates.get(template_name, {
            "subject": "Уведомление",
            "body": "Системное уведомление"
        })

    async def _get_recipient_email(self, entity_type: EntityType, entity_id: int, config: Dict[str, Any]) -> str:
        """Получение email получателя"""
        # Проверяем конфиг
        if config.get("email"):
            return config["email"]

        # Получаем из сущности
        if entity_type == EntityType.CUSTOMER:
            customer = self.db.query(Customer).filter(Customer.id == entity_id).first()
            return customer.email if customer else ""

        return ""

    async def _get_recipient_phone(self, entity_type: EntityType, entity_id: int, config: Dict[str, Any]) -> str:
        """Получение номера телефона"""
        # Проверяем конфиг
        if config.get("phone"):
            return config["phone"]

        # Получаем из сущности
        if entity_type == EntityType.CUSTOMER:
            customer = self.db.query(Customer).filter(Customer.id == entity_id).first()
            return customer.phone if customer else ""

        return ""

    async def _get_entity_text(self, entity_type: EntityType, entity_id: int) -> str:
        """Получение текста для анализа"""
        # TODO: Реализация получения текста из сущности
        return "Sample text for analysis"

    async def _get_entity_context(self, entity_type: EntityType, entity_id: int) -> str:
        """Получение контекста для генерации ответа"""
        # TODO: Реализация получения контекста из сущности
        return "Sample context for response generation"

    def _replace_placeholders(self, text: str, data: Dict[str, Any]) -> str:
        """Замена плейсхолдеров в строке"""
        if not text:
            return text

        for key, value in data.items():
            if value is not None:
                placeholder = f"{{{key}}}"
                text = text.replace(placeholder, str(value))

        return text

    def _replace_placeholders_in_dict(self, data: Dict[str, Any], entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Рекурсивная замена плейсхолдеров в словаре"""
        if not data:
            return data

        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self._replace_placeholders(value, entity_data)
            elif isinstance(value, dict):
                result[key] = self._replace_placeholders_in_dict(value, entity_data)
            elif isinstance(value, list):
                result[key] = [
                    self._replace_placeholders_in_dict(item, entity_data) if isinstance(item, dict)
                    else self._replace_placeholders(item, entity_data) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                result[key] = value

        return result
