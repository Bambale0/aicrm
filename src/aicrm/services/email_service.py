"""
Сервис для отправки email сообщений
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import asyncio
from typing import List, Optional, Dict, Any
from pathlib import Path
import logging
from dataclasses import dataclass

from ..core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class EmailAttachment:
    """Вложение для email"""
    filename: str
    content: bytes
    content_type: str = "application/octet-stream"


@dataclass
class EmailMessage:
    """Email сообщение"""
    to: str | List[str]
    subject: str
    body: str
    from_email: Optional[str] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    attachments: Optional[List[EmailAttachment]] = None
    html_body: Optional[str] = None
    reply_to: Optional[str] = None


class EmailService:
    """Сервис для отправки email через SMTP"""

    def __init__(self):
        self.smtp_server = settings.smtp_server or "smtp.gmail.com"
        self.smtp_port = settings.smtp_port or 587
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.from_email = settings.from_email or self.smtp_username
        self.use_tls = settings.smtp_use_tls if hasattr(settings, 'smtp_use_tls') else True
        self.use_ssl = settings.smtp_use_ssl if hasattr(settings, 'smtp_use_ssl') else False

    async def send_email(self, message: EmailMessage) -> bool:
        """
        Отправка email сообщения

        Args:
            message: EmailMessage объект с данными письма

        Returns:
            bool: True если отправка успешна
        """
        try:
            # Создаем сообщение
            msg = MIMEMultipart('alternative')
            msg['Subject'] = message.subject
            msg['From'] = message.from_email or self.from_email

            # Получатели
            if isinstance(message.to, str):
                msg['To'] = message.to
                to_list = [message.to]
            else:
                msg['To'] = ', '.join(message.to)
                to_list = message.to

            if message.cc:
                msg['Cc'] = ', '.join(message.cc)
                to_list.extend(message.cc)

            if message.bcc:
                to_list.extend(message.bcc)

            if message.reply_to:
                msg['Reply-To'] = message.reply_to

            # Добавляем текстовую версию
            if message.body:
                text_part = MIMEText(message.body, 'plain', 'utf-8')
                msg.attach(text_part)

            # Добавляем HTML версию
            if message.html_body:
                html_part = MIMEText(message.html_body, 'html', 'utf-8')
                msg.attach(html_part)

            # Добавляем вложения
            if message.attachments:
                for attachment in message.attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.content)
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename="{attachment.filename}"'
                    )
                    part.add_header('Content-Type', attachment.content_type)
                    msg.attach(part)

            # Отправляем в отдельном потоке (SMTP - синхронный)
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                None,
                self._send_smtp,
                msg,
                to_list
            )

            if success:
                logger.info(f"Email отправлен успешно: {message.subject} -> {to_list}")
            else:
                logger.error(f"Не удалось отправить email: {message.subject}")

            return success

        except Exception as e:
            logger.error(f"Ошибка при отправке email: {e}")
            return False

    def _send_smtp(self, msg: MIMEMultipart, to_list: List[str]) -> bool:
        """
        Синхронная отправка через SMTP

        Args:
            msg: Подготовленное MIME сообщение
            to_list: Список получателей

        Returns:
            bool: True если отправка успешна
        """
        try:
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)

            if self.use_tls and not self.use_ssl:
                server.starttls()

            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)

            server.sendmail(
                self.from_email,
                to_list,
                msg.as_string()
            )

            server.quit()
            return True

        except Exception as e:
            logger.error(f"SMTP ошибка: {e}")
            return False

    async def send_template_email(
        self,
        template_name: str,
        to: str | List[str],
        template_data: Dict[str, Any],
        subject: str,
        attachments: Optional[List[EmailAttachment]] = None
    ) -> bool:
        """
        Отправка email с использованием шаблона

        Args:
            template_name: Имя шаблона
            to: Получатель(и)
            template_data: Данные для подстановки в шаблон
            subject: Тема письма
            attachments: Вложения

        Returns:
            bool: True если отправка успешна
        """
        try:
            # Получаем шаблон (пока что простая замена)
            html_body, text_body = self._render_template(template_name, template_data)

            message = EmailMessage(
                to=to,
                subject=subject,
                body=text_body,
                html_body=html_body,
                attachments=attachments
            )

            return await self.send_email(message)

        except Exception as e:
            logger.error(f"Ошибка при отправке шаблонного email: {e}")
            return False

    def _render_template(self, template_name: str, data: Dict[str, Any]) -> tuple[str, str]:
        """
        Рендеринг шаблона (простая реализация)

        Args:
            template_name: Имя шаблона
            data: Данные для подстановки

        Returns:
            tuple: (html_body, text_body)
        """
        # Простые шаблоны для демонстрации
        templates = {
            "order_confirmation": {
                "html": """
                <html>
                <body>
                    <h2>Заказ №{order_id} подтвержден!</h2>
                    <p>Уважаемый {customer_name},</p>
                    <p>Ваш заказ успешно оформлен и передан в производство.</p>
                    <p><strong>Детали заказа:</strong></p>
                    <ul>
                        <li>Заказ №: {order_id}</li>
                        <li>Сумма: {total_amount} руб.</li>
                        <li>Срок выполнения: {deadline}</li>
                    </ul>
                    <p>Статус заказа можно отслеживать в личном кабинете.</p>
                    <br>
                    <p>С уважением,<br>Команда AI CRM</p>
                </body>
                </html>
                """,
                "text": """
                Заказ №{order_id} подтвержден!

                Уважаемый {customer_name},

                Ваш заказ успешно оформлен и передан в производство.

                Детали заказа:
                - Заказ №: {order_id}
                - Сумма: {total_amount} руб.
                - Срок выполнения: {deadline}

                Статус заказа можно отслеживать в личном кабинете.

                С уважением,
                Команда AI CRM
                """
            },
            "task_assigned": {
                "html": """
                <html>
                <body>
                    <h2>Вам назначена новая задача</h2>
                    <p>Уважаемый {assignee_name},</p>
                    <p>Вам назначена новая задача в системе.</p>
                    <p><strong>Детали задачи:</strong></p>
                    <ul>
                        <li>Название: {task_title}</li>
                        <li>Описание: {task_description}</li>
                        <li>Приоритет: {priority}</li>
                        <li>Срок: {deadline}</li>
                    </ul>
                    <br>
                    <p>С уважением,<br>Команда AI CRM</p>
                </body>
                </html>
                """,
                "text": """
                Вам назначена новая задача

                Уважаемый {assignee_name},

                Вам назначена новая задача в системе.

                Детали задачи:
                - Название: {task_title}
                - Описание: {task_description}
                - Приоритет: {priority}
                - Срок: {deadline}

                С уважением,
                Команда AI CRM
                """
            }
        }

        template = templates.get(template_name, {
            "html": "<html><body><h2>{subject}</h2><p>{body}</p></body></html>",
            "text": "{subject}\n\n{body}"
        })

        html_body = template["html"].format(**data)
        text_body = template["text"].format(**data)

        return html_body, text_body

    async def send_order_confirmation(self, order_id: int, customer_email: str, customer_name: str) -> bool:
        """
        Отправка подтверждения заказа

        Args:
            order_id: ID заказа
            customer_email: Email клиента
            customer_name: Имя клиента

        Returns:
            bool: True если отправка успешна
        """
        template_data = {
            "order_id": order_id,
            "customer_name": customer_name,
            "total_amount": "TBD",  # В реальности нужно получить из БД
            "deadline": "TBD"  # В реальности нужно получить из БД
        }

        return await self.send_template_email(
            template_name="order_confirmation",
            to=customer_email,
            template_data=template_data,
            subject=f"Заказ №{order_id} подтвержден"
        )

    async def send_task_notification(self, task_id: int, assignee_email: str, assignee_name: str) -> bool:
        """
        Отправка уведомления о назначении задачи

        Args:
            task_id: ID задачи
            assignee_email: Email исполнителя
            assignee_name: Имя исполнителя

        Returns:
            bool: True если отправка успешна
        """
        template_data = {
            "task_id": task_id,
            "assignee_name": assignee_name,
            "task_title": "TBD",  # В реальности нужно получить из БД
            "task_description": "TBD",  # В реальности нужно получить из БД
            "priority": "TBD",  # В реальности нужно получить из БД
            "deadline": "TBD"  # В реальности нужно получить из БД
        }

        return await self.send_template_email(
            template_name="task_assigned",
            to=assignee_email,
            template_data=template_data,
            subject=f"Вам назначена задача №{task_id}"
        )


# Глобальный экземпляр сервиса
email_service = EmailService()
