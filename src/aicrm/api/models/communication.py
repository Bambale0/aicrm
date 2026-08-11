"""
Модель коммуникации
"""

from sqlalchemy import JSON, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import BaseModel


class Communication(BaseModel):
    """Модель коммуникации с клиентом"""

    __tablename__ = "communications"

    channel = Column(
        String, nullable=False, index=True
    )  # telegram, avito, email, phone, website
    direction = Column(String, nullable=False, index=True)  # inbound, outbound
    message_content = Column(Text, nullable=False)
    message_type = Column(String, default="text")  # text, image, file, voice
    customer_id = Column(Integer, ForeignKey("customers.id"), index=True)
    order_id = Column(
        Integer, ForeignKey("orders.id"), index=True
    )  # Связанный заказ (опционально)
    user_id = Column(
        Integer, ForeignKey("users.id"), index=True
    )  # Кто обработал/отправил
    ai_response_id = Column(String)  # ID ответа от AI
    extra_data = Column(JSON)  # Дополнительные данные (файлы, изображения и т.д.)
    sentiment = Column(String)  # positive, neutral, negative (определяется AI)
    intent = Column(String)  # order, complaint, question, etc.

    # Связи
    customer = relationship("Customer", back_populates="communications")
    order = relationship("Order", back_populates="communications")

    @property
    def channel_display(self) -> str:
        """Человеко-читаемый канал"""
        channels = {
            "telegram": "Telegram",
            "avito": "Avito",
            "email": "Email",
            "phone": "Телефон",
            "website": "Сайт",
        }
        return channels.get(self.channel, self.channel)

    @property
    def direction_display(self) -> str:
        """Человеко-читаемый направление"""
        directions = {"inbound": "Входящее", "outbound": "Исходящее"}
        return directions.get(self.direction, self.direction)

    def __repr__(self) -> str:
        return f"<Communication(channel={self.channel}, direction={self.direction}, customer_id={self.customer_id})>"
