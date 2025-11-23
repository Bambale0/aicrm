"""
API роутер для отправки email сообщений
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, EmailStr

from ...services.email_service import (
    email_service, EmailMessage, EmailTemplate
)
from ...core.dependencies import get_current_user
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
        "smtp_server": settings.smtp_server,
        "smtp_port": settings.smtp_port,
        "from_email": settings.from_email,
        "smtp_username": bool(settings.smtp_username),
        "smtp_configured": bool(settings.smtp_username and settings.smtp_password)
    }

    return {
        "service": "email",
        "status": "configured" if config_status["smtp_configured"] else "not_configured",
        "config": config_status
    }





# ==================== IMAP ENDPOINTS ====================

class EmailFolderResponse(BaseModel):
    """Ответ с информацией о папке"""
    name: str
    flags: List[str]
    delimiter: str
    total_messages: int
    recent_messages: int
    unseen_messages: int


class ReceivedEmailResponse(BaseModel):
    """Ответ с полученным email"""
    id: str
    uid: str
    subject: str
    from_addr: str
    from_name: str
    to: List[str]
    cc: List[str] = []
    date: str  # ISO format
    body_text: str
    body_html: Optional[str] = None
    attachments: List[Dict[str, Any]] = []
    flags: List[str] = []
    size: int
    message_id: Optional[str] = None
    folder: str
    is_read: bool
    is_flagged: bool
    is_deleted: bool


class EmailActionRequest(BaseModel):
    """Запрос на действие с email"""
    message_ids: List[str]
    folder: str = "INBOX"


class EmailMoveRequest(BaseModel):
    """Запрос на перемещение email"""
    message_ids: List[str]
    from_folder: str
    to_folder: str


class EmailSearchRequest(BaseModel):
    """Запрос поиска email"""
    query: str
    folder: str = "INBOX"
    limit: int = 50


@router.get("/folders", response_model=List[EmailFolderResponse])
async def get_email_folders(current_user: User = Depends(get_current_user)):
    """
    Получение списка email папок через IMAP

    Требуется аутентификация пользователя.
    """
    try:
        folders = await email_service.get_folders()
        return [
            EmailFolderResponse(
                name=f.name,
                flags=f.flags,
                delimiter=f.delimiter,
                total_messages=f.total_messages,
                recent_messages=f.recent_messages,
                unseen_messages=f.unseen_messages
            )
            for f in folders
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении папок: {str(e)}"
        )


@router.get("/messages", response_model=List[ReceivedEmailResponse])
async def get_email_messages(
    folder: str = "INBOX",
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user)
):
    """
    Получение email сообщений из папки

    Параметры:
    - folder: Имя папки (по умолчанию INBOX)
    - limit: Максимальное количество сообщений (по умолчанию 50)
    - offset: Смещение для пагинации (по умолчанию 0)

    Требуется аутентификация пользователя.
    """
    try:
        messages = await email_service.get_emails(
            folder=folder,
            limit=limit,
            offset=offset
        )

        return [
            ReceivedEmailResponse(
                id=msg.id,
                uid=msg.uid,
                subject=msg.subject,
                from_addr=msg.from_addr,
                from_name=msg.from_name,
                to=msg.to,
                cc=msg.cc,
                date=msg.date.isoformat(),
                body_text=msg.body_text,
                body_html=msg.body_html,
                attachments=[
                    {
                        "filename": att.filename,
                        "content_type": att.content_type,
                        "size": att.size
                    }
                    for att in msg.attachments
                ],
                flags=msg.flags,
                size=msg.size,
                message_id=msg.message_id,
                folder=msg.folder,
                is_read=msg.is_read,
                is_flagged=msg.is_flagged,
                is_deleted=msg.is_deleted
            )
            for msg in messages
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении сообщений: {str(e)}"
        )


@router.post("/search", response_model=List[ReceivedEmailResponse])
async def search_emails(
    request: EmailSearchRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Поиск email сообщений

    Требуется аутентификация пользователя.
    """
    try:
        messages = await email_service.search_emails(
            query=request.query,
            folder=request.folder,
            limit=request.limit
        )

        return [
            ReceivedEmailResponse(
                id=msg.id,
                uid=msg.uid,
                subject=msg.subject,
                from_addr=msg.from_addr,
                from_name=msg.from_name,
                to=msg.to,
                cc=msg.cc,
                date=msg.date.isoformat(),
                body_text=msg.body_text,
                body_html=msg.body_html,
                attachments=[
                    {
                        "filename": att.filename,
                        "content_type": att.content_type,
                        "size": att.size
                    }
                    for att in msg.attachments
                ],
                flags=msg.flags,
                size=msg.size,
                message_id=msg.message_id,
                folder=msg.folder,
                is_read=msg.is_read,
                is_flagged=msg.is_flagged,
                is_deleted=msg.is_deleted
            )
            for msg in messages
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при поиске сообщений: {str(e)}"
        )


