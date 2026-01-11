"""
Сервис роботов автоматизации
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from ...models.automation import EntityType, Robot, RobotAction, RobotActionConfig
from ...models.customer import Customer
from ...models.order import Order, OrderStatus
from ...models.task import Task
from ...services.automation.error_handler import AutomationErrorHandler
from ...services.calendar_service import calendar_service
from ...services.external_api_service import external_api_service
from ...services.production import ProductionService
from ...services.sms_service import sms_service
from ...services.task import TaskService

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
        self, entity_type: EntityType, entity_id: int, stage_id: int
    ) -> List[Dict[str, Any]]:
        """
        Выполнение всех роботов, привязанных к стадии
        """
        results = []

        # Находим активных роботов для этой стадии
        robots = (
            self.db.query(Robot)
            .filter(
                Robot.entity_type == entity_type,
                Robot.stage_id == stage_id,
                Robot.is_active,
            )
            .all()
        )

        for robot in robots:
            try:
                robot_result = await self._execute_robot_sequence(
                    robot, entity_type, entity_id
                )
                results.append(
                    {
                        "robot_id": robot.id,
                        "robot_name": robot.name,
                        "entity_type": entity_type.value,
                        "entity_id": entity_id,
                        "success": True,
                        "actions_executed": robot_result,
                    }
                )

            except Exception as e:
                logger.error(f"Error executing robot {robot.id}: {e}")
                results.append(
                    {
                        "robot_id": robot.id,
                        "robot_name": robot.name,
                        "success": False,
                        "error": str(e),
                    }
                )

        return results

    async def _execute_robot_sequence(
        self, robot: Robot, entity_type: EntityType, entity_id: int
    ) -> List[Dict[str, Any]]:
        """
        Последовательное выполнение действий робота
        """
        # Создаем запись выполнения автоматизации
        from ...models.automation import AutomationExecution

        automation_execution = AutomationExecution(
            entity_type=entity_type,
            entity_id=entity_id,
            robot_id=robot.id,
            stage_id=robot.stage_id,
            execution_status="running",
            actions_total=len(robot.actions),
            actions_successful=0,
            actions_failed=0,
        )

        try:
            self.db.add(automation_execution)
            self.db.commit()
            self.db.refresh(automation_execution)
        except Exception as e:
            logger.error(
                f"Failed to create automation execution for robot {robot.id}: {e}"
            )
            raise

        logger.info(
            f"Automation execution created: ID {automation_execution.id} for robot {robot.id}"
        )

        executed_actions = []

        # Проходим по всем действиям робота
        for action_config in robot.actions:
            try:
                # Задержка выполнения если указана
                if action_config.delay_seconds > 0:
                    await asyncio.sleep(action_config.delay_seconds)

                # Выполняем действие
                result = await self._execute_robot_action(
                    action_config, entity_type, entity_id
                )

                executed_actions.append(
                    {
                        "action_id": action_config.id,
                        "action_type": action_config.action_type.value,
                        "success": True,
                        "result": result,
                    }
                )

                # Обновляем статистику выполнения
                automation_execution.actions_successful += 1

            except Exception as e:
                error_message = str(e)
                logger.error(
                    f"Error executing robot action {action_config.id}: {error_message}"
                )

                # Обрабатываем ошибку через error handler
                try:
                    error_result = await self.error_handler.handle_error(
                        automation_execution_id=automation_execution.id,
                        robot_id=robot.id,
                        trigger_id=None,
                        error_type="robot_action",
                        error_message=error_message,
                        error_details={
                            "action_config": action_config.config,
                            "robot_name": robot.name,
                            "entity_type": entity_type.value,
                            "entity_id": entity_id,
                        },
                        entity_type=entity_type,
                        entity_id=entity_id,
                        action_type=action_config.action_type.value,
                    )
                except Exception as handler_error:
                    logger.error(f"Error handler itself failed: {handler_error}")
                    error_result = {"error_logged": False, "retry_scheduled": False}

                executed_actions.append(
                    {
                        "action_id": action_config.id,
                        "action_type": action_config.action_type.value,
                        "success": False,
                        "error": error_message,
                        "error_handled": error_result.get("error_logged", False),
                        "retry_scheduled": error_result.get("retry_scheduled", False),
                    }
                )

                automation_execution.actions_failed += 1

                # Определяем критичность ошибки и решаем, продолжать ли выполнение
                is_critical = self._is_error_critical(
                    error_message, action_config.action_type
                )
                if is_critical:
                    logger.warning(
                        f"Critical error in robot {robot.id}, stopping execution"
                    )
                    break

        # Обновляем финальный статус выполнения
        try:
            total_executed = len(executed_actions)
            if total_executed > 0:
                success_rate = automation_execution.actions_successful / total_executed
                automation_execution.execution_status = (
                    "completed" if success_rate == 1.0 else "partially_completed"
                )
            else:
                automation_execution.execution_status = (
                    "completed"  # No actions to execute
                )
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to update automation execution status: {e}")

        return executed_actions

    async def execute_robot_action(
        self,
        robot_id: int,
        action_config: Dict[str, Any],
        entity_type: EntityType,
        entity_id: int,
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
            from ...models.automation import RobotAction, RobotActionConfig

            # Получаем action_type из словаря (может быть вложенным)
            if "action_config" in action_config:
                # Если данные пришли как {'action_config': {...}}
                action_config = action_config["action_config"]

            action_type_str = action_config.get("action_type")
            if not action_type_str:
                logger.error(f"action_config: {action_config}")
                raise ValueError("action_type is required in action_config")

            config_obj = RobotActionConfig(
                robot_id=0,  # Временный ID для создания объекта
                action_type=RobotAction(action_type_str),
                config=action_config.get("config", {}),
                execution_order=action_config.get("execution_order", 1),
                delay_seconds=action_config.get("delay_seconds", 0),
            )

            # Выполняем действие
            result = await self._execute_robot_action(
                config_obj, entity_type, entity_id
            )
            return {"success": True, "result": result}

        except Exception as e:
            logger.error(f"Error executing robot action: {e}")
            return {"success": False, "error": str(e)}

    async def _execute_robot_action(
        self, action_config: RobotActionConfig, entity_type: EntityType, entity_id: int
    ) -> Any:
        """Выполнение конкретного действия робота"""
        executor = self.action_executors.get(action_config.action_type)
        if not executor:
            raise ValueError(
                f"No executor for action type: {action_config.action_type}"
            )

        return await executor(action_config, entity_type, entity_id)

    # Реализации конкретных действий

    async def _execute_send_email(
        self, action_config: RobotActionConfig, entity_type: EntityType, entity_id: int
    ) -> Dict[str, Any]:
        """Отправка email через робота"""
        config = action_config.config or {}

        # Получаем данные сущности для подстановки в шаблон
        entity_data = await self._get_entity_data(entity_type, entity_id)

        # Генерация содержимого email
        template_name = config.get("template") if config else None
        email_content = await self._render_email_template(template_name, entity_data)

        # Получаем email получателя
        recipient_email = await self._get_recipient_email(
            entity_type, entity_id, config
        )

        if not recipient_email:
            raise ValueError("Recipient email not found")

        # Отправляем email через email сервис
        from ...services.email_service import EmailMessage, email_service

        message = EmailMessage(
            to=recipient_email,
            subject=email_content.get("subject", "Уведомление"),
            body=email_content.get("body", "Системное уведомление"),
            html_body=email_content.get("html_body"),
        )

        success = await email_service.send_email(message)

        return {
            "status": "email_sent" if success else "email_failed",
            "template": template_name,
            "recipient": recipient_email,
            "subject": email_content.get("subject"),
            "success": success,
        }

    async def _execute_send_sms(
        self, action_config: RobotActionConfig, entity_type: EntityType, entity_id: int
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
            "error": result.get("error"),
        }

    async def _execute_send_telegram(
        self, action_config: RobotActionConfig, entity_type: EntityType, entity_id: int
    ) -> Dict[str, Any]:
        """Отправка Telegram сообщения через робота"""
        config = action_config.config or {}

        # Получаем Telegram ID
        telegram_id = config.get("telegram_id")
        message = config.get("message", "Уведомление от системы")

        # Получаем данные сущности для подстановки
        entity_data = await self._get_entity_data(entity_type, entity_id)
        message = self._replace_placeholders(message, entity_data)

        # Интеграция с Telegram Bot API
        try:
            from ...services.telegram_bot_service import telegram_bot_service

            if not telegram_id:
                raise ValueError("Telegram ID not specified")

            # Отправляем сообщение через Telegram сервис
            result = await telegram_bot_service.send_message(
                chat_id=str(telegram_id), text=message
            )

            return {
                "status": (
                    "telegram_sent" if result.get("success") else "telegram_failed"
                ),
                "telegram_id": telegram_id,
                "message": message[:100] + "..." if len(message) > 100 else message,
                "message_id": result.get("message_id"),
                "success": result.get("success", False),
                "error": result.get("error"),
            }

        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return {
                "status": "telegram_failed",
                "telegram_id": telegram_id,
                "message": message[:100] + "..." if len(message) > 100 else message,
                "error": str(e),
            }

    async def _execute_create_message(
        self, action_config: RobotActionConfig, entity_type: EntityType, entity_id: int
    ) -> Dict[str, Any]:
        """Создание сообщения в системе коммуникаций"""
        config = action_config.config or {}

        # Получаем данные сущности для подстановки
        entity_data = await self._get_entity_data(entity_type, entity_id)

        message_content = config.get("content", "Автоматическое сообщение")
        message_content = self._replace_placeholders(message_content, entity_data)

        # Создаем запись коммуникации
        from ...models.communication import Communication

        communication = Communication(
            channel=config.get("channel", "system"),
            direction="outbound",
            message_content=message_content,
            message_type=config.get("message_type", "notification"),
            customer_id=(
                entity_data.get("customer_id")
                if entity_type == EntityType.CUSTOMER
                else None
            ),
            order_id=entity_data.get("id") if entity_type == EntityType.ORDER else None,
            user_id=config.get("user_id", 1),  # Системный пользователь
            intent=config.get("intent"),
            extra_data={
                "automation_triggered": True,
                "robot_action": "create_message",
                "entity_type": entity_type.value,
                "entity_id": entity_id,
            },
        )

        self.db.add(communication)
        self.db.commit()
        self.db.refresh(communication)

        return {
            "status": "message_created",
            "communication_id": communication.id,
            "channel": communication.channel,
            "content": (
                message_content[:100] + "..."
                if len(message_content) > 100
                else message_content
            ),
        }

    async def _execute_create_task(
        self, action_config: RobotActionConfig, entity_type: EntityType, entity_id: int
    ) -> Dict[str, Any]:
        """Создание задачи через робота"""
        config = action_config.config or {}

        task_data = {
            "title": config.get("title", "Автоматическая задача"),
            "description": config.get("description", ""),
            "assigned_to": config.get("assigned_to"),
            "priority": config.get("priority", "medium"),
            "deadline": config.get("deadline"),
        }

        # Создаем задачу через сервис
        task_service = TaskService(self.db)
        created_task = task_service.create_task(
            self.db,
            task_data,
            created_by=config.get("created_by", 1),  # Системный пользователь
        )

        return {
            "status": "task_created",
            "task_id": created_task.id,
            "task_title": created_task.title,
        }

    async def _execute_update_task_status(
        self, action_config: RobotActionConfig, entity_type: EntityType, entity_id: int
    ) -> Dict[str, Any]:
        """Обновление статуса задачи"""
        config = action_config.config or {}

        task_id = (
            config.get("task_id") or entity_id
        )  # Если не указан, используем текущую сущность
        new_status = config.get("status")

        if not new_status:
            raise ValueError("Status not specified for task update")

        # Обновляем задачу
        task_service = TaskService(self.db)
        task_service.update_task(self.db, task_id, {"status": new_status})

        return {"status": "task_updated", "task_id": task_id, "new_status": new_status}

    async def _execute_create_production_step(
        self, action_config: RobotActionConfig, entity_type: EntityType, entity_id: int
    ) -> Dict[str, Any]:
        """Создание этапа производства"""
        config = action_config.config or {}

        order_id = config.get("order_id") or entity_id
        name = config.get("name", "Автоматический этап")
        description = config.get("description", "")
        estimated_hours = config.get("estimated_hours", 1.0)
        assigned_user_id = config.get("assigned_user_id")

        # Создаем этап через сервис производства
        production_service = ProductionService(self.db)
        created_step = production_service.create_single_production_step(
            order_id=order_id,
            name=name,
            description=description,
            estimated_hours=estimated_hours,
            assigned_user_id=assigned_user_id,
        )

        return {
            "status": "production_step_created",
            "step_id": created_step.id,
            "step_name": created_step.name,
            "order_id": created_step.order_id,
            "sequence_number": created_step.sequence_number,
            "estimated_hours": created_step.estimated_hours,
            "assigned_user_id": created_step.assigned_user_id,
        }

    async def _execute_update_order_status(
        self, action_config: RobotActionConfig, entity_type: EntityType, entity_id: int
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
            "new_status": new_status,
        }

    async def _execute_notify_user(
        self, action_config: RobotActionConfig, entity_type: EntityType, entity_id: int
    ) -> Dict[str, Any]:
        """Уведомление пользователя"""
        config = action_config.config or {}

        user_id = config.get("user_id")
        message = config.get("message", "Системное уведомление")
        notification_type = config.get("type", "info")

        # Получаем данные сущности для подстановки
        entity_data = await self._get_entity_data(entity_type, entity_id)
        message = self._replace_placeholders(message, entity_data)

        # Получаем email пользователя
        from ...models.user import User

        user = self.db.query(User).filter(User.id == user_id).first()

        if not user or not user.email:
            logger.warning(f"User {user_id} not found or has no email")
            return {
                "status": "user_not_found",
                "user_id": user_id,
                "message": message,
                "type": notification_type,
            }

        # Отправляем уведомление по email
        from ...services.email_service import EmailMessage, email_service

        subject = f"Уведомление: {notification_type}"
        email_message = EmailMessage(to=user.email, subject=subject, body=message)

        success = await email_service.send_email(email_message)

        return {
            "status": "user_notified" if success else "notification_failed",
            "user_id": user_id,
            "user_email": user.email,
            "message": message,
            "type": notification_type,
            "success": success,
        }

    async def _execute_notify_group(
        self, action_config: RobotActionConfig, entity_type: EntityType, entity_id: int
    ) -> Dict[str, Any]:
        """Уведомление группы пользователей"""
        config = action_config.config or {}

        group_id = config.get("group_id")
        message = config.get("message", "Системное уведомление группы")
        notification_type = config.get("type", "info")
        channel = config.get("channel", "email")  # email, sms, telegram

        if not group_id:
            raise ValueError("Group ID not specified for group notification")

        # Получаем данные сущности для подстановки
        entity_data = await self._get_entity_data(entity_type, entity_id)
        message = self._replace_placeholders(message, entity_data)

        # Получаем пользователей группы
        group_users = await self._get_group_users(group_id)

        if not group_users:
            logger.warning(f"No users found in group {group_id}")
            return {
                "status": "group_not_found",
                "group_id": group_id,
                "message": message,
                "type": notification_type,
                "users_notified": 0,
            }

        # Отправляем уведомления всем пользователям группы
        notified_count = 0
        failed_count = 0
        results = []

        for user in group_users:
            try:
                result = await self._notify_single_user(
                    user, message, notification_type, channel
                )
                results.append(result)

                if result.get("success", False):
                    notified_count += 1
                else:
                    failed_count += 1

            except Exception as e:
                logger.error(f"Failed to notify user {user.get('id')}: {e}")
                failed_count += 1
                results.append(
                    {"user_id": user.get("id"), "success": False, "error": str(e)}
                )

        logger.info(
            f"Group notification completed: {notified_count} notified, {failed_count} failed"
        )

        return {
            "status": "group_notified",
            "group_id": group_id,
            "message": message,
            "type": notification_type,
            "channel": channel,
            "users_notified": notified_count,
            "users_failed": failed_count,
            "total_users": len(group_users),
            "results": results,
        }

    async def _execute_update_field(
        self, action_config: RobotActionConfig, entity_type: EntityType, entity_id: int
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
            "value": field_value,
        }

    async def _execute_create_communication(
        self, action_config: RobotActionConfig, entity_type: EntityType, entity_id: int
    ) -> Dict[str, Any]:
        """Создание записи коммуникации"""
        config = action_config.config or {}

        # Получаем данные сущности для подстановки
        entity_data = await self._get_entity_data(entity_type, entity_id)

        # Создаем объект коммуникации
        from ...models.communication import Communication

        communication = Communication(
            channel=config.get("channel", "system"),
            direction=config.get("direction", "outbound"),
            message_content=self._replace_placeholders(
                config.get("content", "Автоматическая коммуникация"), entity_data
            ),
            message_type=config.get("message_type", "notification"),
            customer_id=(
                entity_data.get("customer_id")
                if entity_type == EntityType.CUSTOMER
                else None
            ),
            order_id=entity_data.get("id") if entity_type == EntityType.ORDER else None,
            task_id=entity_data.get("id") if entity_type == EntityType.TASK else None,
            user_id=config.get("user_id", 1),  # Системный пользователь по умолчанию
            intent=config.get("intent"),
            extra_data={
                "automation_triggered": True,
                "robot_action": "create_communication",
                "entity_type": entity_type.value,
                "entity_id": entity_id,
                "config": config,
            },
            status=config.get("status", "sent"),
        )

        # Сохраняем в базу данных
        self.db.add(communication)
        self.db.commit()
        self.db.refresh(communication)

        logger.info(
            f"Communication record created: ID {communication.id}, channel {communication.channel}"
        )

        return {
            "status": "communication_created",
            "communication_id": communication.id,
            "channel": communication.channel,
            "direction": communication.direction,
            "message_type": communication.message_type,
            "content": (
                communication.message_content[:100] + "..."
                if len(communication.message_content or "") > 100
                else communication.message_content
            ),
            "customer_id": communication.customer_id,
            "order_id": communication.order_id,
            "task_id": communication.task_id,
            "user_id": communication.user_id,
            "intent": communication.intent,
        }

    async def _execute_analyze_intent(
        self, action_config: RobotActionConfig, entity_type: EntityType, entity_id: int
    ) -> Dict[str, Any]:
        """Анализ намерения через AI"""
        config = action_config.config or {}

        # Получаем текст для анализа
        text_to_analyze = config.get("text") or await self._get_entity_text(
            entity_type, entity_id
        )

        # Интеграция с AI сервисом для анализа намерения
        try:
            from ...services.ai.intent_service import AIIntentService

            ai_service = AIIntentService()

            # Получаем контекст сущности для лучшего анализа
            context = await self._get_entity_context(entity_type, entity_id)

            # Анализируем намерение
            intent = await ai_service.analyze_intent(text_to_analyze, context)

            logger.info(
                f"Intent analyzed: {intent} for text length {len(text_to_analyze)}"
            )

            return {
                "status": "intent_analyzed",
                "text_length": len(text_to_analyze),
                "intent": intent.value if hasattr(intent, "value") else str(intent),
                "confidence": 0.85,  # Можно получить из AI сервиса
                "analysis_result": "success",
            }

        except Exception as e:
            logger.error(f"AI intent analysis failed: {e}")
            return {
                "status": "intent_analysis_failed",
                "text_length": len(text_to_analyze),
                "error": str(e),
                "analysis_result": "failed",
            }

    async def _execute_generate_response(
        self, action_config: RobotActionConfig, entity_type: EntityType, entity_id: int
    ) -> Dict[str, Any]:
        """Генерация ответа через AI"""
        config = action_config.config or {}

        # Получаем контекст для генерации
        context_str = config.get("context") or await self._get_entity_context(
            entity_type, entity_id
        )

        # Интеграция с AI сервисом для генерации ответа
        try:
            from ...services.ai.intent_service import AIIntentService

            ai_service = AIIntentService()

            # Получаем текст для анализа намерения
            text_to_analyze = config.get("text") or await self._get_entity_text(
                entity_type, entity_id
            )

            # Анализируем намерение и генерируем ответ
            intent = await ai_service.analyze_intent(
                text_to_analyze, {"context": context_str}
            )
            response = await ai_service.generate_response(
                intent, text_to_analyze, {"context": {"context": context_str}}
            )

            logger.info(f"Response generated for intent {intent}: {response[:100]}...")

            return {
                "status": "response_generated",
                "context_length": len(context_str),
                "intent": intent.value if hasattr(intent, "value") else str(intent),
                "generated_response": response,
                "response_type": "ai_generated",
            }

        except Exception as e:
            logger.error(f"AI response generation failed: {e}")
            return {
                "status": "response_generation_failed",
                "context_length": len(context_str),
                "error": str(e),
                "generated_response": "Извините, произошла ошибка при генерации ответа. Мы свяжемся с вами в ближайшее время.",
            }

    async def _execute_send_standard_response(
        self, action_config: RobotActionConfig, entity_type: EntityType, entity_id: int
    ) -> Dict[str, Any]:
        """Отправка стандартного ответа"""
        config = action_config.config or {}

        response_text = config.get(
            "response_text",
            "Спасибо за обращение. Мы свяжемся с вами в ближайшее время.",
        )
        channel = config.get("channel", "email")  # email, telegram, sms

        # Получаем данные сущности для подстановки
        entity_data = await self._get_entity_data(entity_type, entity_id)
        response_text = self._replace_placeholders(response_text, entity_data)

        # Получаем данные получателя
        recipient_data = await self._get_recipient_data(entity_type, entity_id, channel)

        # Отправляем через соответствующий канал
        result = await self._send_via_channel(channel, response_text, recipient_data)

        return {
            "status": (
                "standard_response_sent"
                if result.get("success")
                else "standard_response_failed"
            ),
            "channel": channel,
            "response_text": response_text,
            "success": result.get("success", False),
            "error": result.get("error"),
        }

    async def _execute_escalate_complex_query(
        self, action_config: RobotActionConfig, entity_type: EntityType, entity_id: int
    ) -> Dict[str, Any]:
        """Эскалация сложного запроса"""
        config = action_config.config or {}

        escalation_reason = config.get(
            "reason", "Сложный запрос требует ручной обработки"
        )
        target_user_id = config.get("target_user_id")
        priority = config.get("priority", "high")

        # Создаем задачу для эскалации
        task_data = {
            "title": f"Эскалация: {escalation_reason}",
            "description": f"Автоматическая эскалация для сущности {entity_type.value} ID {entity_id}",
            "assigned_to": target_user_id,
            "priority": priority,
        }

        # Создаем задачу
        task_service = TaskService(self.db)
        created_task = await task_service.create_task(
            self.db, task_data, created_by=1  # Системный пользователь
        )

        return {
            "status": "query_escalated",
            "task_id": created_task.id,
            "reason": escalation_reason,
            "priority": priority,
        }

    # Новые действия для расширенной автоматизации

    async def _execute_call_external_api(
        self, action_config: RobotActionConfig, entity_type: EntityType, entity_id: int
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
            bearer_token=bearer_token,
        )

        return {
            "status": "api_called",
            "method": method,
            "url": url,
            "success": result.get("success", False),
            "status_code": result.get("status_code"),
            "response": result.get("json") or result.get("text", "")[:500],
        }

    async def _execute_call_webhook(
        self, action_config: RobotActionConfig, entity_type: EntityType, entity_id: int
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
            "automation_triggered": True,
        }

        # Выполняем вызов webhook
        result = await external_api_service.call_webhook(
            url=url, event_type=event_type, payload=payload, secret=secret
        )

        return {
            "status": "webhook_called",
            "url": url,
            "event_type": event_type,
            "success": result.get("success", False),
            "status_code": result.get("status_code"),
        }

    async def _execute_call_graphql(
        self, action_config: RobotActionConfig, entity_type: EntityType, entity_id: int
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
            url=url, query=query, variables=variables, headers=headers
        )

        return {
            "status": "graphql_called",
            "url": url,
            "success": result.get("success", False),
            "status_code": result.get("status_code"),
            "data": result.get("json", {}).get("data"),
            "errors": result.get("json", {}).get("errors"),
        }

    async def _execute_call_soap(
        self, action_config: RobotActionConfig, entity_type: EntityType, entity_id: int
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
            url=url, soap_action=soap_action, soap_body=soap_body, headers=headers
        )

        return {
            "status": "soap_called",
            "url": url,
            "soap_action": soap_action,
            "success": result.get("success", False),
            "status_code": result.get("status_code"),
            "response_length": len(result.get("text", "")),
        }

    async def _execute_create_calendar_event(
        self, action_config: RobotActionConfig, entity_type: EntityType, entity_id: int
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
            start_time=start_time or "",
            end_time=end_time or "",
            attendees=attendees,
            calendar_id=calendar_id,
            provider=provider or "google",
        )

        return {
            "status": (
                "calendar_event_created"
                if result.get("success")
                else "calendar_event_failed"
            ),
            "title": title,
            "start_time": start_time,
            "end_time": end_time,
            "attendees_count": len(attendees),
            "event_id": result.get("event_id"),
            "provider": result.get("provider"),
            "success": result.get("success", False),
            "error": result.get("error"),
        }

    async def _execute_update_calendar_event(
        self, action_config: RobotActionConfig, entity_type: EntityType, entity_id: int
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
            provider=provider or "google",
        )

        return {
            "status": (
                "calendar_event_updated"
                if result.get("success")
                else "calendar_event_update_failed"
            ),
            "event_id": event_id,
            "updates": updates,
            "provider": result.get("provider"),
            "success": result.get("success", False),
            "error": result.get("error"),
        }

    async def _execute_send_calendar_invite(
        self, action_config: RobotActionConfig, entity_type: EntityType, entity_id: int
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
            provider=provider or "google",
        )

        return {
            "status": (
                "calendar_invites_sent"
                if result.get("success")
                else "calendar_invites_failed"
            ),
            "event_id": event_id,
            "attendees_count": len(attendees),
            "provider": result.get("provider"),
            "success": result.get("success", False),
            "error": result.get("error"),
        }

    # Вспомогательные методы

    async def _get_entity_data(
        self, entity_type: EntityType, entity_id: int
    ) -> Dict[str, Any]:
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

    async def _render_email_template(
        self, template_name: str, data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Рендеринг шаблона email"""
        try:
            # Расширенная система шаблонов
            templates = {
                "welcome": {
                    "subject": "Добро пожаловать в нашу систему!",
                    "body": f"""
Здравствуйте, {data.get('name', 'уважаемый клиент')}!

Спасибо за регистрацию в нашей системе печати на текстиле.

Ваши данные:
- Email: {data.get('email', 'N/A')}
- Телефон: {data.get('phone', 'N/A')}

Теперь вы можете:
• Размещать заказы на печать
• Отслеживать статус выполнения
• Получать персональные предложения

Для начала работы войдите в систему по ссылке: https://app.company.com

Если у вас есть вопросы, звоните: +7 (XXX) XXX-XX-XX

С уважением,
Команда Company
                    """.strip(),
                    "html_body": f"""
<html>
<body>
<h2>Добро пожаловать, {data.get('name', 'уважаемый клиент')}!</h2>
<p>Спасибо за регистрацию в нашей системе печати на текстиле.</p>

<p><strong>Ваши данные:</strong></p>
<ul>
<li>Email: {data.get('email', 'N/A')}</li>
<li>Телефон: {data.get('phone', 'N/A')}</li>
</ul>

<p><strong>Теперь вы можете:</strong></p>
<ul>
<li>Размещать заказы на печать</li>
<li>Отслеживать статус выполнения</li>
<li>Получать персональные предложения</li>
</ul>

<p><a href="https://app.company.com">Войти в систему</a></p>

<p>Если у вас есть вопросы, звоните: +7 (XXX) XXX-XX-XX</p>

<p>С уважением,<br>Команда Company</p>
</body>
</html>
                    """.strip(),
                },
                "order_confirmation": {
                    "subject": f"Заказ #{data.get('id', 'N/A')} подтвержден",
                    "body": f"""
Здравствуйте, {data.get('customer_name', 'клиент')}!

Ваш заказ #{data.get('id', 'N/A')} успешно принят в обработку.

Информация о заказе:
- Тип услуги: {data.get('service_type', 'печать')}
- Статус: {data.get('status', 'принят')}
- Ориентировочная дата готовности: {data.get('due_date', 'через 3-5 дней')}

Стоимость: {data.get('total_price', 'N/A')} руб.

Отследить заказ: https://app.company.com/orders/{data.get('id', '')}

При возникновении вопросов звоните: +7 (XXX) XXX-XX-XX

Спасибо за выбор нашей компании!
                    """.strip(),
                    "html_body": f"""
<html>
<body>
<h2>Заказ #{data.get('id', 'N/A')} подтвержден</h2>

<p>Здравствуйте, {data.get('customer_name', 'клиент')}!</p>

<p>Ваш заказ успешно принят в обработку.</p>

<h3>Информация о заказе:</h3>
<ul>
<li><strong>Тип услуги:</strong> {data.get('service_type', 'печать')}</li>
<li><strong>Статус:</strong> {data.get('status', 'принят')}</li>
<li><strong>Дата готовности:</strong> {data.get('due_date', 'через 3-5 дней')}</li>
<li><strong>Стоимость:</strong> {data.get('total_price', 'N/A')} руб.</li>
</ul>

<p><a href="https://app.company.com/orders/{data.get('id', '')}">Отследить заказ</a></p>

<p>При возникновении вопросов звоните: +7 (XXX) XXX-XX-XX</p>

<p><strong>Спасибо за выбор нашей компании!</strong></p>
</body>
</html>
                    """.strip(),
                },
                "order_ready": {
                    "subject": f"Заказ #{data.get('id', 'N/A')} готов к выдаче",
                    "body": f"""
Здравствуйте, {data.get('customer_name', 'клиент')}!

Ваш заказ #{data.get('id', 'N/A')} готов к выдаче.

Адрес самовывоза: ул. Примерная, д. 123
Режим работы: Пн-Пт 9:00-18:00, Сб 10:00-16:00

Не забудьте взять паспорт для получения заказа.

С уважением,
Команда Company
                    """.strip(),
                },
                "payment_reminder": {
                    "subject": f"Напоминание об оплате заказа #{data.get('id', 'N/A')}",
                    "body": f"""
Здравствуйте, {data.get('customer_name', 'клиент')}!

Напоминаем о необходимости оплаты заказа #{data.get('id', 'N/A')}.

Сумма к оплате: {data.get('amount', 'N/A')} руб.
Срок оплаты: {data.get('due_date', 'сегодня')}

Способы оплаты:
• Банковский перевод
• Оплата картой на сайте
• Наличными при получении

Оплатить: https://app.company.com/payment/{data.get('id', '')}

С уважением,
Команда Company
                    """.strip(),
                },
            }

            # Получаем шаблон
            template = templates.get(template_name)
            if not template:
                # Создаем базовый шаблон если не найден
                template = {
                    "subject": f"Уведомление: {template_name}",
                    "body": f"""
Здравствуйте!

{data.get('message', 'У вас новое уведомление от системы.')}

{'Дополнительная информация: ' + str(data) if data else ''}

С уважением,
Команда Company
                    """.strip(),
                }

            # Заменяем плейсхолдеры в шаблоне
            for key, value in data.items():
                placeholder = f"{{{key}}}"
                if isinstance(template.get("subject"), str):
                    template["subject"] = template["subject"].replace(
                        placeholder, str(value) if value is not None else ""
                    )
                if isinstance(template.get("body"), str):
                    template["body"] = template["body"].replace(
                        placeholder, str(value) if value is not None else ""
                    )
                if isinstance(template.get("html_body"), str):
                    template["html_body"] = template["html_body"].replace(
                        placeholder, str(value) if value is not None else ""
                    )

            return template

        except Exception as e:
            logger.error(f"Failed to render email template {template_name}: {e}")
            return {
                "subject": f"Ошибка в шаблоне {template_name}",
                "body": f"Произошла ошибка при формировании письма: {str(e)}",
                "error": str(e),
            }

    async def _get_recipient_email(
        self, entity_type: EntityType, entity_id: int, config: Dict[str, Any]
    ) -> str:
        """Получение email получателя"""
        # Проверяем конфиг
        if isinstance(config, dict) and config.get("email"):
            return str(config["email"])

        # Получаем из сущности
        if entity_type == EntityType.CUSTOMER:
            customer = self.db.query(Customer).filter(Customer.id == entity_id).first()
            return str(customer.email) if customer and customer.email else ""

        return ""

    async def _get_recipient_phone(
        self, entity_type: EntityType, entity_id: int, config: Dict[str, Any]
    ) -> str:
        """Получение номера телефона"""
        # Проверяем конфиг
        if isinstance(config, dict) and config.get("phone"):
            return str(config["phone"])

        # Получаем из сущности
        if entity_type == EntityType.CUSTOMER:
            customer = self.db.query(Customer).filter(Customer.id == entity_id).first()
            return str(customer.phone) if customer and customer.phone else ""

        return ""

    async def _get_recipient_data(
        self, entity_type: EntityType, entity_id: int, channel: str
    ) -> Dict[str, Any]:
        """Получение данных получателя для отправки через канал"""
        try:
            if channel == "email":
                email = await self._get_recipient_email(entity_type, entity_id, {})
                return {"email": email} if email else {}
            elif channel == "sms":
                phone = await self._get_recipient_phone(entity_type, entity_id, {})
                return {"phone": phone} if phone else {}
            elif channel == "telegram":
                # Для Telegram получаем ID из конфига или сущности
                if entity_type == EntityType.CUSTOMER:
                    customer = (
                        self.db.query(Customer).filter(Customer.id == entity_id).first()
                    )
                    telegram_id = (
                        getattr(customer, "telegram_id", None) if customer else None
                    )
                    return {"telegram_id": telegram_id} if telegram_id else {}
                return {}
            else:
                return {}
        except Exception as e:
            logger.error(
                f"Failed to get recipient data for {entity_type} {entity_id} via {channel}: {e}"
            )
            return {}

    async def _send_via_channel(
        self, channel: str, response: str, recipient_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Отправка через соответствующий канал"""
        try:
            channel = channel.lower()

            if channel == "email":
                # Отправка по email
                from ...services.email_service import EmailMessage, email_service

                recipient_email = recipient_data.get("email")
                if not recipient_email:
                    raise ValueError("Email recipient not specified")

                message = EmailMessage(
                    to=recipient_email, subject="Автоматический ответ", body=response
                )

                success = await email_service.send_email(message)

            elif channel == "telegram":
                # Отправка через Telegram
                from ...services.telegram_bot_service import telegram_bot_service

                telegram_id = recipient_data.get("telegram_id")
                if not telegram_id:
                    raise ValueError("Telegram ID not specified")

                result = await telegram_bot_service.send_message(
                    chat_id=str(telegram_id), text=response
                )
                success = result.get("success", False)

            elif channel == "sms":
                # Отправка SMS
                from ...services.sms_service import sms_service

                phone = recipient_data.get("phone")
                if not phone:
                    raise ValueError("Phone number not specified")

                result = await sms_service.send_sms(phone, response)
                success = result.get("success", False)

            else:
                logger.warning(f"Unsupported channel: {channel}")
                return {
                    "success": False,
                    "error": f"Channel '{channel}' is not supported",
                }

            return {"success": success}

        except Exception as e:
            logger.error(f"Failed to send response via {channel}: {e}")
            return {"success": False, "error": str(e)}

    async def _get_entity_text(self, entity_type: EntityType, entity_id: int) -> str:
        """Получение текста для анализа"""
        try:
            if entity_type == EntityType.CUSTOMER:
                customer = (
                    self.db.query(Customer).filter(Customer.id == entity_id).first()
                )
                if customer:
                    # Собираем текстовую информацию о клиенте
                    text_parts = []
                    if customer.name:
                        text_parts.append(f"Имя: {customer.name}")
                    if customer.email:
                        text_parts.append(f"Email: {customer.email}")
                    if customer.phone:
                        text_parts.append(f"Телефон: {customer.phone}")
                    if customer.company:
                        text_parts.append(f"Компания: {customer.company}")
                    if customer.notes:
                        text_parts.append(f"Заметки: {customer.notes}")

                    return " | ".join(text_parts) if text_parts else "Новый клиент"

            elif entity_type == EntityType.ORDER:
                order = self.db.query(Order).filter(Order.id == entity_id).first()
                if order:
                    # Собираем текстовую информацию о заказе
                    text_parts = []
                    text_parts.append(f"Заказ #{order.id}")
                    if order.description:
                        text_parts.append(f"Описание: {order.description}")
                    if order.status:
                        text_parts.append(f"Статус: {order.status.value}")
                    if order.total_amount:
                        text_parts.append(f"Сумма: {order.total_amount} руб.")
                    if order.notes:
                        text_parts.append(f"Заметки: {order.notes}")

                    return " | ".join(text_parts)

            elif entity_type == EntityType.TASK:
                task = self.db.query(Task).filter(Task.id == entity_id).first()
                if task:
                    # Собираем текстовую информацию о задаче
                    text_parts = []
                    text_parts.append(f"Задача: {task.title}")
                    if task.description:
                        text_parts.append(f"Описание: {task.description}")
                    if task.status:
                        text_parts.append(f"Статус: {task.status.value}")
                    if task.priority:
                        text_parts.append(f"Приоритет: {task.priority}")

                    return " | ".join(text_parts)

            logger.warning(f"Unknown entity type for text extraction: {entity_type}")
            return f"Неизвестный тип сущности: {entity_type}"

        except Exception as e:
            logger.error(
                f"Failed to get entity text for {entity_type} {entity_id}: {e}"
            )
            return f"Ошибка получения текста: {str(e)}"

    async def _get_entity_context(self, entity_type: EntityType, entity_id: int) -> str:
        """Получение контекста для генерации ответа"""
        try:
            context_parts = []

            if entity_type == EntityType.CUSTOMER:
                from ...models.communication import Communication
                from ...models.customer import Customer
                from ...models.order import Order

                customer = (
                    self.db.query(Customer).filter(Customer.id == entity_id).first()
                )
                if customer:
                    context_parts.append(f"Клиент: {customer.name or 'Неизвестный'}")
                    context_parts.append(f"Email: {customer.email or 'Не указан'}")
                    context_parts.append(f"Телефон: {customer.phone or 'Не указан'}")

                    # Получаем статистику заказов
                    orders = (
                        self.db.query(Order)
                        .filter(Order.customer_id == entity_id)
                        .all()
                    )
                    orders_count = len(orders)
                    context_parts.append(f"Количество заказов: {orders_count}")

                    if orders_count > 0:
                        total_spent = sum(order.total_amount or 0 for order in orders)
                        context_parts.append(f"Общая сумма заказов: {total_spent} руб.")

                        completed_orders = sum(
                            1
                            for order in orders
                            if order.status == OrderStatus.COMPLETED
                        )
                        context_parts.append(f"Завершенных заказов: {completed_orders}")

                    if customer.company:
                        context_parts.append(f"Компания: {customer.company}")

                    if customer.notes:
                        context_parts.append(f"Заметки: {customer.notes}")

                    # Определяем статус клиента
                    if orders_count > 10:
                        context_parts.append("Статус: VIP клиент")
                    elif orders_count > 5:
                        context_parts.append("Статус: Постоянный клиент")
                    elif orders_count > 0:
                        context_parts.append("Статус: Активный клиент")
                    else:
                        context_parts.append("Статус: Новый клиент")

                    # Получаем последние коммуникации
                    recent_communications = (
                        self.db.query(Communication)
                        .filter(Communication.customer_id == entity_id)
                        .order_by(Communication.created_at.desc())
                        .limit(3)
                        .all()
                    )

                    if recent_communications:
                        context_parts.append("Последние взаимодействия:")
                        for comm in recent_communications:
                            context_parts.append(
                                f"  - {comm.channel}: {comm.message_content[:50]}..."
                                if len(comm.message_content or "") > 50
                                else f"  - {comm.channel}: {comm.message_content}"
                            )

            elif entity_type == EntityType.ORDER:
                from ...models.customer import Customer
                from ...models.order import Order
                from ...models.production_step import ProductionStep
                from ...models.task import Task

                order = self.db.query(Order).filter(Order.id == entity_id).first()
                if order:
                    context_parts.append(f"Заказ #{order.id}")
                    context_parts.append(
                        f"Статус: {order.status.value if order.status else 'Неизвестен'}"
                    )

                    if order.customer:
                        context_parts.append(
                            f"Клиент: {order.customer.name or 'Неизвестный'}"
                        )
                        context_parts.append(
                            f"Email клиента: {order.customer.email or 'Не указан'}"
                        )

                    if order.description:
                        context_parts.append(f"Описание: {order.description}")

                    if order.total_amount:
                        context_parts.append(f"Стоимость: {order.total_amount} руб.")

                    if order.created_at:
                        context_parts.append(
                            f"Дата создания: {order.created_at.strftime('%Y-%m-%d %H:%M')}"
                        )

                    # Получаем этапы производства
                    steps = (
                        self.db.query(ProductionStep)
                        .filter(ProductionStep.order_id == order.id)
                        .all()
                    )
                    if steps:
                        completed_steps = sum(
                            1 for step in steps if step.status == "completed"
                        )
                        in_progress_steps = sum(
                            1 for step in steps if step.status == "in_progress"
                        )
                        context_parts.append(
                            f"Этапы производства: {completed_steps}/{len(steps)} завершено, {in_progress_steps} в работе"
                        )

                        # Детали этапов
                        context_parts.append("Этапы:")
                        for step in sorted(steps, key=lambda s: s.sequence_number):
                            status_emoji = (
                                "✅"
                                if step.status == "completed"
                                else "🔄" if step.status == "in_progress" else "⏳"
                            )
                            context_parts.append(
                                f"  {status_emoji} {step.name} ({step.estimated_hours}ч)"
                            )

                    # Получаем связанные задачи
                    tasks = self.db.query(Task).filter(Task.order_id == order.id).all()
                    if tasks:
                        completed_tasks = sum(
                            1 for task in tasks if task.status == "completed"
                        )
                        context_parts.append(
                            f"Связанные задачи: {completed_tasks}/{len(tasks)} завершено"
                        )

                    if order.notes:
                        context_parts.append(f"Заметки: {order.notes}")

            elif entity_type == EntityType.TASK:
                from ...models.order import Order
                from ...models.task import Task

                task = self.db.query(Task).filter(Task.id == entity_id).first()
                if task:
                    context_parts.append(f"Задача: {task.title}")
                    context_parts.append(
                        f"Статус: {task.status.value if task.status else 'Неизвестен'}"
                    )
                    context_parts.append(f"Приоритет: {task.priority or 'Не указан'}")

                    if task.assigned_to and task.assigned_user:
                        context_parts.append(
                            f"Исполнитель: {task.assigned_user.name or 'Неизвестен'}"
                        )

                    if task.description:
                        context_parts.append(f"Описание: {task.description}")

                    if task.deadline:
                        context_parts.append(
                            f"Дедлайн: {task.deadline.strftime('%Y-%m-%d %H:%M')}"
                        )

                    if task.created_at:
                        context_parts.append(
                            f"Дата создания: {task.created_at.strftime('%Y-%m-%d %H:%M')}"
                        )

                    if task.order:
                        context_parts.append(
                            f"Связан с заказом: #{task.order.id} ({task.order.status.value if task.order.status else 'Неизвестен'})"
                        )

                    if task.notes:
                        context_parts.append(f"Заметки: {task.notes}")

            # Добавляем общую информацию
            context_parts.append(f"Тип сущности: {entity_type.value}")
            context_parts.append(f"ID сущности: {entity_id}")
            context_parts.append(
                f"Время запроса: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
            )

            return " | ".join(context_parts)

        except Exception as e:
            logger.error(
                f"Failed to get entity context for {entity_type} {entity_id}: {e}"
            )
            return f"Ошибка получения контекста: {str(e)} | Тип: {entity_type.value} | ID: {entity_id}"

    def _replace_placeholders(self, text: str, data: Dict[str, Any]) -> str:
        """Замена плейсхолдеров в строке"""
        if not text:
            return text

        for key, value in data.items():
            if value is not None:
                placeholder = f"{{{key}}}"
                text = text.replace(placeholder, str(value))

        return text

    def _replace_placeholders_in_dict(
        self, data: Dict[str, Any], entity_data: Dict[str, Any]
    ) -> Dict[str, Any]:
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
                    (
                        self._replace_placeholders_in_dict(item, entity_data)
                        if isinstance(item, dict)
                        else (
                            self._replace_placeholders(item, entity_data)
                            if isinstance(item, str)
                            else item
                        )
                    )
                    for item in value
                ]
            else:
                result[key] = value

        return result

    def _is_error_critical(self, error_message: str, action_type: RobotAction) -> bool:
        """
        Определяет, является ли ошибка критической для остановки выполнения последовательности

        Args:
            error_message: Сообщение об ошибке
            action_type: Тип действия, при котором произошла ошибка

        Returns:
            bool: True если ошибка критическая и нужно остановить выполнение
        """
        # Критические ошибки, которые всегда останавливают выполнение
        critical_patterns = [
            "authentication failed",
            "authorization failed",
            "permission denied",
            "database connection failed",
            "service unavailable",
            "internal server error",
            "invalid credentials",
            "quota exceeded",
            "rate limit exceeded",
            "foreign key constraint",
            "unique constraint",
            "not null constraint",
        ]

        error_lower = error_message.lower()

        # Проверяем на критические паттерны
        for pattern in critical_patterns:
            if pattern in error_lower:
                return True

        # Критические действия - если они падают, останавливаем выполнение
        critical_actions = [
            RobotAction.UPDATE_ORDER_STATUS,  # Изменение статуса заказа критично
            RobotAction.UPDATE_TASK_STATUS,  # Изменение статуса задачи критично
            RobotAction.UPDATE_FIELD,  # Изменение полей сущностей критично
            RobotAction.CREATE_TASK,  # Создание задач обычно критично
            RobotAction.ESCALATE_COMPLEX_QUERY,  # Эскалация должна выполниться
        ]

        if action_type in critical_actions:
            return True

        # Некритические действия - продолжаем выполнение при ошибках
        non_critical_actions = [
            RobotAction.SEND_EMAIL,  # Email может не отправиться - не критично
            RobotAction.SEND_SMS,  # SMS может не отправиться - не критично
            RobotAction.SEND_TELEGRAM,  # Telegram может не отправиться - не критично
            RobotAction.NOTIFY_USER,  # Уведомления могут не отправиться - не критично
            RobotAction.NOTIFY_GROUP,  # Групповые уведомления могут не отправиться - не критично
            RobotAction.CREATE_MESSAGE,  # Создание сообщений может не выполниться - не критично
            RobotAction.ANALYZE_INTENT,  # Анализ намерения может упасть - не критично
            RobotAction.GENERATE_RESPONSE,  # Генерация ответа может упасть - не критично
            RobotAction.CALL_EXTERNAL_API,  # Внешние API могут быть недоступны - не критично
            RobotAction.CALL_WEBHOOK,  # Webhook может быть недоступен - не критично
            RobotAction.CREATE_CALENDAR_EVENT,  # Календарь может быть недоступен - не критично
        ]

        if action_type in non_critical_actions:
            return False

        # По умолчанию считаем ошибку некритической для продолжения выполнения
        return False

    async def _get_group_users(self, group_identifier: str) -> List[Dict[str, Any]]:
        """
        Получение списка пользователей группы

        Args:
            group_identifier: Идентификатор группы (роль или специальный ID)

        Returns:
            List[Dict] с данными пользователей
        """
        try:
            from ...models.user import User

            # Поддерживаемые группы на основе ролей
            role_groups = {
                "admin": "admin",
                "admins": "admin",
                "администраторы": "admin",
                "manager": "manager",
                "managers": "manager",
                "менеджеры": "manager",
                "user": "user",
                "users": "user",
                "пользователи": "user",
                "all": "all_users",
                "все": "all_users",
            }

            if group_identifier in role_groups:
                role_filter = role_groups[group_identifier]

                if role_filter == "all_users":
                    users = self.db.query(User).filter(User.is_active == True).all()
                else:
                    users = (
                        self.db.query(User)
                        .filter(User.role == role_filter, User.is_active == True)
                        .all()
                    )
            else:
                # Для числовых ID групп можно добавить логику позже
                # Пока поддерживаем только роли
                try:
                    numeric_id = int(group_identifier)
                    logger.warning(
                        f"Numeric group IDs not implemented yet, got: {numeric_id}"
                    )
                    return []
                except ValueError:
                    logger.warning(f"Unknown group identifier: {group_identifier}")
                    return []

            # Преобразуем в словарь для удобства
            result = []
            for user in users:
                result.append(
                    {
                        "id": user.id,
                        "name": user.full_name or user.email,
                        "email": user.email,
                        "phone": getattr(user, "phone", None),
                        "telegram_id": getattr(user, "telegram_id", None),
                        "role": user.role,
                    }
                )

            logger.info(f"Found {len(result)} users in group '{group_identifier}'")
            return result

        except Exception as e:
            logger.error(
                f"Failed to get group users for group '{group_identifier}': {e}"
            )
            return []

    # Публичные методы для внешнего использования

    async def send_telegram_message(
        self, telegram_id: str, message: str
    ) -> Dict[str, Any]:
        """Отправка сообщения в Telegram Bot API"""
        try:
            from ...services.telegram_bot_service import telegram_bot_service

            # Используем метод send_message_to_chat из telegram_bot_service
            success = await telegram_bot_service.send_message_to_chat(
                chat_id=str(telegram_id), message=message
            )

            if success:
                return {
                    "success": True,
                    "telegram_id": telegram_id,
                    "message": message[:100] + "..." if len(message) > 100 else message,
                    "status": "telegram_sent",
                }
            else:
                return {
                    "success": False,
                    "telegram_id": telegram_id,
                    "message": message[:100] + "..." if len(message) > 100 else message,
                    "error": "Failed to send message",
                    "status": "telegram_failed",
                }

        except Exception as e:
            logger.error(f"Failed to send Telegram message to {telegram_id}: {e}")
            return {
                "success": False,
                "telegram_id": telegram_id,
                "message": message[:100] + "..." if len(message) > 100 else message,
                "error": str(e),
                "status": "telegram_failed",
            }

    async def create_communication_message(
        self, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Создание сообщения в системе коммуникаций"""
        try:
            # Получаем данные из словаря
            channel = data.get("channel", "system")
            direction = data.get("direction", "outbound")
            message_content = data.get("content", "")
            message_type = data.get("message_type", "notification")
            customer_id = data.get("customer_id")
            order_id = data.get("order_id")
            user_id = data.get("user_id", 1)
            intent = data.get("intent")
            extra_data = data.get("extra_data", {})

            # Создаем запись коммуникации
            from ...models.communication import Communication

            communication = Communication(
                channel=channel,
                direction=direction,
                message_content=message_content,
                message_type=message_type,
                customer_id=customer_id,
                order_id=order_id,
                user_id=user_id,
                intent=intent,
                extra_data=extra_data,
            )

            self.db.add(communication)
            self.db.commit()
            self.db.refresh(communication)

            logger.info(
                f"Communication message created: ID {communication.id}, channel {channel}"
            )

            return {
                "success": True,
                "communication_id": communication.id,
                "channel": channel,
                "direction": direction,
                "message_type": message_type,
                "content": (
                    message_content[:100] + "..."
                    if len(message_content) > 100
                    else message_content
                ),
            }

        except Exception as e:
            logger.error(f"Failed to create communication message: {e}")
            return {"success": False, "error": str(e), "data": data}

    async def create_production_step(
        self, order_id: int, step_name: str, **kwargs
    ) -> Dict[str, Any]:
        """Создание отдельного этапа производства"""
        try:
            description = kwargs.get("description", "")
            estimated_hours = kwargs.get("estimated_hours", 1.0)
            assigned_user_id = kwargs.get("assigned_user_id")

            # Создаем этап через сервис производства
            production_service = ProductionService(self.db)
            created_step = production_service.create_single_production_step(
                order_id=order_id,
                name=step_name,
                description=description,
                estimated_hours=estimated_hours,
                assigned_user_id=assigned_user_id,
            )

            return {
                "success": True,
                "step_id": created_step.id,
                "step_name": created_step.name,
                "order_id": created_step.order_id,
                "sequence_number": created_step.sequence_number,
                "estimated_hours": created_step.estimated_hours,
                "assigned_user_id": created_step.assigned_user_id,
            }

        except Exception as e:
            logger.error(f"Failed to create production step for order {order_id}: {e}")
            return {
                "success": False,
                "order_id": order_id,
                "step_name": step_name,
                "error": str(e),
            }

    async def notify_user(self, user_id: int, message: str, **kwargs) -> Dict[str, Any]:
        """Система уведомлений пользователей"""
        try:
            notification_type = kwargs.get("type", "info")
            channel = kwargs.get("channel", "email")

            # Получаем данные пользователя
            from ...models.user import User

            user = self.db.query(User).filter(User.id == user_id).first()

            if not user:
                return {"success": False, "user_id": user_id, "error": "User not found"}

            # Отправляем через соответствующий канал
            recipient_data = {
                "email": user.email,
                "phone": user.phone,
                "telegram_id": getattr(user, "telegram_id", None),
            }

            result = await self._send_via_channel(channel, message, recipient_data)

            return {
                "success": result.get("success", False),
                "user_id": user_id,
                "user_email": user.email,
                "channel": channel,
                "message": message[:100] + "..." if len(message) > 100 else message,
                "type": notification_type,
                "error": result.get("error"),
            }

        except Exception as e:
            logger.error(f"Failed to notify user {user_id}: {e}")
            return {
                "success": False,
                "user_id": user_id,
                "message": message[:100] + "..." if len(message) > 100 else message,
                "error": str(e),
            }

    async def notify_group(
        self, group_id: int, message: str, **kwargs
    ) -> Dict[str, Any]:
        """Система групповых уведомлений"""
        try:
            notification_type = kwargs.get("type", "info")
            channel = kwargs.get("channel", "email")

            # Получаем пользователей группы
            group_users = await self._get_group_users(group_id)

            if not group_users:
                return {
                    "success": False,
                    "group_id": group_id,
                    "error": "No users found in group",
                    "users_notified": 0,
                }

            # Отправляем уведомления всем пользователям группы
            notified_count = 0
            failed_count = 0
            results = []

            for user in group_users:
                try:
                    result = await self._notify_single_user(
                        user, message, notification_type, channel
                    )
                    results.append(result)

                    if result.get("success", False):
                        notified_count += 1
                    else:
                        failed_count += 1

                except Exception as e:
                    logger.error(f"Failed to notify user {user.get('id')}: {e}")
                    failed_count += 1
                    results.append(
                        {"user_id": user.get("id"), "success": False, "error": str(e)}
                    )

            logger.info(
                f"Group notification completed: {notified_count} notified, {failed_count} failed"
            )

            return {
                "success": notified_count > 0,
                "group_id": group_id,
                "message": message[:100] + "..." if len(message) > 100 else message,
                "channel": channel,
                "type": notification_type,
                "users_notified": notified_count,
                "users_failed": failed_count,
                "total_users": len(group_users),
                "results": results,
            }

        except Exception as e:
            logger.error(f"Failed to notify group {group_id}: {e}")
            return {
                "success": False,
                "group_id": group_id,
                "message": message[:100] + "..." if len(message) > 100 else message,
                "error": str(e),
            }

    async def create_communication_record(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание записи в таблице коммуникаций"""
        # Этот метод аналогичен create_communication_message
        return await self.create_communication_message(data)

    async def analyze_intent(self, text: str, **kwargs) -> Dict[str, Any]:
        """Анализ намерения с помощью AI"""
        try:
            context = kwargs.get("context", "")
            entity_type = kwargs.get("entity_type")
            entity_id = kwargs.get("entity_id")

            # Если указаны entity_type и entity_id, получаем контекст из сущности
            if entity_type and entity_id:
                from ...models.automation import EntityType as AutomationEntityType

                entity_type_enum = AutomationEntityType(entity_type)
                context = await self._get_entity_context(entity_type_enum, entity_id)

            # Интеграция с AI сервисом
            try:
                from ...services.ai.intent_service import AIIntentService

                ai_service = AIIntentService()

                intent = await ai_service.analyze_intent(text, {"context": context})

                return {
                    "success": True,
                    "intent": intent.value if hasattr(intent, "value") else str(intent),
                    "confidence": 0.85,  # Можно получить из AI сервиса
                    "text": text[:100] + "..." if len(text) > 100 else text,
                    "context_length": len(context),
                }

            except Exception as ai_error:
                logger.warning(f"AI intent analysis failed, using fallback: {ai_error}")
                # Fallback: простая логика определения намерения
                intent = "general"
                if "заказ" in text.lower() or "order" in text.lower():
                    intent = "order_request"
                elif "цена" in text.lower() or "price" in text.lower():
                    intent = "pricing_inquiry"
                elif "доставка" in text.lower() or "delivery" in text.lower():
                    intent = "delivery_question"

                return {
                    "success": True,
                    "intent": intent,
                    "confidence": 0.6,
                    "text": text[:100] + "..." if len(text) > 100 else text,
                    "fallback_used": True,
                    "ai_error": str(ai_error),
                }

        except Exception as e:
            logger.error(f"Failed to analyze intent: {e}")
            return {
                "success": False,
                "text": text[:100] + "..." if len(text) > 100 else text,
                "error": str(e),
            }

    async def generate_response(self, context: str, **kwargs) -> Dict[str, Any]:
        """Генерация ответа с помощью AI"""
        try:
            intent = kwargs.get("intent", "general")
            text = kwargs.get("text", "")
            entity_type = kwargs.get("entity_type")
            entity_id = kwargs.get("entity_id")

            # Если указаны entity_type и entity_id, получаем дополнительный контекст
            if entity_type and entity_id:
                from ...models.automation import EntityType as AutomationEntityType

                entity_type_enum = AutomationEntityType(entity_type)
                additional_context = await self._get_entity_context(
                    entity_type_enum, entity_id
                )
                context = f"{context} | {additional_context}"

            # Интеграция с AI сервисом
            try:
                from ...services.ai.intent_service import AIIntentService

                ai_service = AIIntentService()

                response = await ai_service.generate_response(
                    intent, text, {"context": context}
                )

                return {
                    "success": True,
                    "response": response,
                    "intent": intent,
                    "context_length": len(context),
                    "generated_by": "ai",
                }

            except Exception as ai_error:
                logger.warning(
                    f"AI response generation failed, using template: {ai_error}"
                )
                # Fallback: шаблонные ответы
                template_responses = {
                    "order_request": "Спасибо за ваш запрос! Мы можем изготовить эту продукцию. Для уточнения деталей и оформления заказа, пожалуйста, позвоните нам по телефону +7 (495) 123-45-67 или напишите на email info@company.com",
                    "pricing_inquiry": "Стоимость изготовления зависит от тиража, сложности дизайна и материалов. Минимальный тираж - 50 штук. Цена от 150 руб/шт. Для точного расчета пришлите макет и требования.",
                    "delivery_question": "Мы осуществляем доставку по всей России через транспортные компании. Стоимость доставки рассчитывается индивидуально в зависимости от региона и веса груза. Срок доставки 3-7 дней.",
                    "general": "Спасибо за ваше обращение! Мы свяжемся с вами в ближайшее время для уточнения деталей.",
                }

                response = template_responses.get(intent, template_responses["general"])

                return {
                    "success": True,
                    "response": response,
                    "intent": intent,
                    "context_length": len(context),
                    "generated_by": "template_fallback",
                    "ai_error": str(ai_error),
                }

        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return {
                "success": False,
                "context": context[:100] + "..." if len(context) > 100 else context,
                "error": str(e),
                "fallback_response": "Извините, произошла ошибка. Мы свяжемся с вами в ближайшее время.",
            }

    async def send_via_channel(
        self, channel: str, response: str, recipient_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Отправка через соответствующий канал"""
        return await self._send_via_channel(channel, response, recipient_data)

    async def render_email_template(
        self, template_name: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Рендеринг шаблона email"""
        try:
            template = await self._render_email_template(template_name, context)

            return {
                "success": True,
                "template_name": template_name,
                "subject": template.get("subject"),
                "body": template.get("body"),
                "html_body": template.get("html_body"),
                "context_keys": list(context.keys()),
            }

        except Exception as e:
            logger.error(f"Failed to render email template {template_name}: {e}")
            return {
                "success": False,
                "template_name": template_name,
                "error": str(e),
                "context_keys": list(context.keys()) if context else [],
            }

    async def get_entity_text(self, entity_type: str, entity_id: int) -> Dict[str, Any]:
        """Получение текста из сущности"""
        try:
            from ...models.automation import EntityType as AutomationEntityType

            entity_type_enum = AutomationEntityType(entity_type)

            text = await self._get_entity_text(entity_type_enum, entity_id)

            return {
                "success": True,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "text": text,
                "text_length": len(text),
            }

        except Exception as e:
            logger.error(
                f"Failed to get entity text for {entity_type} {entity_id}: {e}"
            )
            return {
                "success": False,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "error": str(e),
            }

    async def get_entity_context(
        self, entity_type: str, entity_id: int
    ) -> Dict[str, Any]:
        """Получение контекста из сущности"""
        try:
            from ...models.automation import EntityType as AutomationEntityType

            entity_type_enum = AutomationEntityType(entity_type)

            context = await self._get_entity_context(entity_type_enum, entity_id)

            return {
                "success": True,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "context": context,
                "context_length": len(context),
            }

        except Exception as e:
            logger.error(
                f"Failed to get entity context for {entity_type} {entity_id}: {e}"
            )
            return {
                "success": False,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "error": str(e),
            }

    async def _notify_single_user(
        self, user: Dict[str, Any], message: str, notification_type: str, channel: str
    ) -> Dict[str, Any]:
        """
        Отправка уведомления одному пользователю

        Args:
            user: Данные пользователя
            message: Текст сообщения
            notification_type: Тип уведомления
            channel: Канал отправки

        Returns:
            Dict с результатом отправки
        """
        try:
            user_id = user.get("id")
            user_email = user.get("email")
            user_phone = user.get("phone")
            user_telegram_id = user.get("telegram_id")

            if channel == "email":
                if not user_email:
                    return {
                        "user_id": user_id,
                        "success": False,
                        "error": "No email address",
                        "channel": "email",
                    }

                # Отправляем email
                from ...services.email_service import EmailMessage, email_service

                subject = f"Уведомление: {notification_type}"
                email_message = EmailMessage(
                    to=user_email, subject=subject, body=message
                )

                success = await email_service.send_email(email_message)

                return {
                    "user_id": user_id,
                    "success": success,
                    "channel": "email",
                    "recipient": user_email,
                }

            elif channel == "sms":
                if not user_phone:
                    return {
                        "user_id": user_id,
                        "success": False,
                        "error": "No phone number",
                        "channel": "sms",
                    }

                # Отправляем SMS
                result = await sms_service.send_sms(user_phone, message)

                return {
                    "user_id": user_id,
                    "success": result.get("success", False),
                    "channel": "sms",
                    "recipient": user_phone,
                    "message_id": result.get("message_id"),
                    "provider": result.get("provider"),
                    "cost": result.get("cost"),
                    "error": result.get("error"),
                }

            elif channel == "telegram":
                if not user_telegram_id:
                    return {
                        "user_id": user_id,
                        "success": False,
                        "error": "No Telegram ID",
                        "channel": "telegram",
                    }

                # Отправляем в Telegram
                from ...services.telegram_bot_service import telegram_bot_service

                result = await telegram_bot_service.send_message(
                    chat_id=str(user_telegram_id), text=message
                )

                return {
                    "user_id": user_id,
                    "success": result.get("success", False),
                    "channel": "telegram",
                    "recipient": user_telegram_id,
                    "message_id": result.get("message_id"),
                    "error": result.get("error"),
                }

            else:
                return {
                    "user_id": user_id,
                    "success": False,
                    "error": f"Unsupported channel: {channel}",
                    "channel": channel,
                }

        except Exception as e:
            logger.error(f"Failed to notify user {user.get('id')}: {e}")
            return {"user_id": user.get("id"), "success": False, "error": str(e)}
