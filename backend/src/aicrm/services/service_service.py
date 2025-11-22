"""
Сервис для управления услугами
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from ..models.service import Service


class ServiceService:
    """Сервис для работы с услугами"""

    def __init__(self, db: Session):
        self.db = db

    def get_all_services(self) -> List[Service]:
        """Получить все услуги"""
        return self.db.query(Service).order_by(Service.category, Service.name).all()

    def get_active_services(self) -> List[Service]:
        """Получить активные услуги"""
        return self.db.query(Service).filter(Service.is_active == True).order_by(Service.category, Service.name).all()

    def get_services_by_category(self, category: str) -> List[Service]:
        """Получить услуги по категории"""
        return self.db.query(Service).filter(
            Service.category == category,
            Service.is_active == True
        ).order_by(Service.name).all()

    def get_service_by_id(self, service_id: int) -> Optional[Service]:
        """Получить услугу по ID"""
        return self.db.query(Service).filter(Service.id == service_id).first()

    def create_service(self, name: str, description: str, price: float, category: str, **kwargs) -> Service:
        """Создать новую услугу"""
        service = Service(
            name=name,
            description=description,
            price=price,
            category=category,
            **kwargs
        )
        self.db.add(service)
        self.db.commit()
        self.db.refresh(service)
        return service

    def update_service(self, service_id: int, **kwargs) -> Optional[Service]:
        """Обновить услугу"""
        service = self.get_service_by_id(service_id)
        if not service:
            return None

        for key, value in kwargs.items():
            if hasattr(service, key):
                setattr(service, key, value)

        self.db.commit()
        self.db.refresh(service)
        return service

    def delete_service(self, service_id: int) -> bool:
        """Удалить услугу"""
        service = self.get_service_by_id(service_id)
        if not service:
            return False

        self.db.delete(service)
        self.db.commit()
        return True

    def toggle_service_status(self, service_id: int) -> Optional[Service]:
        """Переключить статус услуги (активна/неактивна)"""
        service = self.get_service_by_id(service_id)
        if not service:
            return None

        service.is_active = not service.is_active
        self.db.commit()
        self.db.refresh(service)
        return service

    def get_categories(self) -> List[str]:
        """Получить список уникальных категорий услуг"""
        result = self.db.query(Service.category).distinct().all()
        return [row[0] for row in result]