@router.post("/mark-read")
async def mark_emails_as_read(
    request: EmailActionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Отметить email сообщения как прочитанные

    Требуется аутентификация пользователя.
    """
    try:
        success = await email_service.mark_as_read(
            message_ids=request.message_ids,
            folder=request.folder
        )

        if success:
            return {"success": True, "message": "Сообщения отмечены как прочитанные"}
        else:
            raise HTTPException(status_code=500, detail="Не удалось отметить сообщения как прочитанные")

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при отметке сообщений: {str(e)}"
        )


@router.post("/mark-unread")
async def mark_emails_as_unread(
    request: EmailActionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Отметить email сообщения как непрочитанные

    Требуется аутентификация пользователя.
    """
    try:
        success = await email_service.mark_as_unread(
            message_ids=request.message_ids,
            folder=request.folder
        )

        if success:
            return {"success": True, "message": "Сообщения отмечены как непрочитанные"}
        else:
            raise HTTPException(status_code=500, detail="Не удалось отметить сообщения как непрочитанные")

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при отметке сообщений: {str(e)}"
        )


@router.post("/flag")
async def flag_emails(
    request: EmailActionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Пометить email сообщения флагом

    Требуется аутентификация пользователя.
    """
    try:
        success = await email_service.flag_messages(
            message_ids=request.message_ids,
            folder=request.folder
        )

        if success:
            return {"success": True, "message": "Сообщения помечены флагом"}
        else:
            raise HTTPException(status_code=500, detail="Не удалось пометить сообщения флагом")

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при установке флага: {str(e)}"
        )


@router.post("/unflag")
async def unflag_emails(
    request: EmailActionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Снять флаг с email сообщений

    Требуется аутентификация пользователя.
    """
    try:
        success = await email_service.unflag_messages(
            message_ids=request.message_ids,
            folder=request.folder
        )

        if success:
            return {"success": True, "message": "Флаг снят с сообщений"}
        else:
            raise HTTPException(status_code=500, detail="Не удалось снять флаг с сообщений")

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при снятии флага: {str(e)}"
        )


@router.post("/delete")
async def delete_emails(
    request: EmailActionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Удалить email сообщения

    Требуется аутентификация пользователя.
    """
    try:
        success = await email_service.delete_messages(
            message_ids=request.message_ids,
            folder=request.folder
        )

        if success:
            return {"success": True, "message": "Сообщения удалены"}
        else:
            raise HTTPException(status_code=500, detail="Не удалось удалить сообщения")

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при удалении сообщений: {str(e)}"
        )


@router.post("/move")
async def move_emails(
    request: EmailMoveRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Переместить email сообщения между папками

    Требуется аутентификация пользователя.
    """
    try:
        success = await email_service.move_messages(
            message_ids=request.message_ids,
            from_folder=request.from_folder,
            to_folder=request.to_folder
        )

        if success:
            return {"success": True, "message": f"Сообщения перемещены в папку {request.to_folder}"}
        else:
            raise HTTPException(status_code=500, detail="Не удалось переместить сообщения")

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при перемещении сообщений: {str(e)}"
        )


