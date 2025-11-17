"""
Полноценный email сервис с поддержкой отправки и получения сообщений
"""
import smtplib
import imaplib
import poplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.application import MIMEApplication
from email import encoders, policy, utils
from email.utils import parseaddr, formataddr, make_msgid
from email.header import decode_header
import asyncio
from typing import List, Optional, Dict, Any, Tuple, Union
from pathlib import Path
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import re
import base64
import quopri
import mimetypes

from ..core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class EmailAttachment:
    """Вложение для email"""
    filename: str
    content: bytes
    content_type: str = "application/octet-stream"
    size: int = 0


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


@dataclass
class ReceivedEmailMessage:
    """Полученное email сообщение"""
    id: str
    uid: str
    subject: str
    from_addr: str
    from_name: str
    to: List[str]
    date: datetime
    body_text: str
    cc: List[str] = field(default_factory=list)
    bcc: List[str] = field(default_factory=list)
    body_html: Optional[str] = None
    attachments: List[EmailAttachment] = field(default_factory=list)
    flags: List[str] = field(default_factory=list)
    size: int = 0
    message_id: Optional[str] = None
    in_reply_to: Optional[str] = None
    references: List[str] = field(default_factory=list)
    folder: str = "INBOX"
    is_read: bool = False
    is_flagged: bool = False
    is_deleted: bool = False


@dataclass
class EmailFolder:
    """Email папка"""
    name: str
    flags: List[str] = field(default_factory=list)
    delimiter: str = "/"
    total_messages: int = 0
    recent_messages: int = 0
    unseen_messages: int = 0


@dataclass
class EmailContact:
    """Email контакт"""
    email: str
    name: str
    frequency: int = 0
    last_contact: Optional[datetime] = None
    is_blocked: bool = False


