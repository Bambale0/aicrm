"""
Сервис управления производством
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from ..models.order import Order, OrderStatus
from ..models.production_step import ProductionStep, StepStatus
import logging

logger = logging.getLogger(__name__)


class ProductionService:
    """
    Сервис управления производственным процессом
    """

    def __init__(self, db: Session):
        self.db = db

    def create_production_workflow(self, order_id: int) -> List[ProductionStep]:
        """
        Автоматическое создание workflow производства для заказа
        """
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError(f"Заказ с ID {order_id} не найден")

        # Стандартные этапы для печати на одежде
        steps_config = [
            {"name": "Подготовка макета", "description": "Подготовка и оптимизация дизайн-макета", "duration_hours": 24},
            {"name": "Подготовка материалов", "description": "Подготовка ткани и расходных материалов", "duration_hours": 12},
            {"name": "Печать", "description": "Нанесение принта на изделия", "duration_hours": 48},
            {"name": "Пост-обработка", "description": "Фиксация краски и финальная обработка", "duration_hours": 24},
            {"name": "Контроль качества", "description": "Проверка качества и финальный осмотр", "duration_hours": 6},
        ]

        steps = []
        for i, config in enumerate(steps_config):
            step = ProductionStep(
                order_id=order_id,
                name=config["name"],
                description=config["description"],
                sequence_number=i + 1,
                status=StepStatus.PENDING,
                estimated_hours=config["duration_hours"]
            )
            self.db.add(step)
            steps.append(step)

        self.db.commit()

        # Обновляем статус заказа
        order.update_status(OrderStatus.IN_DESIGN)
        self.db.commit()

        logger.info(f"Создан workflow производства для заказа {order_id} с {len(steps)} этапами")
        return steps

    def update_progress(self, order_id: int) -> Dict[str, Any]:
        """
        Обновление и расчет прогресса производства заказа
        """
        steps = self.db.query(ProductionStep).filter(
            ProductionStep.order_id == order_id
        ).order_by(ProductionStep.sequence_number).all()

        if not steps:
            return {
                "total_steps": 0,
                "completed_steps": 0,
                "progress": 0.0,
                "current_step": None,
                "next_step": None,
                "is_overdue": False
            }

        total_steps = len(steps)
        completed_steps = len([s for s in steps if s.status == StepStatus.COMPLETED])
        in_progress_steps = [s for s in steps if s.status == StepStatus.IN_PROGRESS]
        pending_steps = [s for s in steps if s.status == StepStatus.PENDING]

        # Расчет общего прогресса
        progress = ((completed_steps + len(in_progress_steps) * 0.5) / total_steps) * 100
        progress = min(progress, 100.0)

        # Текущий и следующий этапы
        current_step = in_progress_steps[0] if in_progress_steps else None
        next_step = pending_steps[0] if pending_steps else None

        # Проверка просрочки
        is_overdue = any(step.is_overdue for step in steps if step.status == StepStatus.IN_PROGRESS)

        return {
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "in_progress_steps": len(in_progress_steps),
            "pending_steps": len(pending_steps),
            "progress": round(progress, 2),
            "current_step": current_step.name if current_step else None,
            "next_step": next_step.name if next_step else None,
            "is_overdue": is_overdue,
            "steps": [
                {
                    "id": step.id,
                    "name": step.name,
                    "status": step.status.value,
                    "sequence_number": step.sequence_number,
                    "estimated_hours": step.estimated_hours,
                    "actual_hours": step.actual_hours,
                    "started_at": step.started_at.isoformat() if step.started_at else None,
                    "completed_at": step.completed_at.isoformat() if step.completed_at else None,
                    "is_overdue": step.is_overdue,
                    "progress_percentage": step.progress_percentage
                } for step in steps
            ]
        }

    def start_step(self, step_id: int, user_id: int = None) -> ProductionStep:
        """
        Начать выполнение этапа производства
        """
        step = self.db.query(ProductionStep).filter(ProductionStep.id == step_id).first()
        if not step:
            raise ValueError(f"Этап с ID {step_id} не найден")

        if step.status != StepStatus.PENDING:
            raise ValueError(f"Этап {step.name} уже в статусе {step.status.value}")

        step.start_work()
        if user_id:
            step.assigned_user_id = user_id

        self.db.commit()
        logger.info(f"Начат этап '{step.name}' для заказа {step.order_id}")
        return step

    def complete_step(self, step_id: int, actual_hours: float = None, notes: str = None) -> ProductionStep:
        """
        Завершить выполнение этапа производства
        """
        step = self.db.query(ProductionStep).filter(ProductionStep.id == step_id).first()
        if not step:
            raise ValueError(f"Этап с ID {step_id} не найден")

        if step.status != StepStatus.IN_PROGRESS:
            raise ValueError(f"Этап {step.name} не в работе (статус: {step.status.value})")

        step.complete_work(actual_hours, notes)
        self.db.commit()

        # Проверяем, нужно ли запустить следующий этап
        self._check_and_start_next_step(step.order_id)

        # Проверяем, завершен ли весь заказ
        self._check_order_completion(step.order_id)

        logger.info(f"Завершен этап '{step.name}' для заказа {step.order_id}")
        return step

    def _check_and_start_next_step(self, order_id: int):
        """
        Проверить и автоматически запустить следующий этап
        """
        steps = self.db.query(ProductionStep).filter(
            ProductionStep.order_id == order_id
        ).order_by(ProductionStep.sequence_number).all()

        # Найти первый ожидающий этап
        pending_steps = [s for s in steps if s.status == StepStatus.PENDING]
        if pending_steps:
            next_step = pending_steps[0]
            # Автоматически запускаем следующий этап
            next_step.start_work()
            self.db.commit()
            logger.info(f"Автоматически запущен следующий этап '{next_step.name}' для заказа {order_id}")

    def _check_order_completion(self, order_id: int):
        """
        Проверить, завершен ли весь заказ
        """
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return

        steps = order.production_steps
        if not steps:
            return

        # Если все этапы завершены, переводим заказ в статус READY
        all_completed = all(step.status == StepStatus.COMPLETED for step in steps)
        if all_completed and order.status != OrderStatus.READY:
            order.update_status(OrderStatus.READY)
            self.db.commit()
            logger.info(f"Заказ {order_id} автоматически переведен в статус 'Готов'")

    def get_overdue_steps(self) -> List[Dict[str, Any]]:
        """
        Получить список просроченных этапов
        """
        overdue_steps = self.db.query(ProductionStep).filter(
            ProductionStep.status == StepStatus.IN_PROGRESS,
            ProductionStep.started_at.isnot(None),
            ProductionStep.estimated_hours.isnot(None)
        ).all()

        result = []
        for step in overdue_steps:
            if step.is_overdue:
                order = step.order
                result.append({
                    "step_id": step.id,
                    "step_name": step.name,
                    "order_id": step.order_id,
                    "customer_name": order.customer.name if order.customer else "Неизвестен",
                    "overdue_hours": (datetime.utcnow() - (step.started_at + timedelta(hours=step.estimated_hours))).total_seconds() / 3600,
                    "started_at": step.started_at.isoformat()
                })

        return result

    def reassign_step(self, step_id: int, user_id: int) -> ProductionStep:
        """
        Переназначить этап другому исполнителю
        """
        step = self.db.query(ProductionStep).filter(ProductionStep.id == step_id).first()
        if not step:
            raise ValueError(f"Этап с ID {step_id} не найден")

        step.assigned_user_id = user_id
        self.db.commit()

        logger.info(f"Этап '{step.name}' переназначен пользователю {user_id}")
        return step