# ==================== CONTACT MANAGEMENT ====================

class EmailContactRequest(BaseModel):
    """Запрос на добавление контакта"""
    email: EmailStr
    name: str


class EmailContactResponse(BaseModel):
    """Ответ с информацией о контакте"""
    email: str
    name: str
    frequency: int
    last_contact: Optional[str] = None
    is_blocked: bool


@router.post("/contacts", response_model=EmailContactResponse)
async def add_email_contact(
    request: EmailContactRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Добавить email контакт

    Требуется аутентификация пользователя.
    """
    try:
        success = await email_service.add_contact(
            email=request.email,
            name=request.name
        )

        if success:
            # Получаем добавленный контакт
            contacts = await email_service.get_contacts(search=request.email)
            if contacts:
                contact = contacts[0]
                return EmailContactResponse(
                    email=contact.email,
                    name=contact.name,
                    frequency=contact.frequency,
                    last_contact=contact.last_contact.isoformat() if contact.last_contact else None,
                    is_blocked=contact.is_blocked
                )

        raise HTTPException(status_code=500, detail="Не удалось добавить контакт")

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при добавлении контакта: {str(e)}"
        )


@router.get("/contacts", response_model=List[EmailContactResponse])
async def get_email_contacts(
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Получить список email контактов

    Параметры:
    - search: Строка поиска по email или имени

    Требуется аутентификация пользователя.
    """
    try:
        contacts = await email_service.get_contacts(search=search)

        return [
            EmailContactResponse(
                email=c.email,
                name=c.name,
                frequency=c.frequency,
                last_contact=c.last_contact.isoformat() if c.last_contact else None,
                is_blocked=c.is_blocked
            )
            for c in contacts
        ]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении контактов: {str(e)}"
        )


# ==================== TEMPLATE MANAGEMENT ====================

class EmailTemplateRequest(BaseModel):
    """Запрос на создание шаблона"""
    name: str
    subject_template: str
    html_template: str
    text_template: str
    variables: List[str] = []
    category: str = "general"


class EmailTemplateResponse(BaseModel):
    """Ответ с информацией о шаблоне"""
    name: str
    subject_template: str
    html_template: str
    text_template: str
    variables: List[str]
    category: str
    created_at: str
    updated_at: str


@router.post("/templates", response_model=EmailTemplateResponse)
async def create_email_template(
    request: EmailTemplateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Создать новый email шаблон

    Требуется аутентификация пользователя.
    """
    try:
        from datetime import datetime

        template = EmailTemplate(
            name=request.name,
            subject_template=request.subject_template,
            html_template=request.html_template,
            text_template=request.text_template,
            variables=request.variables,
            category=request.category,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        success = await email_service.create_template(template)

        if success:
            return EmailTemplateResponse(
                name=template.name,
                subject_template=template.subject_template,
                html_template=template.html_template,
                text_template=template.text_template,
                variables=template.variables,
                category=template.category,
                created_at=template.created_at.isoformat(),
                updated_at=template.updated_at.isoformat()
            )

        raise HTTPException(status_code=500, detail="Не удалось создать шаблон")

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при создании шаблона: {str(e)}"
        )


@router.get("/templates/list", response_model=List[EmailTemplateResponse])
async def get_email_templates(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Получить список email шаблонов

    Параметры:
    - category: Фильтр по категории шаблонов

    Требуется аутентификация пользователя.
    """
    try:
        templates = await email_service.get_templates(category=category)

        return [
            EmailTemplateResponse(
                name=t.name,
                subject_template=t.subject_template,
                html_template=t.html_template,
                text_template=t.text_template,
                variables=t.variables,
                category=t.category,
                created_at=t.created_at.isoformat(),
                updated_at=t.updated_at.isoformat()
            )
            for t in templates
        ]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении шаблонов: {str(e)}"
        )


