"""
Сервис анализа намерений и генерации ответов через AI
"""
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from ...core.config import settings
from ...utils.logging import get_logger
from ..session_service import session_service

logger = get_logger(__name__)


class IntentType:
    """Типы намерений клиентов"""
    CONSULTATION = "consultation"  # Консультация по услугам/ценам
    ORDER_REQUEST = "order_request"  # Запрос на заказ
    COMPLAINT = "complaint"  # Жалоба
    SUPPORT = "support"  # Техническая поддержка
    GENERAL = "general"  # Общий вопрос
    PRICE_INQUIRY = "price_inquiry"  # Запрос цены
    STATUS_CHECK = "status_check"  # Проверка статуса заказа
    MODIFICATION = "modification"  # Изменение заказа
    CANCELLATION = "cancellation"  # Отмена заказа


class AIIntentService:
    """Сервис для анализа намерений и генерации ответов"""

    def __init__(self):
        self.redis_url = settings.redis_url
        self.intent_patterns = self._load_intent_patterns()
        self.knowledge_base = self._load_knowledge_base()

    def _load_intent_patterns(self) -> Dict[str, List[str]]:
        """Загрузка паттернов для распознавания намерений"""
        return {
            IntentType.CONSULTATION: [
                r"сколько\s+стоит", r"цена\s+на", r"стоимость", r"тариф",
                r"как\s+заказать", r"как\s+сделать\s+заказ", r"условия",
                r"требования", r"размеры", r"форматы", r"материалы"
            ],
            IntentType.ORDER_REQUEST: [
                r"хочу\s+заказать", r"нужен\s+заказ", r"сделайте\s+заказ",
                r"закажите\s+для\s+меня", r"нужна\s+печать", r"тираж",
                r"количество", r"сроки", r"когда\s+готово"
            ],
            IntentType.COMPLAINT: [
                r"плохо", r"не\s+нравится", r"проблема", r"жалоба",
                r"неправильно", r"ошибка", r"брак", r"недоволен"
            ],
            IntentType.SUPPORT: [
                r"помощь", r"поддержка", r"не\s+работает", r"ошибка",
                r"проблема\s+с", r"техническая\s+поддержка", r"не\s+могу"
            ],
            IntentType.PRICE_INQUIRY: [
                r"сколько\s+будет\s+стоить", r"цена\s+за", r"расчет\s+стоимости",
                r"прайс", r"тарифы", r"скидки", r"акции"
            ],
            IntentType.STATUS_CHECK: [
                r"статус\s+заказа", r"где\s+мой\s+заказ", r"когда\s+будет\s+готово",
                r"проверить\s+заказ", r"отследить\s+заказ"
            ],
            IntentType.MODIFICATION: [
                r"изменить\s+заказ", r"добавить\s+в\s+заказ", r"убрать\s+из\s+заказа",
                r"исправить\s+заказ", r"корректировка"
            ],
            IntentType.CANCELLATION: [
                r"отменить\s+заказ", r"отказаться\s+от\s+заказа", r"вернуть\s+деньги"
            ]
        }

    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Загрузка базы знаний для генерации ответов"""
        return {
            "services": {
                "screen_print": {
                    "name": "Трафаретная печать",
                    "description": "Классическая технология печати на текстиле",
                    "min_quantity": 10,
                    "max_quantity": 1000,
                    "base_price": 150,
                    "production_time": "3-5 дней"
                },
                "dtg": {
                    "name": "Прямая печать на ткани",
                    "description": "Цифровая печать высокого качества",
                    "min_quantity": 1,
                    "max_quantity": 500,
                    "base_price": 300,
                    "production_time": "1-3 дня"
                },
                "embroidery": {
                    "name": "Вышивка",
                    "description": "Машинная вышивка логотипов и надписей",
                    "min_quantity": 5,
                    "max_quantity": 200,
                    "base_price": 200,
                    "production_time": "5-7 дней"
                }
            },
            "pricing": {
                "factors": ["тираж", "сложность дизайна", "срочность", "материал"],
                "discounts": {
                    "bulk_50": "5% скидка при тираже от 50 шт",
                    "bulk_100": "10% скидка при тираже от 100 шт",
                    "bulk_500": "15% скидка при тираже от 500 шт"
                }
            },
            "policies": {
                "returns": "Возврат возможен в течение 7 дней при сохранении товарного вида",
                "warranty": "Гарантия на печать 30 дней",
                "payment": "Оплата 50% предоплата, 50% после готовности"
            }
        }

    async def analyze_intent(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Анализ намерения на основе текста и контекста

        Args:
            text: Текст для анализа
            context: Дополнительный контекст (история, пользователь и т.д.)

        Returns:
            str: Определенное намерение
        """
        try:
            text_lower = text.lower().strip()

            # Проверяем паттерны для каждого типа намерения
            intent_scores = {}

            for intent_type, patterns in self.intent_patterns.items():
                score = 0
                for pattern in patterns:
                    matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
                    score += matches

                # Увеличиваем вес для более специфичных паттернов
                if intent_type in [IntentType.PRICE_INQUIRY, IntentType.STATUS_CHECK]:
                    score *= 1.5

                intent_scores[intent_type] = score

            # Находим намерение с максимальным счетом
            best_intent = max(intent_scores.items(), key=lambda x: x[1])

            # Если счет низкий, возвращаем general
            if best_intent[1] == 0:
                detected_intent = IntentType.GENERAL
                confidence = 0.3
            else:
                detected_intent = best_intent[0]
                # Рассчитываем confidence на основе максимального счета
                max_score = best_intent[1]
                total_words = len(text.split())
                confidence = min(max_score / max(1, total_words * 0.1), 1.0)

            # Учитываем контекст для улучшения точности
            if context:
                detected_intent = await self._refine_intent_with_context(
                    detected_intent, text, context
                )

            # Кешируем результат
            await self._cache_intent_result(text, detected_intent, confidence)

            # Записываем метрику
            try:
                from ..metrics_service import metrics_service
                metrics_service.record_ai_request("intent_analysis", "local", "success")
            except ImportError:
                pass  # Метрики не обязательны

            logger.info("Intent analyzed", intent=detected_intent, confidence=confidence, text_length=len(text))

            return detected_intent

        except Exception as e:
            logger.error("Intent analysis failed", error=str(e), text=text[:100])
            try:
                from ..metrics_service import metrics_service
                metrics_service.record_ai_request("intent_analysis", "local", "error")
            except ImportError:
                pass  # Метрики не обязательны
            return IntentType.GENERAL

    async def _refine_intent_with_context(
        self,
        initial_intent: str,
        text: str,
        context: Dict[str, Any]
    ) -> str:
        """Уточнение намерения с учетом контекста"""
        # Если есть история предыдущих сообщений
        if "conversation_history" in context:
            history = context["conversation_history"]
            if history:
                # Если предыдущее сообщение было о цене, текущее может быть уточнением
                last_intent = history[-1].get("intent")
                if last_intent == IntentType.PRICE_INQUIRY and initial_intent == IntentType.GENERAL:
                    return IntentType.PRICE_INQUIRY

        # Учитываем информацию о пользователе
        if "user_info" in context:
            user_info = context["user_info"]
            # Если пользователь уже имеет заказы, запрос статуса более вероятен
            if user_info.get("total_orders", 0) > 0 and "статус" in text.lower():
                return IntentType.STATUS_CHECK

        return initial_intent

    async def generate_response(
        self,
        intent: str,
        original_text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Генерация ответа на основе намерения

        Args:
            intent: Определенное намерение
            original_text: Оригинальный текст запроса
            context: Контекст для персонализации

        Returns:
            str: Сгенерированный ответ
        """
        try:
            # Получаем шаблон ответа для намерения
            response_template = self._get_response_template(intent)

            # Заполняем шаблон данными из базы знаний
            response_data = self._prepare_response_data(intent, original_text, context)

            # Генерируем персонализированный ответ
            response = self._fill_template(response_template, response_data)

            # Проверяем и корректируем ответ
            response = await self._validate_and_improve_response(response, intent, context)

            # Кешируем результат
            await self._cache_response_result(intent, original_text, response)

            # Записываем метрику
            try:
                from ..metrics_service import metrics_service
                metrics_service.record_ai_request("response_generation", "local", "success")
            except ImportError:
                pass  # Метрики не обязательны

            logger.info("Response generated", intent=intent, response_length=len(response))

            return response

        except Exception as e:
            logger.error("Response generation failed", error=str(e), intent=intent)
            try:
                from ..metrics_service import metrics_service
                metrics_service.record_ai_request("response_generation", "local", "error")
            except ImportError:
                pass  # Метрики не обязательны

            # Возвращаем стандартный ответ на ошибку
            return "Извините, произошла ошибка при обработке вашего запроса. " \
                   "Наш менеджер свяжется с вами в ближайшее время."

    def _get_response_template(self, intent: str) -> str:
        """Получение шаблона ответа для намерения"""
        templates = {
            IntentType.CONSULTATION: """
Здравствуйте! Спасибо за интерес к нашим услугам печати.

{services_info}

Для точного расчета стоимости мне нужно знать:
- Тип печати (трафаретная, DTG, вышивка)
- Тираж
- Сложность дизайна

Свяжитесь с нами для консультации: +7 (495) 123-45-67
            """,

            IntentType.PRICE_INQUIRY: """
Расчет стоимости зависит от нескольких факторов:

{pricing_info}

Базовые цены на наши услуги:
{service_prices}

Для точного расчета пришлите макет и укажите тираж.
Минимальный заказ: от {min_quantity} шт.

{contact_info}
            """,

            IntentType.ORDER_REQUEST: """
Отлично! Мы готовы принять ваш заказ.

Процесс заказа:
1. Отправьте макет в высоком разрешении
2. Укажите тираж и желаемые сроки
3. Мы подготовим расчет и образец

{production_info}

Для начала заказа позвоните: +7 (495) 123-45-67
или напишите в WhatsApp: wa.me/74951234567
            """,

            IntentType.STATUS_CHECK: """
Для проверки статуса заказа укажите номер заказа или ваши контактные данные.

Мы отправим актуальную информацию о готовности.

Если у вас нет номера заказа, свяжитесь с менеджером:
+7 (495) 123-45-67
            """,

            IntentType.COMPLAINT: """
Приносим извинения за доставленные неудобства.

Для решения проблемы:
1. Опишите ситуацию подробнее
2. Пришлите фото (если возможно)
3. Укажите номер заказа

Мы обязательно разберемся и исправим ситуацию.

Свяжитесь с нами: +7 (495) 123-45-67
            """,

            IntentType.SUPPORT: """
Техническая поддержка:

{service_prices}

Свяжитесь с нами для помощи:
+7 (495) 123-45-67
support@company.com
            """
        }

        return templates.get(intent, """
Спасибо за ваше сообщение. Мы рассмотрим ваш запрос и свяжемся с вами в ближайшее время.

Если вопрос срочный, позвоните: +7 (495) 123-45-67
        """)

    def _prepare_response_data(self, intent: str, original_text: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Подготовка данных для заполнения шаблона ответа"""
        data = {
            "services_info": self._format_services_info(),
            "pricing_info": self._format_pricing_info(),
            "service_prices": self._format_service_prices(),
            "min_quantity": "1-10",
            "contact_info": "+7 (495) 123-45-67 | email@company.com",
            "production_info": self._format_production_info()
        }

        # Добавляем персонализацию из контекста
        if context and "user_info" in context:
            user_info = context["user_info"]
            if user_info.get("name"):
                data["greeting"] = f"Здравствуйте, {user_info['name']}!"
            if user_info.get("total_orders", 0) > 0:
                data["loyalty_info"] = "Как постоянному клиенту, вам доступны специальные условия."

        return data

    def _format_services_info(self) -> str:
        """Форматирование информации об услугах"""
        services = self.knowledge_base["services"]
        info = []

        for service_key, service_data in services.items():
            info.append(f"""
• {service_data['name']}
  {service_data['description']}
  Мин. тираж: {service_data['min_quantity']} шт
  Сроки: {service_data['production_time']}
            """.strip())

        return "\n".join(info)

    def _format_pricing_info(self) -> str:
        """Форматирование информации о ценообразовании"""
        pricing = self.knowledge_base["pricing"]
        factors = ", ".join(pricing["factors"])

        discounts = []
        for discount_key, discount_desc in pricing["discounts"].items():
            discounts.append(f"• {discount_desc}")

        discount_text = "\n".join(discounts)
        return f"""
Стоимость рассчитывается с учетом: {factors}

Скидки:
{discount_text}
        """.strip()

    def _format_service_prices(self) -> str:
        """Форматирование базовых цен"""
        services = self.knowledge_base["services"]
        prices = []

        for service_key, service_data in services.items():
            prices.append(f"• {service_data['name']}: от {service_data['base_price']} руб/шт")

        return "\n".join(prices)

    def _format_production_info(self) -> str:
        """Форматирование информации о производстве"""
        return """
Этапы производства:
1. Дизайн и подготовка макета (1-2 дня)
2. Печать/вышивка (1-5 дней)
3. Контроль качества и упаковка (1 день)
4. Доставка (1-3 дня)

Общий срок: от 3 дней
        """.strip()

    def _fill_template(self, template: str, data: Dict[str, Any]) -> str:
        """Заполнение шаблона данными"""
        result = template

        for key, value in data.items():
            placeholder = f"{{{key}}}"
            result = result.replace(placeholder, str(value))

        return result.strip()

    async def _validate_and_improve_response(
        self,
        response: str,
        intent: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Валидация и улучшение сгенерированного ответа"""
        # Проверяем длину ответа
        if len(response) < 50:
            response += "\n\nЕсли у вас есть дополнительные вопросы, мы всегда готовы помочь!"

        # Добавляем контактную информацию если её нет
        if "телефон" not in response.lower() and "email" not in response.lower():
            response += "\n\nСвяжитесь с нами: +7 (495) 123-45-67"

        # Удаляем лишние плейсхолдеры
        response = re.sub(r'\{[^}]+\}', '', response)

        return response.strip()

    async def _cache_intent_result(self, text: str, intent: str, confidence: float):
        """Кеширование результата анализа намерения"""
        try:
            cache_key = f"intent:{hash(text) % 10000}"
            cache_data = {
                "intent": intent,
                "confidence": confidence,
                "timestamp": datetime.utcnow().isoformat()
            }

            async with session_service:
                client = await session_service._get_client()
                await client.setex(cache_key, 3600, json.dumps(cache_data))  # 1 час

        except Exception as e:
            logger.warning("Failed to cache intent result", error=str(e))

    async def _cache_response_result(self, intent: str, text: str, response: str):
        """Кеширование сгенерированного ответа"""
        try:
            cache_key = f"response:{intent}:{hash(text) % 10000}"
            cache_data = {
                "response": response,
                "timestamp": datetime.utcnow().isoformat()
            }

            async with session_service:
                client = await session_service._get_client()
                await client.setex(cache_key, 1800, json.dumps(cache_data))  # 30 минут

        except Exception as e:
            logger.warning("Failed to cache response result", error=str(e))

    async def get_cached_intent(self, text: str) -> Optional[Dict[str, Any]]:
        """Получение кешированного результата анализа намерения"""
        try:
            cache_key = f"intent:{hash(text) % 10000}"

            async with session_service:
                client = await session_service._get_client()
                cached_data = await client.get(cache_key)

            if cached_data:
                return json.loads(cached_data)

        except Exception as e:
            logger.warning("Failed to get cached intent", error=str(e))

        return None

    async def get_cached_response(self, intent: str, text: str) -> Optional[str]:
        """Получение кешированного ответа"""
        try:
            cache_key = f"response:{intent}:{hash(text) % 10000}"

            async with session_service:
                client = await session_service._get_client()
                cached_data = await client.get(cache_key)

            if cached_data:
                cache_obj = json.loads(cached_data)
                return cache_obj.get("response")

        except Exception as e:
            logger.warning("Failed to get cached response", error=str(e))

        return None
