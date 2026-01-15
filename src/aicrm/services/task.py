"""
Сервис управления задачами
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from ..models.task import Task


class TaskService:
    """Сервис для работы с задачами"""

    @staticmethod
    def create_task(db: Session, task_data: dict, created_by: int) -> Task:
        """Создание новой задачи"""
        task_data["created_by"] = created_by
        task_data["status"] = "todo"  # По умолчанию
        task = Task(**task_data)
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def get_task(db: Session, task_id: int) -> Optional[Task]:
        """Получение задачи по ID"""
        return db.query(Task).filter(Task.id == task_id).first()

    @staticmethod
    def get_tasks(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        assigned_to: Optional[int] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> List[Task]:
        """Получение списка задач с фильтрацией"""
        query = db.query(Task)

        if assigned_to:
            query = query.filter(Task.assigned_to == assigned_to)
        if status:
            query = query.filter(Task.status == status)
        if priority:
            query = query.filter(Task.priority == priority)

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update_task(db: Session, task_id: int, update_data: dict) -> Optional[Task]:
        """Обновление данных задачи"""
        task = TaskService.get_task(db, task_id)
        if not task:
            return None

        for key, value in update_data.items():
            if value is not None:
                setattr(task, key, value)

        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def delete_task(db: Session, task_id: int) -> bool:
        """Удаление задачи"""
        task = TaskService.get_task(db, task_id)
        if not task:
            return False

        db.delete(task)
        db.commit()
        return True

    @staticmethod
    def complete_task(db: Session, task_id: int) -> Optional[Task]:
        """Завершение задачи"""
        task = TaskService.get_task(db, task_id)
        if not task:
            return None

        task.complete()
        db.commit()
        db.refresh(task)
        return task


task_service = TaskService()
