"""
Pydantic схемы для email API
"""

from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class EmailAttachment(BaseModel):
    """Схема вложения для email"""

    filename: str = Field(..., description="Имя файла вложения")
    content: bytes = Field(..., description="Содержимое файла в байтах")
    content_type: str = Field(
        default="application/octet-stream", description="MIME тип файла"
    )


class EmailRequest(BaseModel):
    """Схема запроса на отправку email"""

    to: str | List[EmailStr] = Field(..., description="Получатель(и) email")
    subject: str = Field(..., description="Тема письма", max_length=200)
    body: str = Field(..., description="Текстовое содержимое письма")
    html_body: Optional[str] = Field(None, description="HTML версия письма")
    cc: Optional[List[EmailStr]] = Field(None, description="Копия получателям")
    bcc: Optional[List[EmailStr]] = Field(None, description="Скрытая копия получателям")
    reply_to: Optional[EmailStr] = Field(None, description="Адрес для ответа")


class TemplateEmailRequest(BaseModel):
    """Схема запроса на отправку шаблонного email"""

    template_name: str = Field(
        ..., description="Имя шаблона", examples=["order_confirmation", "task_assigned"]
    )
    to: str | List[EmailStr] = Field(..., description="Получатель(и) email")
    template_data: dict = Field(..., description="Данные для подстановки в шаблон")
    subject: str = Field(..., description="Тема письма", max_length=200)
    cc: Optional[List[EmailStr]] = Field(None, description="Копия получателям")
    bcc: Optional[List[EmailStr]] = Field(None, description="Скрытая копия получателям")


class EmailStatusResponse(BaseModel):
    """Схема ответа со статусом отправки email"""

    success: bool = Field(..., description="Успешность отправки")
    message: str = Field(..., description="Сообщение о статусе")
    email_id: Optional[str] = Field(
        None, description="Уникальный ID отправленного email"
    )


class EmailTemplateInfo(BaseModel):
    """Информация о email шаблоне"""

    name: str = Field(..., description="Человекопонятное название шаблона")
    description: str = Field(..., description="Описание назначения шаблона")
    required_fields: List[str] = Field(..., description="Обязательные поля для шаблона")


class EmailTemplatesResponse(BaseModel):
    """Ответ со списком доступных шаблонов"""

    templates: dict[str, EmailTemplateInfo] = Field(..., description="Словарь шаблонов")
    total: int = Field(..., description="Общее количество шаблонов")


class EmailServiceStatus(BaseModel):
    """Статус email сервиса"""

    service: str = Field(default="email", description="Название сервиса")
    status: str = Field(
        ...,
        description="Статус конфигурации",
        examples=["configured", "not_configured"],
    )
    config: dict = Field(..., description="Информация о конфигурации")


class TestEmailRequest(BaseModel):
    """Запрос на тестовую отправку email"""

    test_email: EmailStr = Field(..., description="Email адрес для тестового сообщения")
