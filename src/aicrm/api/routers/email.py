"""
API роутер для отправки email сообщений
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, EmailStr

from ...services.email_service import email_service, EmailMessage, EmailAttachment
from .auth import get_current_user
from ...models.user import User

router = APIRouter(prefix="/email", tags=["email"])


class EmailRequest(BaseModel):
    """Запрос на отправку email"""
    to: str | List[EmailStr]
    subject: str
    body: str
    html_body: Optional[str] = None
    cc: Optional[List[EmailStr]] = None
    bcc: Optional[List[EmailStr]] = None
    reply_to: Optional[EmailStr] = None


class TemplateEmailRequest(BaseModel):
    """Запрос на отправку шаблонного email"""
    template_name: str
    to: str | List[EmailStr]
    template_data: Dict[str, Any]
    subject: str
    cc: Optional[List[EmailStr]] = None
    bcc: Optional[List[EmailStr]] = None


class EmailStatusResponse(BaseModel):
    """Ответ со статусом отправки"""
    success: bool
    message: str
    email_id: Optional[str] = None


@router.post("/send", response_model=EmailStatusResponse)
async def send_email(
    request: EmailRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Отправка email сообщения

    Требуется аутентификация пользователя.
    """
    try:
        message = EmailMessage(
            to=request.to,
            subject=request.subject,
            body=request.body,
            html_body=request.html_body,
            cc=request.cc,
            bcc=request.bcc,
            reply_to=request.reply_to
        )

        # Отправляем в фоне для лучшей производительности
        background_tasks.add_task(email_service.send_email, message)

        return EmailStatusResponse(
            success=True,
            message="Email принят в очередь на отправку",
            email_id=f"email_{current_user.id}_{request.subject[:20]}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при отправке email: {str(e)}"
        )


@router.post("/send-template", response_model=EmailStatusResponse)
async def send_template_email(
    request: TemplateEmailRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Отправка email с использованием шаблона

    Доступные шаблоны:
    - order_confirmation: Подтверждение заказа
    - task_assigned: Уведомление о назначении задачи

    Требуется аутентификация пользователя.
    """
    try:
        # Отправляем в фоне для лучшей производительности
        background_tasks.add_task(
            email_service.send_template_email,
            request.template_name,
            request.to,
            request.template_data,
            request.subject
        )

        return EmailStatusResponse(
            success=True,
            message="Шаблонный email принят в очередь на отправку",
            email_id=f"template_{current_user.id}_{request.template_name}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при отправке шаблонного email: {str(e)}"
        )


@router.post("/test", response_model=EmailStatusResponse)
async def test_email_config(
    test_email: EmailStr,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Тестовая отправка email для проверки конфигурации SMTP

    Отправляет тестовое сообщение на указанный email адрес.
    Требуется аутентификация пользователя.
    """
    try:
        message = EmailMessage(
            to=test_email,
            subject="Тестовое сообщение от AI CRM",
            body=f"""
            Привет!

            Это тестовое сообщение от системы AI CRM.
            Если вы получили это письмо, значит конфигурация email работает корректно.

            Отправлено пользователем: {current_user.email}
            Время отправки: {__import__('datetime').datetime.now()}

            С уважением,
            Команда AI CRM
            """,
            html_body=f"""
            <html>
            <body>
                <h2>Тестовое сообщение от AI CRM</h2>
                <p>Привет!</p>
                <p>Это тестовое сообщение от системы AI CRM.</p>
                <p>Если вы получили это письмо, значит конфигурация email работает корректно.</p>
                <br>
                <p><strong>Отправлено пользователем:</strong> {current_user.email}</p>
                <p><strong>Время отправки:</strong> {__import__('datetime').datetime.now()}</p>
                <br>
                <p>С уважением,<br>Команда AI CRM</p>
            </body>
            </html>
            """
        )

        # Отправляем в фоне
        background_tasks.add_task(email_service.send_email, message)

        return EmailStatusResponse(
            success=True,
            message=f"Тестовое email отправлено на {test_email}",
            email_id=f"test_{current_user.id}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при отправке тестового email: {str(e)}"
        )


@router.get("/templates")
async def get_available_templates(current_user: User = Depends(get_current_user)):
    """
    Получение списка доступных email шаблонов

    Требуется аутентификация пользователя.
    """
    templates = {
        "order_confirmation": {
            "name": "Подтверждение заказа",
            "description": "Отправляется клиенту после оформления заказа",
            "required_fields": ["order_id", "customer_name", "total_amount", "deadline"]
        },
        "task_assigned": {
            "name": "Уведомление о задаче",
            "description": "Отправляется исполнителю при назначении задачи",
            "required_fields": ["task_id", "assignee_name", "task_title", "task_description", "priority", "deadline"]
        }
    }

    return {
        "templates": templates,
        "total": len(templates)
    }


@router.get("/status")
async def get_email_service_status(current_user: User = Depends(get_current_user)):
    """
    Получение статуса email сервиса

    Требуется аутентификация пользователя.
    """
    from ...core.config import settings

    config_status = {
        "smtp_server": settings.SMTP_SERVER,
        "smtp_port": settings.SMTP_PORT,
        "from_email": settings.FROM_EMAIL,
        "smtp_username": bool(settings.SMTP_USERNAME),
        "smtp_configured": bool(settings.SMTP_USERNAME and settings.SMTP_PASSWORD)
    }

    return {
        "service": "email",
        "status": "configured" if config_status["smtp_configured"] else "not_configured",
        "config": config_status
    }
