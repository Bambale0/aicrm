"""
Workflow Engine для автоматических бизнес-процессов
"""
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from sqlalchemy.orm import Session
from enum import Enum
import asyncio

from ..models.automation import EntityType
from ..models.order import Order, OrderStatus
from ..models.task import Task
from ..models.customer import Customer
from ..models.production_step import ProductionStep, StepStatus
from ..services.automation.robot_service import RobotService
from ..utils.logging import get_logger

logger = get_logger(__name__)


class WorkflowStatus(Enum):
    """Статусы workflow"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStep:
    """Шаг workflow"""

    def __init__(self, step_id: str, name: str, action: Callable, conditions: Optional[Dict] = None):
        self.step_id = step_id
        self.name = name
        self.action = action
        self.conditions = conditions or {}
        self.status = WorkflowStatus.PENDING
        self.result = None
        self.error = None
        self.executed_at = None

    async def execute(self, context: Dict[str, Any]) -> bool:
        """Выполнить шаг"""
        try:
            # Проверяем условия выполнения
            if not await self._check_conditions(context):
                logger.info(f"Step {self.step_id} conditions not met, skipping")
                self.status = WorkflowStatus.CANCELLED
                return True

            self.status = WorkflowStatus.RUNNING
            logger.info(f"Executing workflow step: {self.step_id} - {self.name}")

            # Выполняем действие
            self.result = await self.action(context)
            self.executed_at = datetime.utcnow()
            self.status = WorkflowStatus.COMPLETED

            logger.info(f"Workflow step completed: {self.step_id}")
            return True

        except Exception as e:
            logger.error(f"Workflow step failed: {self.step_id}", error=str(e))
            self.status = WorkflowStatus.FAILED
            self.error = str(e)
            self.executed_at = datetime.utcnow()
            return False

    async def _check_conditions(self, context: Dict[str, Any]) -> bool:
        """Проверить условия выполнения шага"""
        for condition_key, condition_value in self.conditions.items():
            if condition_key not in context:
                return False

            context_value = context[condition_key]

            # Поддержка простых операторов
            if isinstance(condition_value, dict):
                operator = condition_value.get("operator", "eq")
                expected_value = condition_value.get("value")

                if operator == "eq" and context_value != expected_value:
                    return False
                elif operator == "neq" and context_value == expected_value:
                    return False
                elif operator == "gt" and not (context_value > expected_value):
                    return False
                elif operator == "lt" and not (context_value < expected_value):
                    return False
                elif operator == "in" and context_value not in expected_value:
                    return False
            else:
                # Простое равенство
                if context_value != condition_value:
                    return False

        return True


class Workflow:
    """Бизнес-процесс workflow"""

    def __init__(self, workflow_id: str, name: str, entity_type: EntityType):
        self.workflow_id = workflow_id
        self.name = name
        self.entity_type = entity_type
        self.steps: List[WorkflowStep] = []
        self.status = WorkflowStatus.PENDING
        self.context: Dict[str, Any] = {}
        self.created_at = datetime.utcnow()
        self.completed_at = None

    def add_step(self, step: WorkflowStep):
        """Добавить шаг в workflow"""
        self.steps.append(step)

    async def execute(self, initial_context: Dict[str, Any]) -> bool:
        """Выполнить workflow"""
        self.status = WorkflowStatus.RUNNING
        self.context.update(initial_context)

        logger.info(f"Starting workflow: {self.workflow_id} - {self.name}")

        success = True

        for step in self.steps:
            step_success = await step.execute(self.context)
            if not step_success:
                success = False
                # Определяем, продолжать ли выполнение при ошибке
                if not self._should_continue_on_failure(step):
                    break

        self.status = WorkflowStatus.COMPLETED if success else WorkflowStatus.FAILED
        self.completed_at = datetime.utcnow()

        logger.info(f"Workflow completed: {self.workflow_id}, success: {success}")

        # Записываем метрику
        from ..services.metrics_service import metrics_service
        metrics_service.record_ai_request("workflow_execution", "local", "success" if success else "error")

        return success

    def _should_continue_on_failure(self, step: WorkflowStep) -> bool:
        """Определить, продолжать ли выполнение при ошибке шага"""
        # Для критических шагов останавливаемся
        critical_steps = ["create_order", "validate_payment", "assign_production"]
        return step.step_id not in critical_steps


class WorkflowEngine:
    """Движок workflow для автоматических бизнес-процессов"""

    def __init__(self, db: Session):
        self.db = db
        self.workflows: Dict[str, Workflow] = {}
        self.active_workflows: Dict[str, Workflow] = {}
        self.robot_service = RobotService(db)

        # Регистрируем стандартные workflow
        self._register_standard_workflows()

    def _register_standard_workflows(self):
        """Регистрация стандартных workflow"""

        # 1. Workflow создания заказа
        order_workflow = Workflow("order_creation", "Создание заказа", EntityType.ORDER)
        order_workflow.add_step(WorkflowStep(
            "validate_order",
            "Валидация заказа",
            self._validate_order_data,
            {"order_status": "pending"}
        ))
        order_workflow.add_step(WorkflowStep(
            "create_production_steps",
            "Создание этапов производства",
            self._create_production_steps,
            {"validation_passed": True}
        ))
        order_workflow.add_step(WorkflowStep(
            "assign_tasks",
            "Назначение задач сотрудникам",
            self._assign_production_tasks,
            {"production_steps_created": True}
        ))
        order_workflow.add_step(WorkflowStep(
            "notify_customer",
            "Уведомление клиента",
            self._notify_customer_order_created,
            {"tasks_assigned": True}
        ))
        self.workflows["order_creation"] = order_workflow

        # 2. Workflow обработки платежа
        payment_workflow = Workflow("payment_processing", "Обработка платежа", EntityType.ORDER)
        payment_workflow.add_step(WorkflowStep(
            "validate_payment",
            "Валидация платежа",
            self._validate_payment,
            {"payment_amount": {"operator": "gt", "value": 0}}
        ))
        payment_workflow.add_step(WorkflowStep(
            "update_order_status",
            "Обновление статуса заказа",
            self._update_order_to_paid,
            {"payment_valid": True}
        ))
        payment_workflow.add_step(WorkflowStep(
            "start_production",
            "Запуск производства",
            self._start_production_workflow,
            {"order_status": "paid"}
        ))
        self.workflows["payment_processing"] = payment_workflow

        # 3. Workflow завершения производства
        completion_workflow = Workflow("production_completion", "Завершение производства", EntityType.ORDER)
        completion_workflow.add_step(WorkflowStep(
            "check_all_steps_completed",
            "Проверка завершения всех этапов",
            self._check_production_completion,
            {"order_status": "in_production"}
        ))
        completion_workflow.add_step(WorkflowStep(
            "update_order_completed",
            "Обновление заказа на завершенный",
            self._mark_order_completed,
            {"all_steps_completed": True}
        ))
        completion_workflow.add_step(WorkflowStep(
            "notify_customer_delivery",
            "Уведомление о готовности к доставке",
            self._notify_customer_delivery_ready,
            {"order_completed": True}
        ))
        self.workflows["production_completion"] = completion_workflow

        # 4. Workflow обработки жалоб
        complaint_workflow = Workflow("complaint_handling", "Обработка жалоб", EntityType.CUSTOMER)
        complaint_workflow.add_step(WorkflowStep(
            "analyze_complaint",
            "Анализ жалобы",
            self._analyze_complaint,
            {"complaint_text": {"operator": "neq", "value": ""}}
        ))
        complaint_workflow.add_step(WorkflowStep(
            "escalate_if_needed",
            "Эскалация при необходимости",
            self._escalate_complaint,
            {"complaint_severity": {"operator": "in", "value": ["high", "critical"]}}
        ))
        complaint_workflow.add_step(WorkflowStep(
            "create_resolution_task",
            "Создание задачи на разрешение",
            self._create_resolution_task,
            {"escalation_needed": False}
        ))
        self.workflows["complaint_handling"] = complaint_workflow

    async def trigger_workflow(self, workflow_id: str, entity_type: EntityType, entity_id: int, trigger_data: Optional[Dict] = None) -> str:
        """Запустить workflow"""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow = self.workflows[workflow_id]
        execution_id = f"{workflow_id}_{entity_id}_{datetime.utcnow().timestamp()}"

        # Создаем копию workflow для выполнения
        execution_workflow = Workflow(
            execution_id,
            f"{workflow.name} (Execution {execution_id})",
            entity_type
        )

        # Копируем шаги
        for step in workflow.steps:
            execution_workflow.add_step(WorkflowStep(
                step.step_id,
                step.name,
                step.action,
                step.conditions.copy()
            ))

        # Готовим контекст выполнения
        context = {
            "entity_type": entity_type.value,
            "entity_id": entity_id,
            "execution_id": execution_id,
            "trigger_data": trigger_data or {},
            "db": self.db
        }

        # Добавляем данные сущности в контекст
        await self._load_entity_data(context)

        # Запускаем выполнение
        self.active_workflows[execution_id] = execution_workflow

        # Запускаем в фоне
        asyncio.create_task(self._execute_workflow_async(execution_workflow, context))

        logger.info(f"Workflow triggered: {workflow_id}, execution_id: {execution_id}")
        return execution_id

    async def _execute_workflow_async(self, workflow: Workflow, context: Dict[str, Any]):
        """Асинхронное выполнение workflow"""
        try:
            await workflow.execute(context)
        except Exception as e:
            logger.error(f"Workflow execution failed: {workflow.workflow_id}", error=str(e))
        finally:
            # Удаляем из активных после выполнения
            if workflow.workflow_id in self.active_workflows:
                del self.active_workflows[workflow.workflow_id]

    async def get_workflow_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Получить статус выполнения workflow"""
        workflow = self.active_workflows.get(execution_id)
        if not workflow:
            return None

        return {
            "execution_id": execution_id,
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "status": workflow.status.value,
            "created_at": workflow.created_at.isoformat(),
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "steps": [
                {
                    "step_id": step.step_id,
                    "name": step.name,
                    "status": step.status.value,
                    "executed_at": step.executed_at.isoformat() if step.executed_at else None,
                    "error": step.error
                }
                for step in workflow.steps
            ]
        }

    async def cancel_workflow(self, execution_id: str) -> bool:
        """Отменить выполнение workflow"""
        workflow = self.active_workflows.get(execution_id)
        if not workflow:
            return False

        workflow.status = WorkflowStatus.CANCELLED
        logger.info(f"Workflow cancelled: {execution_id}")
        return True

    async def _load_entity_data(self, context: Dict[str, Any]):
        """Загрузить данные сущности в контекст"""
        entity_type = context["entity_type"]
        entity_id = context["entity_id"]

        if entity_type == EntityType.ORDER.value:
            order = self.db.query(Order).filter(Order.id == entity_id).first()
            if order:
                context.update({
                    "order": order.__dict__,
                    "order_status": order.status.value,
                    "customer_id": order.customer_id,
                    "order_total": order.total_amount
                })

        elif entity_type == EntityType.CUSTOMER.value:
            customer = self.db.query(Customer).filter(Customer.id == entity_id).first()
            if customer:
                context.update({
                    "customer": customer.__dict__,
                    "customer_email": customer.email,
                    "customer_phone": customer.phone,
                    "total_orders": customer.total_orders
                })

        elif entity_type == EntityType.TASK.value:
            task = self.db.query(Task).filter(Task.id == entity_id).first()
            if task:
                context.update({
                    "task": task.__dict__,
                    "task_status": task.status.value,
                    "assigned_to": task.assigned_to
                })

    # Методы действий workflow

    async def _validate_order_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Валидация данных заказа"""
        order_data = context.get("order", {})

        # Проверяем обязательные поля
        required_fields = ["customer_id", "total_amount"]
        for field in required_fields:
            if not order_data.get(field):
                raise ValueError(f"Missing required field: {field}")

        # Проверяем сумму
        if order_data.get("total_amount", 0) <= 0:
            raise ValueError("Order total must be positive")

        context["validation_passed"] = True
        return {"status": "validated"}

    async def _create_production_steps(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Создание этапов производства"""
        order_id = context["entity_id"]
        order_data = context.get("order", {})

        # Определяем этапы на основе типа печати
        print_type = order_data.get("print_type", "screen_print")
        steps_config = self._get_production_steps_for_print_type(print_type)

        created_steps = []
        for i, step_name in enumerate(steps_config, 1):
            step = ProductionStep(
                order_id=order_id,
                name=step_name,
                status=StepStatus.pending,
                sequence=i
            )
            self.db.add(step)
            created_steps.append(step)

        self.db.commit()

        context["production_steps_created"] = True
        context["production_steps_count"] = len(created_steps)

        return {"steps_created": len(created_steps)}

    async def _assign_production_tasks(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Назначение задач сотрудникам"""
        order_id = context["entity_id"]

        # Получаем этапы производства
        steps = self.db.query(ProductionStep).filter(
            ProductionStep.order_id == order_id
        ).all()

        assigned_tasks = []
        for step in steps:
            # Создаем задачу для этапа
            task = Task(
                user_id=1,  # Системный пользователь, будет переназначена
                title=f"Производство: {step.name}",
                description=f"Выполнить этап производства для заказа #{order_id}",
                assigned_to=self._get_employee_for_step(step.name),
                priority="medium",
                related_order_id=order_id,
                related_production_step_id=step.id
            )
            self.db.add(task)
            assigned_tasks.append(task)

        self.db.commit()

        context["tasks_assigned"] = True
        context["tasks_count"] = len(assigned_tasks)

        return {"tasks_assigned": len(assigned_tasks)}

    async def _notify_customer_order_created(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Уведомление клиента о создании заказа"""
        customer_email = context.get("customer_email")
        order_id = context["entity_id"]

        if customer_email:
            # Используем robot service для отправки уведомления
            await self.robot_service.execute_robot_action(
                robot_id="system_notification",
                action_config={
                    "action_type": "send_email",
                    "config": {
                        "template": "order_created",
                        "email": customer_email,
                        "order_id": order_id
                    }
                },
                entity_type=EntityType.ORDER,
                entity_id=order_id
            )

        return {"notification_sent": bool(customer_email)}

    async def _validate_payment(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Валидация платежа"""
        payment_amount = context.get("trigger_data", {}).get("amount", 0)
        order_total = context.get("order_total", 0)

        if payment_amount < order_total:
            raise ValueError(f"Payment amount {payment_amount} less than order total {order_total}")

        context["payment_valid"] = True
        return {"payment_validated": True}

    async def _update_order_to_paid(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Обновление статуса заказа на оплаченный"""
        order_id = context["entity_id"]

        order = self.db.query(Order).filter(Order.id == order_id).first()
        if order:
            order.status = OrderStatus.paid
            self.db.commit()

        context["order_status"] = "paid"
        return {"order_updated": True}

    async def _start_production_workflow(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Запуск производства"""
        order_id = context["entity_id"]

        # Обновляем статус этапов производства
        steps = self.db.query(ProductionStep).filter(
            ProductionStep.order_id == order_id,
            ProductionStep.sequence == 1  # Первый этап
        ).all()

        for step in steps:
            step.status = StepStatus.in_progress
            step.started_at = datetime.utcnow()

        self.db.commit()

        return {"production_started": True}

    async def _check_production_completion(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Проверка завершения всех этапов производства"""
        order_id = context["entity_id"]

        # Проверяем все этапы
        total_steps = self.db.query(ProductionStep).filter(
            ProductionStep.order_id == order_id
        ).count()

        completed_steps = self.db.query(ProductionStep).filter(
            ProductionStep.order_id == order_id,
            ProductionStep.status == StepStatus.completed
        ).count()

        all_completed = total_steps == completed_steps
        context["all_steps_completed"] = all_completed

        return {"total_steps": total_steps, "completed_steps": completed_steps, "all_completed": all_completed}

    async def _mark_order_completed(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Отметка заказа как завершенного"""
        order_id = context["entity_id"]

        order = self.db.query(Order).filter(Order.id == order_id).first()
        if order:
            order.status = OrderStatus.completed
            self.db.commit()

        context["order_completed"] = True
        return {"order_marked_completed": True}

    async def _notify_customer_delivery_ready(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Уведомление клиента о готовности к доставке"""
        customer_email = context.get("customer_email")
        order_id = context["entity_id"]

        if customer_email:
            await self.robot_service.execute_robot_action(
                robot_id="system_notification",
                action_config={
                    "action_type": "send_email",
                    "config": {
                        "template": "order_ready",
                        "email": customer_email,
                        "order_id": order_id
                    }
                },
                entity_type=EntityType.ORDER,
                entity_id=order_id
            )

        return {"delivery_notification_sent": bool(customer_email)}

    async def _analyze_complaint(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ жалобы"""
        complaint_text = context.get("trigger_data", {}).get("complaint_text", "")

        # Простой анализ серьезности
        severity = "low"
        if any(word in complaint_text.lower() for word in ["брак", "плохо", "ужасно", "возврат"]):
            severity = "high"
        elif any(word in complaint_text.lower() for word in ["задержка", "долго", "проблема"]):
            severity = "medium"

        context["complaint_severity"] = severity
        return {"severity": severity}

    async def _escalate_complaint(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Эскалация жалобы"""
        severity = context.get("complaint_severity", "low")

        # Создаем задачу для менеджера
        task = Task(
            user_id=1,
            title=f"Эскалация жалобы (severity: {severity})",
            description=f"Клиент {context.get('customer_email')} подал жалобу высокой серьезности",
            assigned_to=self._get_manager_for_complaints(),
            priority="high" if severity == "high" else "medium"
        )
        self.db.add(task)
        self.db.commit()

        context["escalation_needed"] = True
        return {"escalated": True, "task_id": task.id}

    async def _create_resolution_task(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Создание задачи на разрешение жалобы"""
        task = Task(
            user_id=1,
            title="Разрешение жалобы клиента",
            description=f"Обработать жалобу клиента {context.get('customer_email')}",
            assigned_to=self._get_support_employee(),
            priority="medium"
        )
        self.db.add(task)
        self.db.commit()

        return {"resolution_task_created": True, "task_id": task.id}

    def _get_production_steps_for_print_type(self, print_type: str) -> List[str]:
        """Получить этапы производства для типа печати"""
        steps = {
            "screen_print": [
                "Подготовка макета",
                "Создание формы",
                "Печать",
                "Сушка и термообработка",
                "Контроль качества",
                "Упаковка"
            ],
            "dtg": [
                "Подготовка принтера",
                "Печать DTG",
                "Фиксация красок",
                "Финальная сушка",
                "Контроль качества",
                "Упаковка"
            ],
            "embroidery": [
                "Оцифровка дизайна",
                "Подготовка машины",
                "Вышивка",
                "Контроль качества",
                "Упаковка"
            ]
        }
        return steps.get(print_type, steps["screen_print"])

    def _get_employee_for_step(self, step_name: str) -> Optional[int]:
        """Получить сотрудника для этапа производства"""
        # Простая логика назначения
        assignments = {
            "дизайн": 2,  # Дизайнер
            "печать": 3,  # Печатник
            "вышивка": 4, # Вышивальщик
            "упаковка": 5 # Упаковщик
        }

        for key, employee_id in assignments.items():
            if key in step_name.lower():
                return employee_id

        return 3  # По умолчанию печатник

    def _get_manager_for_complaints(self) -> int:
        """Получить менеджера для жалоб"""
        return 1  # Главный менеджер

    def _get_support_employee(self) -> int:
        """Получить сотрудника поддержки"""
        return 6  # Сотрудник поддержки


# Глобальный экземпляр движка
workflow_engine = None

def get_workflow_engine(db: Session) -> WorkflowEngine:
    """Получить экземпляр workflow engine"""
    global workflow_engine
    if workflow_engine is None:
        workflow_engine = WorkflowEngine(db)
    return workflow_engine
