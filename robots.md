# models/automation.py
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Boolean, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class EntityType(enum.Enum):
    LEAD = "lead"
    DEAL = "deal"
    ORDER = "order"
    TASK = "task"
    SIGNATURE = "signature"
    SMART_PROCESS = "smart_process"

class TriggerEvent(enum.Enum):
    # CRM события
    EMAIL_OPENED = "email_opened"
    LINK_CLICKED = "link_clicked"
    PAYMENT_RECEIVED = "payment_received"
    STATUS_CHANGED = "status_changed"
    STAGE_CHANGED = "stage_changed"
    CALL_RECEIVED = "call_received"
    MESSAGE_RECEIVED = "message_received"
    DOCUMENT_VIEWED = "document_viewed"
    
    # Задачи
    DEADLINE_APPROACHING = "deadline_approaching"
    TASK_STATUS_CHANGED = "task_status_changed"
    
    # Подпись
    DOCUMENT_SIGNED = "document_signed"
    SIGNATURE_COMPLETED = "signature_completed"
    
    # Общие
    FIELD_CHANGED = "field_changed"
    NEW_COMMENT = "new_comment"

class RobotAction(enum.Enum):
    # Коммуникации
    SEND_EMAIL = "send_email"
    SEND_SMS = "send_sms"
    SEND_TELEGRAM = "send_telegram"
    
    # CRM действия
    CREATE_TASK = "create_task"
    CREATE_DEAL = "create_deal"
    CREATE_INVOICE = "create_invoice"
    UPDATE_FIELD = "update_field"
    
    # Уведомления
    NOTIFY_USER = "notify_user"
    NOTIFY_GROUP = "notify_group"
    
    # Производство
    CREATE_PRODUCTION_STEP = "create_production_step"
    UPDATE_ORDER_STATUS = "update_order_status"
    
    # Документы
    CREATE_DOCUMENT = "create_document"
    SEND_FOR_SIGNATURE = "send_for_signature"

class Trigger(Base):
    __tablename__ = "triggers"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Контекст триггера (в каком модуле работает)
    entity_type = Column(Enum(EntityType), nullable=False)
    process_id = Column(Integer, ForeignKey("processes.id"), nullable=True)
    
    # Событие, на которое реагирует триггер
    event_type = Column(Enum(TriggerEvent), nullable=False)
    
    # Условия срабатывания
    conditions = Column(JSON)  # {field: value, operator: "equals", ...}
    
    # Целевая стадия (куда переместить элемент)
    target_stage_id = Column(Integer, ForeignKey("stages.id"))
    target_stage = relationship("Stage", foreign_keys=[target_stage_id])
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Robot(Base):
    __tablename__ = "robots"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Контекст робота (в каком модуле работает)
    entity_type = Column(Enum(EntityType), nullable=False)
    
    # Стадия, на которой срабатывает робот
    stage_id = Column(Integer, ForeignKey("stages.id"), nullable=False)
    stage = relationship("Stage", foreign_keys=[stage_id])
    
    # Последовательные действия
    actions = relationship("RobotActionConfig", back_populates="robot", order_by="RobotActionConfig.execution_order")
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class RobotActionConfig(Base):
    __tablename__ = "robot_actions_config"
    
    id = Column(Integer, primary_key=True)
    robot_id = Column(Integer, ForeignKey("robots.id"))
    robot = relationship("Robot", back_populates="actions")
    
    action_type = Column(Enum(RobotAction), nullable=False)
    execution_order = Column(Integer, nullable=False)
    
    # Конфигурация действия
    config = Column(JSON)  # {template: "welcome_email", delay: 3600, ...}
    
    # Условия выполнения
    conditions = Column(JSON)
    delay_seconds = Column(Integer, default=0)

class Stage(Base):
    __tablename__ = "stages"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    entity_type = Column(Enum(EntityType), nullable=False)
    process_id = Column(Integer, ForeignKey("processes.id"))
    
    # Роботы, привязанные к этой стадии
    robots = relationship("Robot", backref="stage_robots")
    
    order_index = Column(Integer, default=0)
    color = Column(String(7))  # HEX цвет для визуализации

