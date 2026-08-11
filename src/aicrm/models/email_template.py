"""
Модель email шаблонов
"""

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text

from .base import BaseModel


class EmailTemplate(BaseModel):
    """Модель email шаблонов"""

    __tablename__ = "email_templates"

    name = Column(String(255), nullable=False, index=True, unique=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)

    # Шаблоны
    subject_template = Column(Text, nullable=False)
    html_template = Column(Text, nullable=False)
    text_template = Column(Text, nullable=False)

    # Переменные шаблона
    variables = Column(JSON, default=list)  # Список доступных переменных
    required_variables = Column(JSON, default=list)  # Обязательные переменные

    # Категории и метаданные
    category = Column(String(100), default="general", index=True)
    tags = Column(JSON, default=list)  # Теги для поиска

    # Настройки
    is_active = Column(Boolean, default=True, index=True)
    is_default = Column(
        Boolean, default=False, index=True
    )  # Шаблон по умолчанию для категории

    # Статистика использования
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime)

    # Системные поля
    created_by = Column(Integer, index=True)  # ID пользователя, создавшего шаблон
    updated_by = Column(Integer, index=True)  # ID пользователя, обновившего шаблон

    # Связи
    # creator = relationship("User", foreign_keys=[created_by], backref="created_email_templates")
    # updater = relationship("User", foreign_keys=[updated_by], backref="updated_email_templates")

    def __repr__(self) -> str:
        return f"<EmailTemplate(name='{self.name}', category='{self.category}', active={self.is_active})>"

    def to_dict(self) -> dict:
        """Преобразование в словарь для API"""
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "subject_template": self.subject_template,
            "html_template": self.html_template,
            "text_template": self.text_template,
            "variables": self.variables or [],
            "required_variables": self.required_variables or [],
            "category": self.category,
            "tags": self.tags or [],
            "is_active": self.is_active,
            "is_default": self.is_default,
            "usage_count": self.usage_count,
            "last_used_at": (
                self.last_used_at.isoformat() if self.last_used_at is not None else None
            ),
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def increment_usage(self):
        """Увеличение счетчика использования"""
        from datetime import datetime

        self.usage_count += 1
        self.last_used_at = datetime.utcnow()

    def validate_variables(self, provided_vars: dict) -> tuple[bool, list]:
        """
        Валидация предоставленных переменных

        Args:
            provided_vars: Предоставленные переменные

        Returns:
            tuple: (is_valid, missing_required_vars)
        """
        missing_required = []
        for var in self.required_variables or []:
            if var not in provided_vars:
                missing_required.append(var)

        return len(missing_required) == 0, missing_required

    def render_subject(self, variables: dict) -> str:
        """Рендеринг темы письма"""
        try:
            return self.subject_template.format(**variables)
        except KeyError as e:
            raise ValueError(f"Отсутствует обязательная переменная для темы: {e}")

    def render_html(self, variables: dict) -> str:
        """Рендеринг HTML тела"""
        try:
            return self.html_template.format(**variables)
        except KeyError as e:
            raise ValueError(f"Отсутствует обязательная переменная для HTML: {e}")

    def render_text(self, variables: dict) -> str:
        """Рендеринг текстового тела"""
        try:
            return self.text_template.format(**variables)
        except KeyError as e:
            raise ValueError(f"Отсутствует обязательная переменная для текста: {e}")

    @classmethod
    def get_default_templates(cls) -> list[dict]:
        """Получение списка стандартных шаблонов"""
        return [
            {
                "name": "order_confirmation",
                "display_name": "Подтверждение заказа",
                "description": "Шаблон для подтверждения оформления заказа",
                "subject_template": "Заказ №{order_id} подтвержден",
                "html_template": """
                <!DOCTYPE html>
                <html lang="ru">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Подтверждение заказа</title>
                    <style>
                        body { fontFamily: Arial, sans-serif; line-height: 1.6; color: #333; }
                        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
                        .order-details { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #667eea; }
                        .button { display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
                        .footer { text-align: center; color: #666; font-size: 12px; margin-top: 30px; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>🎉 Заказ подтвержден!</h1>
                            <p>Спасибо за ваш выбор</p>
                        </div>
                        <div class="content">
                            <p>Уважаемый(ая) <strong>{customer_name}</strong>,</p>

                            <p>Ваш заказ успешно оформлен и принят в работу! Мы рады сообщить, что все необходимые приготовления уже начаты.</p>

                            <div class="order-details">
                                <h3>📋 Детали заказа</h3>
                                <ul>
                                    <li><strong>Номер заказа:</strong> #{order_id}</li>
                                    <li><strong>Дата оформления:</strong> {order_date}</li>
                                    <li><strong>Общая сумма:</strong> {total_amount} ₽</li>
                                    <li><strong>Срок выполнения:</strong> {deadline}</li>
                                    <li><strong>Статус:</strong> <span style="color: #28a745;">Принят в работу</span></li>
                                </ul>
                            </div>

                            <p>Вы можете отслеживать статус вашего заказа в <a href="{tracking_url}">личном кабинете</a> или связаться с нами по телефону {support_phone}.</p>

                            <div style="text-align: center;">
                                <a href="{tracking_url}" class="button">📊 Отследить заказ</a>
                            </div>

                            <p>Если у вас возникнут вопросы, наша команда поддержки всегда готова помочь!</p>

                            <div class="footer">
                                <p>С уважением,<br><strong>Команда AI CRM</strong></p>
                                <p>📧 support@aicrm.com | 📞 {support_phone}</p>
                            </div>
                        </div>
                    </div>
                </body>
                </html>
                """,
                "text_template": """
                🎉 ЗАКАЗ ПОДТВЕРЖДЕН!

                Уважаемый(ая) {customer_name},

                Ваш заказ успешно оформлен и принят в работу!

                📋 ДЕТАЛИ ЗАКАЗА:
                • Номер заказа: #{order_id}
                • Дата оформления: {order_date}
                • Общая сумма: {total_amount} ₽
                • Срок выполнения: {deadline}
                • Статус: Принят в работу

                Вы можете отслеживать статус заказа в личном кабинете: {tracking_url}

                Если у вас возникнут вопросы, свяжитесь с нами:
                📞 {support_phone}
                📧 support@aicrm.com

                С уважением,
                Команда AI CRM
                """,
                "variables": [
                    "order_id",
                    "customer_name",
                    "order_date",
                    "total_amount",
                    "deadline",
                    "tracking_url",
                    "support_phone",
                ],
                "required_variables": [
                    "order_id",
                    "customer_name",
                    "total_amount",
                    "deadline",
                ],
                "category": "orders",
                "tags": ["заказ", "подтверждение", "клиент"],
                "is_default": True,
            },
            {
                "name": "task_assigned",
                "display_name": "Уведомление о назначении задачи",
                "description": "Шаблон для уведомления сотрудника о новой задаче",
                "subject_template": "Новая задача: {task_title}",
                "html_template": """
                <!DOCTYPE html>
                <html lang="ru">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Новая задача</title>
                    <style>
                        body { fontFamily: Arial, sans-serif; line-height: 1.6; color: #333; }
                        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                        .header { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
                        .task-details { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #f5576c; }
                        .priority-high { color: #dc3545; font-weight: bold; }
                        .priority-medium { color: #ffc107; font-weight: bold; }
                        .priority-low { color: #28a745; font-weight: bold; }
                        .button { display: inline-block; background: #f5576c; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
                        .footer { text-align: center; color: #666; font-size: 12px; margin-top: 30px; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>📋 Новая задача</h1>
                            <p>Вам назначено новое задание</p>
                        </div>
                        <div class="content">
                            <p>Здравствуйте, <strong>{assignee_name}</strong>!</p>

                            <p>Вам назначена новая задача в системе управления проектами.</p>

                            <div class="task-details">
                                <h3>📝 Детали задачи</h3>
                                <table style="width: 100%; border-collapse: collapse;">
                                    <tr>
                                        <td style="padding: 8px 0; font-weight: bold; width: 120px;">Название:</td>
                                        <td style="padding: 8px 0;">{task_title}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0; font-weight: bold;">Приоритет:</td>
                                        <td style="padding: 8px 0;">
                                            <span class="priority-{priority}">{priority_display}</span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0; font-weight: bold;">Срок выполнения:</td>
                                        <td style="padding: 8px 0;">{deadline}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0; font-weight: bold;">Назначил:</td>
                                        <td style="padding: 8px 0;">{assigner_name}</td>
                                    </tr>
                                </table>

                                <h4>Описание:</h4>
                                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px;">
                                    {task_description}
                                </div>
                            </div>

                            <p>Пожалуйста, ознакомьтесь с задачей и приступите к ее выполнению в установленные сроки.</p>

                            <div style="text-align: center;">
                                <a href="{task_url}" class="button">🔗 Перейти к задаче</a>
                            </div>

                            <p>Если у вас возникнут вопросы по задаче, обратитесь к {assigner_name} или в службу поддержки.</p>

                            <div class="footer">
                                <p>С уважением,<br><strong>Система управления задачами AI CRM</strong></p>
                                <p>📧 support@aicrm.com | 📞 {support_phone}</p>
                            </div>
                        </div>
                    </div>
                </body>
                </html>
                """,
                "text_template": """
                📋 НОВАЯ ЗАДАЧА

                Здравствуйте, {assignee_name}!

                Вам назначена новая задача в системе управления проектами.

                📝 ДЕТАЛИ ЗАДАЧИ:
                • Название: {task_title}
                • Приоритет: {priority_display}
                • Срок выполнения: {deadline}
                • Назначил: {assigner_name}

                ОПИСАНИЕ:
                {task_description}

                Перейти к задаче: {task_url}

                Если у вас возникнут вопросы, обратитесь к {assigner_name} или в службу поддержки.

                С уважением,
                Система управления задачами AI CRM
                📧 support@aicrm.com | 📞 {support_phone}
                """,
                "variables": [
                    "task_id",
                    "task_title",
                    "task_description",
                    "assignee_name",
                    "assigner_name",
                    "priority",
                    "priority_display",
                    "deadline",
                    "task_url",
                    "support_phone",
                ],
                "required_variables": [
                    "task_title",
                    "assignee_name",
                    "task_description",
                ],
                "category": "tasks",
                "tags": ["задача", "назначение", "сотрудник"],
                "is_default": True,
            },
            {
                "name": "payment_reminder",
                "display_name": "Напоминание об оплате",
                "description": "Шаблон для напоминания о необходимости оплаты",
                "subject_template": "Напоминание об оплате заказа №{order_id}",
                "html_template": """
                <!DOCTYPE html>
                <html lang="ru">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Напоминание об оплате</title>
                    <style>
                        body { fontFamily: Arial, sans-serif; line-height: 1.6; color: #333; }
                        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                        .header { background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
                        .payment-details { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ff9a9e; }
                        .amount { font-size: 24px; font-weight: bold; color: #ff9a9e; text-align: center; margin: 20px 0; }
                        .button { display: inline-block; background: #ff9a9e; color: white; padding: 15px 40px; text-decoration: none; border-radius: 5px; margin: 20px 0; font-weight: bold; }
                        .warning { background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 15px; border-radius: 5px; margin: 20px 0; }
                        .footer { text-align: center; color: #666; font-size: 12px; margin-top: 30px; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>💳 Напоминание об оплате</h1>
                            <p>Ваш заказ ожидает оплаты</p>
                        </div>
                        <div class="content">
                            <p>Уважаемый(ая) <strong>{customer_name}</strong>,</p>

                            <p>Напоминаем, что ваш заказ №{order_id} ожидает оплаты. Для продолжения работы над заказом необходимо завершить платеж.</p>

                            <div class="payment-details">
                                <h3>💰 Детали оплаты</h3>
                                <div class="amount">{total_amount} ₽</div>
                                <ul>
                                    <li><strong>Заказ:</strong> #{order_id}</li>
                                    <li><strong>Срок оплаты:</strong> {payment_deadline}</li>
                                    <li><strong>Способ оплаты:</strong> {payment_methods}</li>
                                </ul>
                            </div>

                            <div class="warning">
                                ⚠️ <strong>Важно!</strong> Если оплата не будет произведена до {payment_deadline}, заказ может быть отменен автоматически.
                            </div>

                            <div style="text-align: center;">
                                <a href="{payment_url}" class="button">💳 Оплатить сейчас</a>
                            </div>

                            <p>После успешной оплаты вы получите подтверждение и сможете отслеживать статус выполнения заказа.</p>

                            <p>Если у вас возникли проблемы с оплатой или вопросы по заказу, пожалуйста, свяжитесь с нами.</p>

                            <div class="footer">
                                <p>С уважением,<br><strong>Команда AI CRM</strong></p>
                                <p>📧 support@aicrm.com | 📞 {support_phone}</p>
                            </div>
                        </div>
                    </div>
                </body>
                </html>
                """,
                "text_template": """
                💳 НАПОМИНАНИЕ ОБ ОПЛАТЕ

                Уважаемый(ая) {customer_name},

                Напоминаем, что ваш заказ №{order_id} ожидает оплаты.

                💰 ДЕТАЛИ ОПЛАТЫ:
                Сумма: {total_amount} ₽
                • Заказ: #{order_id}
                • Срок оплаты: {payment_deadline}
                • Способ оплаты: {payment_methods}

                ⚠️ ВАЖНО: Если оплата не будет произведена до {payment_deadline}, заказ может быть отменен.

                Оплатить: {payment_url}

                После оплаты вы получите подтверждение и сможете отслеживать статус заказа.

                Если возникли проблемы, свяжитесь с нами:
                📞 {support_phone}
                📧 support@aicrm.com

                С уважением,
                Команда AI CRM
                """,
                "variables": [
                    "order_id",
                    "customer_name",
                    "total_amount",
                    "payment_deadline",
                    "payment_methods",
                    "payment_url",
                    "support_phone",
                ],
                "required_variables": [
                    "order_id",
                    "customer_name",
                    "total_amount",
                    "payment_deadline",
                ],
                "category": "payments",
                "tags": ["оплата", "напоминание", "заказ"],
                "is_default": True,
            },
            {
                "name": "welcome_new_customer",
                "display_name": "Приветствие нового клиента",
                "description": "Шаблон приветственного письма для новых клиентов",
                "subject_template": "Добро пожаловать в AI CRM, {customer_name}!",
                "html_template": """
                <!DOCTYPE html>
                <html lang="ru">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Добро пожаловать</title>
                    <style>
                        body { fontFamily: Arial, sans-serif; line-height: 1.6; color: #333; }
                        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                        .header { background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
                        .welcome-message { background: white; padding: 25px; border-radius: 8px; margin: 20px 0; text-align: center; }
                        .features { display: flex; flex-wrap: wrap; gap: 20px; margin: 30px 0; }
                        .feature { flex: 1; min-width: 200px; background: white; padding: 20px; border-radius: 8px; text-align: center; }
                        .button { display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
                        .footer { text-align: center; color: #666; font-size: 12px; margin-top: 30px; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>🎊 Добро пожаловать!</h1>
                            <p>Рады приветствовать вас в AI CRM</p>
                        </div>
                        <div class="content">
                            <div class="welcome-message">
                                <h2>Здравствуйте, {customer_name}!</h2>
                                <p>Спасибо, что выбрали наши услуги. Мы рады приветствовать вас в сообществе довольных клиентов AI CRM!</p>
                            </div>

                            <p>Теперь у вас есть доступ к мощным инструментам управления бизнес-процессами:</p>

                            <div class="features">
                                <div class="feature">
                                    <h3>🤖 AI Автоматизация</h3>
                                    <p>Умные роботы берут на себя рутинные задачи</p>
                                </div>
                                <div class="feature">
                                    <h3>📊 Аналитика</h3>
                                    <p>Подробные отчеты и insights для роста бизнеса</p>
                                </div>
                                <div class="feature">
                                    <h3>💬 Коммуникации</h3>
                                    <p>Интегрированные чаты и уведомления</p>
                                </div>
                            </div>

                            <p>Для начала работы рекомендуем ознакомиться с <a href="{getting_started_url}">руководством по началу работы</a> или связаться с персональным менеджером.</p>

                            <div style="text-align: center;">
                                <a href="{dashboard_url}" class="button">🚀 Начать работу</a>
                            </div>

                            <p>Если у вас возникнут вопросы, наша команда поддержки всегда готова помочь!</p>

                            <div class="footer">
                                <p>С уважением,<br><strong>Команда AI CRM</strong></p>
                                <p>📧 support@aicrm.com | 📞 {support_phone}</p>
                            </div>
                        </div>
                    </div>
                </body>
                </html>
                """,
                "text_template": """
                🎊 ДОБРО ПОЖАЛОВАТЬ В AI CRM!

                Здравствуйте, {customer_name}!

                Спасибо, что выбрали наши услуги. Мы рады приветствовать вас в сообществе довольных клиентов AI CRM!

                Теперь у вас есть доступ к мощным инструментам:

                🤖 AI АВТОМАТИЗАЦИЯ
                Умные роботы берут на себя рутинные задачи

                📊 АНАЛИТИКА
                Подробные отчеты и insights для роста бизнеса

                💬 КОММУНИКАЦИИ
                Интегрированные чаты и уведомления

                Для начала работы ознакомьтесь с руководством: {getting_started_url}

                Начать работу: {dashboard_url}

                Если возникнут вопросы, свяжитесь с нами:
                📞 {support_phone}
                📧 support@aicrm.com

                С уважением,
                Команда AI CRM
                """,
                "variables": [
                    "customer_name",
                    "getting_started_url",
                    "dashboard_url",
                    "support_phone",
                ],
                "required_variables": ["customer_name"],
                "category": "welcome",
                "tags": ["приветствие", "новый клиент", "регистрация"],
                "is_default": True,
            },
        ]
