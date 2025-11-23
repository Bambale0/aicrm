"""
Модель клиента
"""
from sqlalchemy import Column, String, Integer, Numeric, JSON, Boolean
from sqlalchemy.orm import relationship

from .base import BaseModel


class Customer(BaseModel):
    """Модель клиента"""

    __tablename__ = "customers"

    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    contact_info = Column(JSON)  # Дополнительная контактная информация
    address = Column(String)
    total_orders = Column(Integer, default=0)
    total_spent = Column(Numeric(10, 2), default=0.00)
    loyalty_level = Column(String, default="bronze")  # bronze, silver, gold, platinum
    notes = Column(String)
    is_deleted = Column(Boolean, default=False)  # Soft delete flag

    # Связи
    orders = relationship("Order", back_populates="customer")
    communications = relationship("Communication", back_populates="customer")
    avito_chat_settings = relationship("AvitoChatSettings", back_populates="customer")
    telegram_chats = relationship("TelegramChat", back_populates="customer")

    def update_stats(self):
        """Обновление статистики клиента"""
        self.total_orders = len(self.orders)
        self.total_spent = sum(order.total_amount for order in self.orders if order.total_amount)

        # Определение уровня лояльности
        if self.total_spent > 10000:
            self.loyalty_level = "platinum"
        elif self.total_spent > 5000:
            self.loyalty_level = "gold"
        elif self.total_spent > 1000:
            self.loyalty_level = "silver"
        else:
            self.loyalty_level = "bronze"

    def __repr__(self) -> str:
        return f"<Customer(name={self.name}, email={self.email})>"