class Process(Base):
    __tablename__ = "processes"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    entity_type = Column(Enum(EntityType), nullable=False)
    description = Column(Text)
    
    # Стадии процесса
    stages = relationship("Stage", backref="process")
    
    is_active = Column(Boolean, default=True)
⚡ Улучшенный Сервис Триггеров
python
# services/trigger_service.py
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from models.automation import Trigger, TriggerEvent, EntityType, Stage
from models.order import Order
from models.customer import Customer
from models.task import Task
from models.communication import Communication
import logging
import asyncio

logger = logging.getLogger(__name__)

class AdvancedTriggerService:
    """
    Улучшенный сервис триггеров в стиле Bitrix24
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.entity_services = {
            EntityType.LEAD: LeadService(db),
            EntityType.DEAL: DealService(db),
            EntityType.ORDER: OrderService(db),
            EntityType.TASK: TaskService(db),
            EntityType.SIGNATURE: SignatureService(db),
            EntityType.SMART_PROCESS: SmartProcessService(db)
        }
    
    async def handle_trigger_event(
        self,
        entity_type: EntityType,
        event_type: TriggerEvent,
        entity_id: int,
        event_data: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Обработка события триггера - перемещение на целевую стадию
        """
        event_data = event_data or {}
        results = []
        
        # Находим активные триггеры для этого типа события и сущности
        triggers = self.db.query(Trigger).filter(
            Trigger.entity_type == entity_type,
            Trigger.event_type == event_type,
            Trigger.is_active == True
        ).all()
        
        for trigger in triggers:
            try:
                # Проверяем условия
                if await self._check_trigger_conditions(trigger, entity_id, event_data):
                    # Перемещаем сущность на целевую стадию
                    move_result = await self._move_to_target_stage(
                        entity_type, entity_id, trigger.target_stage_id
                    )
                    
                    results.append({
                        "trigger_id": trigger.id,
                        "trigger_name": trigger.name,
                        "entity_type": entity_type.value,
                        "entity_id": entity_id,
                        "target_stage_id": trigger.target_stage_id,
                        "success": True,
                        "move_result": move_result
                    })
                    
                    logger.info(f"Trigger {trigger.name} executed successfully")
                    
            except Exception as e:
                logger.error(f"Error executing trigger {trigger.id}: {e}")
                results.append({
                    "trigger_id": trigger.id,
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    async def _check_trigger_conditions(
        self, 
        trigger: Trigger, 
        entity_id: int,
        event_data: Dict[str, Any]
    ) -> bool:
        """Проверка условий срабатывания триггера"""
        if not trigger.conditions:
            return True
        
        # Получаем сервис для типа сущности
        entity_service = self.entity_services.get(trigger.entity_type)
        if not entity_service:
            return False
        
        # Получаем данные сущности
        entity_data = await entity_service.get_entity_data(entity_id)
        if not entity_data:
            return False
        
        # Проверяем условия
        return await self._evaluate_conditions(trigger.conditions, entity_data, event_data)
    
    async def _move_to_target_stage(
        self,
        entity_type: EntityType,
        entity_id: int,
        target_stage_id: int
    ) -> Dict[str, Any]:
        """Перемещение сущности на целевую стадию"""
        entity_service = self.entity_services.get(entity_type)
        if not entity_service:
            raise ValueError(f"No service for entity type: {entity_type}")
        
        # Получаем целевую стадию
        target_stage = self.db.query(Stage).filter(Stage.id == target_stage_id).first()
        if not target_stage:
            raise ValueError(f"Target stage {target_stage_id} not found")
        
        # Перемещаем сущность
        result = await entity_service.move_to_stage(entity_id, target_stage_id)
        
        # Запускаем роботов новой стадии
        if result.get("success"):
            robot_service = RobotService(self.db)
            await robot_service.execute_stage_robots(entity_type, entity_id, target_stage_id)
        
        return result

# Специализированные обработчики событий
class CRMTriggerService(AdvancedTriggerService):
    """Триггеры для CRM модуля"""
    
    async def on_email_opened(self, communication_id: int, customer_id: int):
        """Клиент открыл email"""
        return await self.handle_trigger_event(
            entity_type=EntityType.DEAL,
            event_type=TriggerEvent.EMAIL_OPENED,
            entity_id=customer_id,  # или deal_id, в зависимости от контекста
            event_data={
                "communication_id": communication_id,
                "customer_id": customer_id,
                "action": "email_opened"
            }
        )
    
    async def on_payment_received(self, invoice_id: int, deal_id: int):
        """Получена оплата по счету"""
        return await self.handle_trigger_event(
            entity_type=EntityType.DEAL,
            event_type=TriggerEvent.PAYMENT_RECEIVED,
            entity_id=deal_id,
            event_data={
                "invoice_id": invoice_id,
                "amount": None,  # можно добавить данные об оплате
                "action": "payment_received"
            }
        )
    
    async def on_document_signed(self, document_id: int, deal_id: int):
        """Клиент подписал документ"""
        return await self.handle_trigger_event(
            entity_type=EntityType.DEAL,
            event_type=TriggerEvent.DOCUMENT_SIGNED,
            entity_id=deal_id,
            event_data={
                "document_id": document_id,
                "action": "document_signed"
            }
        )

class TaskTriggerService(AdvancedTriggerService):
    """Триггеры для задач"""
    
    async def on_deadline_approaching(self, task_id: int, hours_left: int):
        """Приближается дедлайн задачи"""
        return await self.handle_trigger_event(
            entity_type=EntityType.TASK,
            event_type=TriggerEvent.DEADLINE_APPROACHING,
            entity_id=task_id,
            event_data={
                "hours_left": hours_left,
                "action": "deadline_approaching"
            }
        )
    
    async def on_task_status_changed(self, task_id: int, old_status: str, new_status: str):
        """Изменен статус задачи"""
        return await self.handle_trigger_event(
            entity_type=EntityType.TASK,
            event_type=TriggerEvent.TASK_STATUS_CHANGED,
            entity_id=task_id,
            event_data={
                "old_status": old_status,
                "new_status": new_status,
                "action": "status_changed"
            }
        )
🤖 Улучшенный Сервис Роботов
python
# services/robot_service.py
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from models.automation import Robot, RobotAction, RobotActionConfig, EntityType, Stage
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AdvancedRobotService:
    """
    Улучшенный сервис роботов в стиле Bitrix24
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.action_executors = {
            RobotAction.SEND_EMAIL: self._execute_send_email,
            RobotAction.SEND_SMS: self._execute_send_sms,
            RobotAction.CREATE_TASK: self._execute_create_task,
            RobotAction.NOTIFY_USER: self._execute_notify_user,
            RobotAction.UPDATE_FIELD: self._execute_update_field,
            RobotAction.CREATE_DOCUMENT: self._execute_create_document,
            RobotAction.SEND_FOR_SIGNATURE: self._execute_send_for_signature,
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
                logger.error(f"Error executing robot action {action_config.id}: {e}")
                executed_actions.append({
                    "action_id": action_config.id,
                    "action_type": action_config.action_type.value,
                    "success": False,
                    "error": str(e)
                })
                # В линейной логике можно прервать выполнение
                break
        
        return executed_actions
    
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
        
        # Отправка email
        # ... логика отправки ...
        
        return {
            "status": "email_sent",
            "template": template_name,
            "recipient": config.get("to"),
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
        
        # Логика отправки SMS
        # ...
        
        return {"status": "sms_sent", "phone": config.get("phone")}
    
    async def _execute_create_task(
        self,
        action_config: RobotActionConfig,
        entity_type: EntityType,
        entity_id: int
    ) -> Dict[str, Any]:
        """Создание задачи через робота"""
        config = action_config.config or {}
        
        # Логика создания задачи
        task_data = {
            "title": config.get("title", "Новая задача"),
            "description": config.get("description", ""),
            "assigned_to": config.get("assigned_to"),
            "deadline": config.get("deadline"),
            "priority": config.get("priority", "medium")
        }
        
        # Создаем задачу в базе
        # ...
        
        return {"status": "task_created", "task_id": None}  # вернуть ID созданной задачи
    
    async def _execute_notify_user(
        self,
        action_config: RobotActionConfig,
        entity_type: EntityType,
        entity_id: int
    ) -> Dict[str, Any]:
        """Уведомление пользователя через робота"""
        config = action_config.config or {}
        
        # Логика уведомления (Telegram, внутренние уведомления и т.д.)
        # ...
        
        return {"status": "user_notified", "user_id": config.get("user_id")}
    
    async def _execute_update_field(
        self,
        action_config: RobotActionConfig,
        entity_type: EntityType,
        entity_id: int
    ) -> Dict[str, Any]:
        """Обновление поля сущности через робота"""
        config = action_config.config or {}
        
        field_name = config.get("field")
        field_value = config.get("value")
        
        if not field_name:
            raise ValueError("No field specified for update")
        
        # Обновляем поле сущности
        update_result = await self._update_entity_field(
            entity_type, entity_id, field_name, field_value
        )
        
        return {
            "status": "field_updated",
            "field": field_name,
            "value": field_value,
            "entity_type": entity_type.value,
            "entity_id": entity_id
        }
    
    async def _execute_create_document(
        self,
        action_config: RobotActionConfig,
        entity_type: EntityType,
        entity_id: int
    ) -> Dict[str, Any]:
        """Создание документа через робота"""
        config = action_config.config or {}
        
        # Логика создания документа (договор, коммерческое предложение и т.д.)
        # ...
        
        return {"status": "document_created", "type": config.get("document_type")}
    
    async def _execute_send_for_signature(
        self,
        action_config: RobotActionConfig,
        entity_type: EntityType,
        entity_id: int
    ) -> Dict[str, Any]:
        """Отправка документа на подпись через робота"""
        config = action_config.config or {}
        
        # Логика интеграции с системой электронной подписи
        # ...
        
        return {"status": "sent_for_signature", "document_id": config.get("document_id")}
    
    # Вспомогательные методы
    async def _get_entity_data(self, entity_type: EntityType, entity_id: int) -> Dict[str, Any]:
        """Получение данных сущности для шаблонов"""
        # Реализация получения данных сущности
        return {}
    
    async def _render_email_template(self, template_name: str, data: Dict[str, Any]) -> Dict[str, str]:
        """Рендеринг шаблона email"""
        # Реализация рендеринга шаблона
        return {"subject": "Тема письма", "body": "Содержимое письма"}
    
    async def _update_entity_field(
        self, 
        entity_type: EntityType, 
        entity_id: int, 
        field_name: str, 
        field_value: Any
    ) -> bool:
        """Обновление поля сущности"""
        # Реализация обновления поля
        return True
🔄 Интеграция с Бизнес-Процессами
python
# services/automation_integration.py
from sqlalchemy.orm import Session
from typing import Dict, Any
from models.automation import EntityType, TriggerEvent
from .trigger_service import CRMTriggerService, TaskTriggerService
from .robot_service import AdvancedRobotService
import logging

logger = logging.getLogger(__name__)

class BitrixStyleAutomation:
    """
    Главный сервис автоматизации в стиле Bitrix24
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.crm_triggers = CRMTriggerService(db)
        self.task_triggers = TaskTriggerService(db)
        self.robot_service = AdvancedRobotService(db)
    
    # CRM автоматизация
    async def on_crm_event(self, event_type: TriggerEvent, entity_id: int, event_data: Dict[str, Any] = None):
        """Обработка событий в CRM"""
        logger.info(f"CRM event: {event_type.value} for entity {entity_id}")
        
        if event_type in [TriggerEvent.EMAIL_OPENED, TriggerEvent.LINK_CLICKED, 
                         TriggerEvent.PAYMENT_RECEIVED, TriggerEvent.DOCUMENT_SIGNED]:
            return await self.crm_triggers.handle_trigger_event(
                EntityType.DEAL, event_type, entity_id, event_data
            )
        
        return []
    
    # Автоматизация задач
    async def on_task_event(self, event_type: TriggerEvent, task_id: int, event_data: Dict[str, Any] = None):
        """Обработка событий задач"""
        logger.info(f"Task event: {event_type.value} for task {task_id}")
        
        if event_type in [TriggerEvent.DEADLINE_APPROACHING, TriggerEvent.TASK_STATUS_CHANGED]:
            return await self.task_triggers.handle_trigger_event(
                EntityType.TASK, event_type, task_id, event_data
            )
        
        return []
    
    # Универсальный метод для перемещения на стадию
    async def move_to_stage(
        self, 
        entity_type: EntityType, 
        entity_id: int, 
        stage_id: int
    ) -> Dict[str, Any]:
        """
        Перемещение сущности на стадию с запуском роботов
        (может вызываться как триггерами, так и вручную)
        """
        try:
            # 1. Перемещаем сущность на стадию
            move_result = await self._move_entity_to_stage(entity_type, entity_id, stage_id)
            
            # 2. Запускаем роботов новой стадии
            if move_result.get("success"):
                robot_results = await self.robot_service.execute_stage_robots(
                    entity_type, entity_id, stage_id
                )
                move_result["robots_executed"] = robot_results
            
            return move_result
            
        except Exception as e:
            logger.error(f"Error moving to stage: {e}")
            return {"success": False, "error": str(e)}
    
    async def _move_entity_to_stage(self, entity_type: EntityType, entity_id: int, stage_id: int):
        """Перемещение сущности на указанную стадию"""
        # Реализация перемещения в зависимости от типа сущности
        if entity_type == EntityType.DEAL:
            return await self._move_deal_to_stage(entity_id, stage_id)
        elif entity_type == EntityType.TASK:
            return await self._move_task_to_stage(entity_id, stage_id)
        elif entity_type == EntityType.ORDER:
            return await self._move_order_to_stage(entity_id, stage_id)
        else:
            raise ValueError(f"Unsupported entity type: {entity_type}")

# Конкретные примеры использования
class Examples:
    """Примеры автоматизации в стиле Bitrix24"""
    
    @staticmethod
    async def deal_automation_example(db: Session):
        """Пример: автоматизация сделки при подписании документа"""
        automation = BitrixStyleAutomation(db)
        
        # Клиент подписал документ - срабатывает триггер
        trigger_results = await automation.on_crm_event(
            event_type=TriggerEvent.DOCUMENT_SIGNED,
            entity_id=123,  # ID сделки
            event_data={"document_id": 456}
        )
        
        # Триггер перемещает сделку на стадию "Ожидание оплаты"
        # На стадии "Ожидание оплаты" срабатывает робот, который:
        # 1. Создает счет на оплату
        # 2. Отправляет счет клиенту по email
        # 3. Создает задачу менеджеру на контроль оплаты
        
        return trigger_results
    
    @staticmethod
    async def task_automation_example(db: Session):
        """Пример: автоматизация задач при приближении дедлайна"""
        automation = BitrixStyleAutomation(db)
        
        # За дедлайн задачи остался 1 день - срабатывает триггер
        trigger_results = await automation.on_task_event(
            event_type=TriggerEvent.DEADLINE_APPROACHING,
            entity_id=789,  # ID задачи
            event_data={"hours_left": 24}
        )
        
        # Триггер перемещает задачу на стадию "Срочно"
        # На стадии "Срочно" срабатывает робот, который:
        # 1. Отправляет уведомление исполнителю
        # 2. Отправляет уведомление руководителю
        # 3. Повышает приоритет задачи
        
        return trigger_results
🎯 API для Управления Автоматизацией
python
# api/v1/endpoints/automation.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from services.automation_integration import BitrixStyleAutomation
from models.automation import EntityType, TriggerEvent
from schemas.automation import *

router = APIRouter()

@router.post("/triggers/{entity_type}/event/{event_type}")
async def fire_trigger_event(
    entity_type: EntityType,
    event_type: TriggerEvent,
    entity_id: int,
    event_data: dict = None,
    db: Session = Depends(get_db)
):
    """Инициация события триггера"""
    automation = BitrixStyleAutomation(db)
    
    if entity_type in [EntityType.LEAD, EntityType.DEAL, EntityType.ORDER]:
        results = await automation.on_crm_event(event_type, entity_id, event_data)
    elif entity_type == EntityType.TASK:
        results = await automation.on_task_event(event_type, entity_id, event_data)
    else:
        raise HTTPException(400, "Unsupported entity type")
    
    return {"results": results}

@router.post("/entities/{entity_type}/{entity_id}/move-to-stage/{stage_id}")
async def move_entity_to_stage(
    entity_type: EntityType,
    entity_id: int,
    stage_id: int,
    db: Session = Depends(get_db)
):
    """Перемещение сущности на стадию (ручное или автоматическое)"""
    automation = BitrixStyleAutomation(db)
    result = await automation.move_to_stage(entity_type, entity_id, stage_id)
    return result

@router.get("/processes/{entity_type}")
async def get_processes(
    entity_type: EntityType,
    db: Session = Depends(get_db)
):
    """Получение процессов и стадий для типа сущности"""
    # Реализация получения процессов
    pass

@router.get("/stages/{stage_id}/robots")
async def get_stage_robots(
    stage_id: int,
    db: Session = Depends(get_db)
):
    """Получение роботов стадии"""
    # Реализация получения роботов
    pass
📊 Примеры Конфигурации
python
# config/automation_examples.py
"""
Примеры конфигурации роботов и триггеров в стиле Bitrix24
"""

DEAL_PROCESS_EXAMPLE = {
    "process_name": "Продажа полиграфии",
    "entity_type": "deal",
    "stages": [
        {"name": "Новая заявка", "color": "#FFEB3B"},
        {"name": "Переговоры", "color": "#2196F3"},
        {"name": "Подписание договора", "color": "#4CAF50"},
        {"name": "Ожидание оплаты", "color": "#FF9800"},
        {"name": "В производстве", "color": "#9C27B0"},
        {"name": "Завершено", "color": "#607D8B"}
    ],
    "triggers": [
        {
            "name": "Клиент открыл КП",
            "event_type": "email_opened",
            "conditions": {"document_type": "commercial_offer"},
            "target_stage": "Переговоры"
        },
        {
            "name": "Клиент подписал договор", 
            "event_type": "document_signed",
            "target_stage": "Ожидание оплаты"
        },
        {
            "name": "Оплата получена",
            "event_type": "payment_received", 
            "target_stage": "В производстве"
        }
    ],
    "robots": [
        {
            "stage": "Новая заявка",
            "name": "Первичный контакт",
            "actions": [
                {
                    "action_type": "send_email",
                    "execution_order": 1,
                    "config": {
                        "template": "welcome_email",
                        "to": "customer_email"
                    }
                },
                {
                    "action_type": "create_task", 
                    "execution_order": 2,
                    "delay_seconds": 3600,  # 1 час
                    "config": {
                        "title": "Позвонить клиенту",
                        "assigned_to": "manager_id",
                        "deadline": "24h"
                    }
                }
            ]
        },
        {
            "stage": "Ожидание оплаты",
            "name": "Отправка счета",
            "actions": [
                {
                    "action_type": "create_document",
                    "execution_order": 1,
                    "config": {"type": "invoice"}
                },
                {
                    "action_type": "send_email",
                    "execution_order": 2, 
                    "config": {
                        "template": "invoice_email",
                        "to": "customer_email"
                    }
                }
            ]
        }
    ]
}

TASK_PROCESS_EXAMPLE = {
    "process_name": "Управление задачами",
    "entity_type": "task", 
    "stages": [
        {"name": "Новая", "color": "#E0E0E0"},
        {"name": "В работе", "color": "#2196F3"},
        {"name": "На проверке", "color": "#FF9800"},
        {"name": "Срочно", "color": "#F44336"},
        {"name": "Завершено", "color": "#4CAF50"}
    ],
    "triggers": [
        {
            "name": "Приближается дедлайн",
            "event_type": "deadline_approaching", 
            "conditions": {"hours_left": 24},
            "target_stage": "Срочно"
        }
    ],
    "robots": [
        {
            "stage": "Срочно",
            "name": "Эскалация срочной задачи",
            "actions": [
                {
                    "action_type": "notify_user",
                    "execution_order": 1,
                    "config": {
                        "user_id": "assignee_id",
                        "message": "Задача требует срочного выполнения!"
                    }
                },
                {
                    "action_type": "notify_user",
                    "execution_order": 2,
                    "config": {
                        "user_id": "manager_id", 
                        "message": "Задача сотрудника требует контроля!"
                    }
                }
            ]
        }
    ]
}