@router.post("/templates/render")
async def render_email_template(
    template_name: str,
    template_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    Рендеринг email шаблона с данными

    Требуется аутентификация пользователя.
    """
    try:
        subject, html_body, text_body = await email_service.render_template(
            template_name=template_name,
            data=template_data
        )

        return {
            "subject": subject,
            "html_body": html_body,
            "text_body": text_body
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при рендеринге шаблона: {str(e)}"
        )


# ==================== SETTINGS MANAGEMENT ====================

class EmailSettingsRequest(BaseModel):
    """Запрос на сохранение настроек email"""
    smtp_host: str
    smtp_port: int = 587
    smtp_username: str
    smtp_password: str
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    imap_host: str
    imap_port: int = 993
    imap_username: str
    imap_password: str
    imap_use_ssl: bool = True
    default_from_email: str
    default_from_name: str = ""
    signature: str = ""
    auto_reply_enabled: bool = False
    auto_reply_message: str = ""


class EmailSettingsResponse(BaseModel):
    """Ответ с настройками email"""
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_use_tls: bool
    smtp_use_ssl: bool
    imap_host: str
    imap_port: int
    imap_username: str
    imap_use_ssl: bool
    default_from_email: str
    default_from_name: str
    signature: str
    auto_reply_enabled: bool
    auto_reply_message: str


class EmailTestResult(BaseModel):
    """Результат тестирования подключения"""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None


@router.get("/settings", response_model=EmailSettingsResponse)
async def get_email_settings(current_user: User = Depends(get_current_user)):
    """
    Получить текущие настройки email

    Требуется аутентификация пользователя.
    """
    try:
        from ...core.config import settings

        # В будущем здесь можно хранить настройки в базе данных
        # Пока возвращаем настройки из конфигурации
        return EmailSettingsResponse(
            smtp_host=settings.smtp_server or "",
            smtp_port=settings.smtp_port,
            smtp_username=settings.smtp_username or "",
            smtp_use_tls=settings.smtp_use_tls,
            smtp_use_ssl=settings.smtp_use_ssl,
            imap_host="",  # Пока не реализовано в конфиге
            imap_port=993,
            imap_username="",
            imap_use_ssl=True,
            default_from_email=settings.from_email or "",
            default_from_name="",
            signature="",
            auto_reply_enabled=False,
            auto_reply_message=""
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении настроек: {str(e)}"
        )


@router.post("/settings", response_model=EmailSettingsResponse)
async def save_email_settings(
    settings_data: EmailSettingsRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Сохранить настройки email

    Требуется аутентификация пользователя.
    """
    try:
        # В будущем здесь нужно сохранить настройки в базе данных
        # Пока просто возвращаем то, что получили
        return EmailSettingsResponse(
            smtp_host=settings_data.smtp_host,
            smtp_port=settings_data.smtp_port,
            smtp_username=settings_data.smtp_username,
            smtp_use_tls=settings_data.smtp_use_tls,
            smtp_use_ssl=settings_data.smtp_use_ssl,
            imap_host=settings_data.imap_host,
            imap_port=settings_data.imap_port,
            imap_username=settings_data.imap_username,
            imap_use_ssl=settings_data.imap_use_ssl,
            default_from_email=settings_data.default_from_email,
            default_from_name=settings_data.default_from_name,
            signature=settings_data.signature,
            auto_reply_enabled=settings_data.auto_reply_enabled,
            auto_reply_message=settings_data.auto_reply_message
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при сохранении настроек: {str(e)}"
        )


@router.post("/test-smtp", response_model=EmailTestResult)
async def test_smtp_connection(
    settings_data: EmailSettingsRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Протестировать подключение к SMTP серверу

    Требуется аутентификация пользователя.
    """
    try:
        # Импортируем smtplib для тестирования
        import smtplib
        from email.mime.text import MIMEText

        # Создаем тестовое сообщение
        msg = MIMEText("Это тестовое сообщение для проверки SMTP подключения.")
        msg['Subject'] = "Тест SMTP подключения - AI CRM"
        msg['From'] = settings_data.default_from_email
        msg['To'] = settings_data.default_from_email

        # Подключаемся к SMTP серверу
        if settings_data.smtp_use_ssl:
            server = smtplib.SMTP_SSL(settings_data.smtp_host, settings_data.smtp_port)
        else:
            server = smtplib.SMTP(settings_data.smtp_host, settings_data.smtp_port)
            if settings_data.smtp_use_tls:
                server.starttls()

        # Логинимся
        server.login(settings_data.smtp_username, settings_data.smtp_password)

        # Отправляем тестовое сообщение самому себе
        server.sendmail(settings_data.default_from_email, settings_data.default_from_email, msg.as_string())

        # Закрываем соединение
        server.quit()

        return EmailTestResult(
            success=True,
            message="SMTP подключение успешно протестировано",
            details={
                "server": settings_data.smtp_host,
                "port": settings_data.smtp_port,
                "use_ssl": settings_data.smtp_use_ssl,
                "use_tls": settings_data.smtp_use_tls
            }
        )

    except smtplib.SMTPAuthenticationError:
        return EmailTestResult(
            success=False,
            message="Ошибка аутентификации. Проверьте логин и пароль.",
            details={"error_type": "authentication"}
        )
    except smtplib.SMTPConnectError:
        return EmailTestResult(
            success=False,
            message="Не удалось подключиться к SMTP серверу. Проверьте хост и порт.",
            details={"error_type": "connection"}
        )
    except smtplib.SMTPException as e:
        return EmailTestResult(
            success=False,
            message=f"SMTP ошибка: {str(e)}",
            details={"error_type": "smtp_error", "error": str(e)}
        )
    except Exception as e:
        return EmailTestResult(
            success=False,
            message=f"Неизвестная ошибка: {str(e)}",
            details={"error_type": "unknown", "error": str(e)}
        )


@router.post("/test-imap", response_model=EmailTestResult)
async def test_imap_connection(
    settings_data: EmailSettingsRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Протестировать подключение к IMAP серверу

    Требуется аутентификация пользователя.
    """
    try:
        # Импортируем imaplib для тестирования
        import imaplib

        # Подключаемся к IMAP серверу
        if settings_data.imap_use_ssl:
            mail = imaplib.IMAP4_SSL(settings_data.imap_host, settings_data.imap_port)
        else:
            mail = imaplib.IMAP4(settings_data.imap_host, settings_data.imap_port)

        # Логинимся
        mail.login(settings_data.imap_username, settings_data.imap_password)

        # Получаем список папок
        status, folders = mail.list()

        # Закрываем соединение
        mail.logout()

        if status == 'OK':
            return EmailTestResult(
                success=True,
                message="IMAP подключение успешно протестировано",
                details={
                    "server": settings_data.imap_host,
                    "port": settings_data.imap_port,
                    "use_ssl": settings_data.imap_use_ssl,
                    "folders_count": len(folders) if folders else 0
                }
            )
        else:
            return EmailTestResult(
                success=False,
                message="Не удалось получить список папок",
                details={"status": status}
            )

    except imaplib.IMAP4.error as e:
        return EmailTestResult(
            success=False,
            message=f"IMAP ошибка: {str(e)}",
            details={"error_type": "imap_error", "error": str(e)}
        )
    except Exception as e:
        return EmailTestResult(
            success=False,
            message=f"Неизвестная ошибка: {str(e)}",
            details={"error_type": "unknown", "error": str(e)}
        )


# ==================== STATISTICS ====================

@router.get("/stats")
async def get_email_stats(current_user: User = Depends(get_current_user)):
    """
    Получить статистику email аккаунта

    Требуется аутентификация пользователя.
    """
    try:
        stats = await email_service.get_email_stats()
        return stats

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении статистики: {str(e)}"
        )