@dataclass
class EmailTemplate:
    """Email шаблон"""
    name: str
    subject_template: str
    html_template: str
    text_template: str
    variables: List[str] = field(default_factory=list)
    category: str = "general"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class EmailService:
    """Полноценный email сервис с поддержкой SMTP, IMAP и POP3"""

    def __init__(self):
        # SMTP настройки
        self.smtp_server = settings.smtp_server or "smtp.gmail.com"
        self.smtp_port = settings.smtp_port or 587
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.from_email = settings.from_email or self.smtp_username
        self.use_tls = getattr(settings, 'smtp_use_tls', True)
        self.use_ssl = getattr(settings, 'smtp_use_ssl', False)

        # IMAP настройки
        self.imap_server = getattr(settings, 'imap_server', "imap.gmail.com")
        self.imap_port = getattr(settings, 'imap_port', 993)
        self.imap_use_ssl = getattr(settings, 'imap_use_ssl', True)

        # POP3 настройки
        self.pop3_server = getattr(settings, 'pop3_server', "pop.gmail.com")
        self.pop3_port = getattr(settings, 'pop3_port', 995)
        self.pop3_use_ssl = getattr(settings, 'pop3_use_ssl', True)

        # Хранилище контактов и шаблонов
        self.contacts: Dict[str, EmailContact] = {}
        self.templates: Dict[str, EmailTemplate] = {}
        self._load_default_templates()

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
                server.login(self.smtp_username or "", self.smtp_password or "")

            server.sendmail(
                self.from_email or self.smtp_username or "",
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

    def _load_default_templates(self):
        """Загрузка стандартных шаблонов"""
        self.templates = {
            "order_confirmation": EmailTemplate(
                name="Подтверждение заказа",
                subject_template="Заказ №{order_id} подтвержден",
                html_template="""
                <html><body>
                    <h2>Заказ №{order_id} подтвержден!</h2>
                    <p>Уважаемый {customer_name},</p>
                    <p>Ваш заказ успешно оформлен.</p>
                    <p>С уважением,<br>AI CRM</p>
                </body></html>
                """,
                text_template="Заказ №{order_id} подтвержден! Уважаемый {customer_name}, Ваш заказ успешно оформлен.",
                variables=["order_id", "customer_name", "total_amount", "deadline"],
                category="orders"
            ),
            "task_assigned": EmailTemplate(
                name="Уведомление о задаче",
                subject_template="Вам назначена задача №{task_id}",
                html_template="""
                <html><body>
                    <h2>Новая задача</h2>
                    <p>Уважаемый {assignee_name},</p>
                    <p>Вам назначена задача: {task_title}</p>
                    <p>С уважением,<br>AI CRM</p>
                </body></html>
                """,
                text_template="Уважаемый {assignee_name}, Вам назначена задача: {task_title}",
                variables=["task_id", "assignee_name", "task_title", "task_description", "priority", "deadline"],
                category="tasks"
            )
        }

    # ==================== IMAP METHODS ====================

    async def get_folders(self) -> List[EmailFolder]:
        """
        Получение списка папок через IMAP

        Returns:
            List[EmailFolder]: Список папок
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._get_folders_imap)

    def _get_folders_imap(self) -> List[EmailFolder]:
        """Синхронное получение папок через IMAP"""
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            if self.smtp_username and self.smtp_password:
                mail.login(self.smtp_username, self.smtp_password)
            else:
                raise ValueError("SMTP credentials not configured")

            status, folders_data = mail.list()
            if status != 'OK':
                return []

            folders = []
            for folder_data in folders_data:
                if isinstance(folder_data, bytes):
                    folder_str = folder_data.decode('utf-8')
                    # Парсим формат: (\HasNoChildren) "/" "INBOX"
                    match = re.match(r'\((.*?)\) "(.*?)" "(.*?)"', folder_str)
                    if match:
                        flags_str, delimiter, name = match.groups()
                        flags = flags_str.split() if flags_str else []

                        # Получаем статистику папки
                        mail.select(name, readonly=True)
                        status, data = mail.status(name, '(MESSAGES RECENT UNSEEN)')
                        total = recent = unseen = 0

                        if status == 'OK' and data:
                            status_str = data[0].decode('utf-8')
                            total_match = re.search(r'MESSAGES (\d+)', status_str)
                            recent_match = re.search(r'RECENT (\d+)', status_str)
                            unseen_match = re.search(r'UNSEEN (\d+)', status_str)

                            total = int(total_match.group(1)) if total_match else 0
                            recent = int(recent_match.group(1)) if recent_match else 0
                            unseen = int(unseen_match.group(1)) if unseen_match else 0

                        folders.append(EmailFolder(
                            name=name,
                            flags=flags,
                            delimiter=delimiter,
                            total_messages=total,
                            recent_messages=recent,
                            unseen_messages=unseen
                        ))

            mail.logout()
            return folders

        except Exception as e:
            logger.error(f"Ошибка при получении папок IMAP: {e}")
            return []

    async def get_emails(
        self,
        folder: str = "INBOX",
        limit: int = 50,
        offset: int = 0,
        search_criteria: Optional[str] = None
    ) -> List[ReceivedEmailMessage]:
        """
        Получение email сообщений из папки

        Args:
            folder: Имя папки
            limit: Максимальное количество сообщений
            offset: Смещение
            search_criteria: Критерии поиска IMAP

        Returns:
            List[ReceivedEmailMessage]: Список сообщений
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._get_emails_imap,
            folder,
            limit,
            offset,
            search_criteria
        )

    def _get_emails_imap(
        self,
        folder: str,
        limit: int,
        offset: int,
        search_criteria: Optional[str]
    ) -> List[ReceivedEmailMessage]:
        """Синхронное получение email через IMAP"""
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            if self.smtp_username and self.smtp_password:
                mail.login(self.smtp_username, self.smtp_password)
            else:
                raise ValueError("SMTP credentials not configured")
            mail.select(folder, readonly=True)

            # Формируем критерии поиска
            if not search_criteria:
                search_criteria = "ALL"

            status, message_ids = mail.search(None, search_criteria)
            if status != 'OK':
                return []

            ids = message_ids[0].split()
            if not ids:
                return []

            # Применяем offset и limit
            ids_list = ids if isinstance(ids, list) else [ids]
            total_ids = len(ids_list)
            start_idx = max(0, total_ids - offset - limit)
            end_idx = max(0, total_ids - offset)
            ids_to_fetch = ids_list[start_idx:end_idx]

            if not ids_to_fetch:
                return []

            messages = []
            for msg_id in ids_to_fetch:
                try:
                    status, msg_data = mail.fetch(msg_id, '(RFC822 FLAGS)')
                    if status != 'OK':
                        continue

                    email_message = self._parse_email_message(msg_data[0], msg_id.decode('utf-8'), folder)
                    if email_message:
                        messages.append(email_message)

                except Exception as e:
                    logger.error(f"Ошибка при разборе сообщения {msg_id}: {e}")
                    continue

            mail.logout()
            return messages

        except Exception as e:
            logger.error(f"Ошибка при получении email через IMAP: {e}")
            return []

    def _parse_email_message(self, raw_data: bytes, msg_id: str, folder: str) -> Optional[ReceivedEmailMessage]:
        """Парсинг сырого email сообщения"""
        try:
            # Разбираем данные IMAP
            envelope_data = raw_data[1] if len(raw_data) > 1 else raw_data[0]
            if isinstance(envelope_data, tuple):
                flags_part, rfc822_part = envelope_data
                flags = self._parse_flags(flags_part)
                raw_email = rfc822_part if isinstance(rfc822_part, bytes) else b""
            else:
                flags = []
                raw_email = envelope_data if isinstance(envelope_data, bytes) else b""

            # Парсим email
            msg = email.message_from_bytes(raw_email, policy=policy.default)

            # Извлекаем заголовки
            subject = self._decode_header(msg.get('Subject', ''))
            from_header = msg.get('From', '')
            from_name, from_addr = parseaddr(from_header)

            to_header = msg.get('To', '')
            to_list = [addr.strip() for addr in to_header.split(',') if addr.strip()]

            cc_header = msg.get('Cc', '')
            cc_list = [addr.strip() for addr in cc_header.split(',') if addr.strip()]

            # Дата
            date_str = msg.get('Date', '')
            try:
                if date_str:
                    date_tuple = utils.parsedate(date_str)
                    if date_tuple:
                        date = datetime(*date_tuple[:6])
                    else:
                        date = datetime.now()
                else:
                    date = datetime.now()
            except:
                date = datetime.now()

            # Message-ID и ссылки
            message_id = msg.get('Message-ID')
            in_reply_to = msg.get('In-Reply-To')
            references = msg.get('References', '').split() if msg.get('References') else []

            # Извлекаем тело и вложения
            body_text, body_html, attachments = self._extract_body_and_attachments(msg)

            # Определяем флаги
            is_read = '\\Seen' in flags
            is_flagged = '\\Flagged' in flags
            is_deleted = '\\Deleted' in flags

            return ReceivedEmailMessage(
                id=msg_id,
                uid=msg_id,  # В упрощенной версии UID = ID
                subject=subject,
                from_addr=from_addr,
                from_name=from_name,
                to=to_list,
                cc=cc_list,
                date=date,
                body_text=body_text,
                body_html=body_html,
                attachments=attachments,
                flags=flags,
                size=len(raw_email),
                message_id=message_id,
                in_reply_to=in_reply_to,
                references=references,
                folder=folder,
                is_read=is_read,
                is_flagged=is_flagged,
                is_deleted=is_deleted
            )

        except Exception as e:
            logger.error(f"Ошибка при парсинге email: {e}")
            return None

    def _parse_flags(self, flags_data: bytes) -> List[str]:
        """Парсинг флагов IMAP"""
        try:
            flags_str = flags_data.decode('utf-8')
            # Ищем FLAGS (....)
            match = re.search(r'FLAGS \((.*?)\)', flags_str)
            if match:
                flags = match.group(1).split()
                return [f.strip('\\') for f in flags]
            return []
        except:
            return []

    def _decode_header(self, header: str) -> str:
        """Декодирование email заголовка"""
        try:
            decoded_parts = decode_header(header)
            result = ""
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        result += part.decode(encoding)
                    else:
                        result += part.decode('utf-8', errors='ignore')
                else:
                    result += str(part)
            return result
        except:
            return header

    def _extract_body_and_attachments(self, msg) -> Tuple[str, Optional[str], List[EmailAttachment]]:
        """Извлечение тела сообщения и вложений"""
        body_text = ""
        body_html = None
        attachments = []

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition', ''))

                # Пропускаем multipart контейнеры
                if content_type.startswith('multipart/'):
                    continue

                # Вложения
                if 'attachment' in content_disposition or part.get_filename():
                    filename = part.get_filename()
                    if filename:
                        filename = self._decode_header(filename)
                        content = part.get_payload(decode=True)
                        if content:
                            attachments.append(EmailAttachment(
                                filename=filename,
                                content=content,
                                content_type=content_type,
                                size=len(content)
                            ))
                    continue

                # Текстовые части
                if content_type == 'text/plain':
                    charset = part.get_content_charset() or 'utf-8'
                    try:
                        text_content = part.get_payload(decode=True).decode(charset)
                        if not body_text:  # Берем первую текстовую часть
                            body_text = text_content
                    except:
                        pass

                elif content_type == 'text/html':
                    charset = part.get_content_charset() or 'utf-8'
                    try:
                        html_content = part.get_payload(decode=True).decode(charset)
                        if not body_html:  # Берем первую HTML часть
                            body_html = html_content
                    except:
                        pass
        else:
            # Простое сообщение
            content_type = msg.get_content_type()
            charset = msg.get_content_charset() or 'utf-8'

            try:
                content = msg.get_payload(decode=True).decode(charset)
                if content_type == 'text/html':
                    body_html = content
                    # Извлекаем текст из HTML
                    import re
                    body_text = re.sub(r'<[^>]+>', '', content).strip()
                else:
                    body_text = content
            except:
                body_text = "Не удалось декодировать содержимое"

        return body_text, body_html, attachments

    async def mark_as_read(self, message_ids: List[str], folder: str = "INBOX") -> bool:
        """Отметить сообщения как прочитанные"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._mark_messages_imap, message_ids, folder, '+FLAGS', '\\Seen')

    async def mark_as_unread(self, message_ids: List[str], folder: str = "INBOX") -> bool:
        """Отметить сообщения как непрочитанные"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._mark_messages_imap, message_ids, folder, '-FLAGS', '\\Seen')

    async def flag_messages(self, message_ids: List[str], folder: str = "INBOX") -> bool:
        """Пометить сообщения флагом"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._mark_messages_imap, message_ids, folder, '+FLAGS', '\\Flagged')

    async def unflag_messages(self, message_ids: List[str], folder: str = "INBOX") -> bool:
        """Снять флаг с сообщений"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._mark_messages_imap, message_ids, folder, '-FLAGS', '\\Flagged')

    async def delete_messages(self, message_ids: List[str], folder: str = "INBOX") -> bool:
        """Удалить сообщения"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._mark_messages_imap, message_ids, folder, '+FLAGS', '\\Deleted')

    def _mark_messages_imap(self, message_ids: List[str], folder: str, action: str, flag: str) -> bool:
        """Установка флагов сообщений через IMAP"""
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            if self.smtp_username and self.smtp_password:
                mail.login(self.smtp_username, self.smtp_password)
            else:
                raise ValueError("SMTP credentials not configured")
            mail.select(folder)

            for msg_id in message_ids:
                mail.store(msg_id, action, flag)

            mail.expunge()  # Применить изменения
            mail.logout()
            return True

        except Exception as e:
            logger.error(f"Ошибка при установке флагов: {e}")
            return False

    async def move_messages(self, message_ids: List[str], from_folder: str, to_folder: str) -> bool:
        """Переместить сообщения между папками"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._move_messages_imap, message_ids, from_folder, to_folder)

    def _move_messages_imap(self, message_ids: List[str], from_folder: str, to_folder: str) -> bool:
        """Перемещение сообщений через IMAP"""
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            if self.smtp_username and self.smtp_password:
                mail.login(self.smtp_username, self.smtp_password)
            else:
                raise ValueError("SMTP credentials not configured")
            mail.select(from_folder)

            # IMAP MOVE command (если поддерживается) или COPY + DELETE
            try:
                # Пробуем MOVE
                for msg_id in message_ids:
                    mail.move(msg_id, to_folder)
            except:
                # Fallback: COPY + DELETE
                for msg_id in message_ids:
                    mail.copy(msg_id, to_folder)
                    mail.store(msg_id, '+FLAGS', '\\Deleted')

            mail.expunge()
            mail.logout()
            return True

        except Exception as e:
            logger.error(f"Ошибка при перемещении сообщений: {e}")
            return False

    # ==================== CONTACT MANAGEMENT ====================

    async def add_contact(self, email: str, name: str) -> bool:
        """Добавить контакт"""
        try:
            contact = EmailContact(
                email=email.lower(),
                name=name,
                last_contact=datetime.now()
            )
            self.contacts[email.lower()] = contact
            return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении контакта: {e}")
            return False

    async def get_contacts(self, search: Optional[str] = None) -> List[EmailContact]:
        """Получить список контактов"""
        contacts = list(self.contacts.values())

        if search:
            search_lower = search.lower()
            contacts = [
                c for c in contacts
                if search_lower in c.email.lower() or search_lower in c.name.lower()
            ]

        return sorted(contacts, key=lambda c: c.last_contact or datetime.min, reverse=True)

    async def update_contact_frequency(self, email: str) -> bool:
        """Обновить частоту использования контакта"""
        try:
            email_lower = email.lower()
            if email_lower in self.contacts:
                self.contacts[email_lower].frequency += 1
                self.contacts[email_lower].last_contact = datetime.now()
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка при обновлении контакта: {e}")
            return False

    # ==================== TEMPLATE MANAGEMENT ====================

    async def create_template(self, template: EmailTemplate) -> bool:
        """Создать новый шаблон"""
        try:
            self.templates[template.name] = template
            return True
        except Exception as e:
            logger.error(f"Ошибка при создании шаблона: {e}")
            return False

    async def get_templates(self, category: Optional[str] = None) -> List[EmailTemplate]:
        """Получить список шаблонов"""
        templates = list(self.templates.values())

        if category:
            templates = [t for t in templates if t.category == category]

        return sorted(templates, key=lambda t: t.updated_at, reverse=True)

    async def render_template(self, template_name: str, data: Dict[str, Any]) -> Tuple[str, str, str]:
        """Рендеринг шаблона с данными"""
        try:
            if template_name not in self.templates:
                raise ValueError(f"Шаблон {template_name} не найден")

            template = self.templates[template_name]

            # Простая подстановка переменных
            subject = template.subject_template.format(**data)
            html_body = template.html_template.format(**data)
            text_body = template.text_template.format(**data)

            return subject, html_body, text_body

        except Exception as e:
            logger.error(f"Ошибка при рендеринге шаблона: {e}")
            return "", "", ""

    # ==================== SEARCH AND FILTER ====================

    async def search_emails(
        self,
        query: str,
        folder: str = "INBOX",
        limit: int = 50
    ) -> List[ReceivedEmailMessage]:
        """Поиск email сообщений"""
        # Преобразуем запрос в IMAP критерии
        imap_criteria = self._build_search_criteria(query)

        return await self.get_emails(
            folder=folder,
            limit=limit,
            search_criteria=imap_criteria
        )

    def _build_search_criteria(self, query: str) -> str:
        """Преобразование текстового запроса в IMAP критерии"""
        # Простая реализация - можно расширить
        if not query:
            return "ALL"

        # Разбираем запрос на части
        parts = query.lower().split()

        criteria = []
        for part in parts:
            if '@' in part:
                # Email адрес
                criteria.append(f'FROM "{part}"')
            elif part in ['unread', 'прочитано']:
                criteria.append('UNSEEN')
            elif part in ['read', 'прочитанное']:
                criteria.append('SEEN')
            elif part in ['flagged', 'помеченное']:
                criteria.append('FLAGGED')
            else:
                # Текстовый поиск
                criteria.append(f'BODY "{part}"')

        if criteria:
            return ' '.join(criteria)
        return "ALL"

    # ==================== UTILITY METHODS ====================

    async def get_email_stats(self) -> Dict[str, Any]:
        """Получить статистику email аккаунта"""
        try:
            # Проверяем, настроен ли IMAP перед попыткой получения папок
            if not self.smtp_username or not self.smtp_password:
                logger.info("IMAP не настроен - возвращаем базовую статистику")
                return {
                    "total_messages": 0,
                    "unread_messages": 0,
                    "folders_count": 0,
                    "contacts_count": len(self.contacts),
                    "templates_count": len(self.templates)
                }

            folders = await self.get_folders()

            total_messages = sum(f.total_messages for f in folders)
            unread_messages = sum(f.unseen_messages for f in folders)

            return {
                "total_messages": total_messages,
                "unread_messages": unread_messages,
                "folders_count": len(folders),
                "contacts_count": len(self.contacts),
                "templates_count": len(self.templates)
            }

        except Exception as e:
            logger.error(f"Ошибка при получении статистики: {e}")
            return {
                "total_messages": 0,
                "unread_messages": 0,
                "folders_count": 0,
                "contacts_count": len(self.contacts),
                "templates_count": len(self.templates)
            }


# Глобальный экземпляр сервиса
email_service = EmailService()
