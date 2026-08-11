"""
Сервис управления email шаблонами
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from ..models.email_template import EmailTemplate

logger = logging.getLogger(__name__)


class EmailTemplateService:
    """Сервис для управления email шаблонами"""

    def __init__(self, db: Session):
        self.db = db

    async def create_template(
        self, template_data: Dict[str, Any], created_by: int
    ) -> EmailTemplate:
        """
        Создание нового шаблона

        Args:
            template_data: Данные шаблона
            created_by: ID пользователя, создавшего шаблон

        Returns:
            EmailTemplate: Созданный шаблон
        """
        try:
            # Проверяем уникальность имени
            existing = (
                self.db.query(EmailTemplate)
                .filter(EmailTemplate.name == template_data["name"])
                .first()
            )

            if existing:
                raise ValueError(
                    f"Шаблон с именем '{template_data['name']}' уже существует"
                )

            # Если устанавливаем как default, снимаем флаг с других шаблонов категории
            if template_data.get("is_default", False):
                self.db.query(EmailTemplate).filter(
                    and_(
                        EmailTemplate.category == template_data["category"],
                        EmailTemplate.is_default == True,
                    )
                ).update({"is_default": False})

            template = EmailTemplate(
                **template_data, created_by=created_by, updated_by=created_by
            )

            self.db.add(template)
            self.db.commit()
            self.db.refresh(template)

            logger.info(f"Создан новый email шаблон: {template.name}")
            return template

        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка создания шаблона: {e}")
            raise

    async def update_template(
        self, template_id: int, update_data: Dict[str, Any], updated_by: int
    ) -> EmailTemplate:
        """
        Обновление шаблона

        Args:
            template_id: ID шаблона
            update_data: Данные для обновления
            updated_by: ID пользователя, обновившего шаблон

        Returns:
            EmailTemplate: Обновленный шаблон
        """
        try:
            template = (
                self.db.query(EmailTemplate)
                .filter(EmailTemplate.id == template_id)
                .first()
            )

            if not template:
                raise ValueError(f"Шаблон с ID {template_id} не найден")

            # Проверяем уникальность имени при изменении
            if "name" in update_data and update_data["name"] != template.name:
                existing = (
                    self.db.query(EmailTemplate)
                    .filter(
                        and_(
                            EmailTemplate.name == update_data["name"],
                            EmailTemplate.id != template_id,
                        )
                    )
                    .first()
                )

                if existing:
                    raise ValueError(
                        f"Шаблон с именем '{update_data['name']}' уже существует"
                    )

            # Если устанавливаем как default, снимаем флаг с других шаблонов категории
            if update_data.get("is_default", False):
                category = update_data.get("category", template.category)
                self.db.query(EmailTemplate).filter(
                    and_(
                        EmailTemplate.category == category,
                        EmailTemplate.id != template_id,
                        EmailTemplate.is_default == True,
                    )
                ).update({"is_default": False})

            # Обновляем поля
            for key, value in update_data.items():
                if hasattr(template, key):
                    setattr(template, key, value)

            template.updated_by = updated_by

            self.db.commit()
            self.db.refresh(template)

            logger.info(f"Обновлен email шаблон: {template.name}")
            return template

        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка обновления шаблона: {e}")
            raise

    async def delete_template(self, template_id: int) -> bool:
        """
        Удаление шаблона

        Args:
            template_id: ID шаблона

        Returns:
            bool: True если удалено успешно
        """
        try:
            template = (
                self.db.query(EmailTemplate)
                .filter(EmailTemplate.id == template_id)
                .first()
            )

            if not template:
                raise ValueError(f"Шаблон с ID {template_id} не найден")

            self.db.delete(template)
            self.db.commit()

            logger.info(f"Удален email шаблон: {template.name}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка удаления шаблона: {e}")
            raise

    async def get_template_by_id(self, template_id: int) -> Optional[EmailTemplate]:
        """
        Получение шаблона по ID

        Args:
            template_id: ID шаблона

        Returns:
            EmailTemplate или None
        """
        return (
            self.db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
        )

    async def get_template_by_name(self, name: str) -> Optional[EmailTemplate]:
        """
        Получение шаблона по имени

        Args:
            name: Имя шаблона

        Returns:
            EmailTemplate или None
        """
        return self.db.query(EmailTemplate).filter(EmailTemplate.name == name).first()

    async def get_templates(
        self,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[EmailTemplate]:
        """
        Получение списка шаблонов с фильтрами

        Args:
            category: Фильтр по категории
            is_active: Фильтр по активности
            search: Поиск по названию или описанию
            limit: Максимальное количество
            offset: Смещение

        Returns:
            List[EmailTemplate]: Список шаблонов
        """
        query = self.db.query(EmailTemplate)

        # Применяем фильтры
        if category:
            query = query.filter(EmailTemplate.category == category)

        if is_active is not None:
            query = query.filter(EmailTemplate.is_active == is_active)

        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    EmailTemplate.name.ilike(search_filter),
                    EmailTemplate.display_name.ilike(search_filter),
                    EmailTemplate.description.ilike(search_filter),
                )
            )

        # Сортировка: default шаблоны первыми, затем по названию
        query = query.order_by(
            EmailTemplate.is_default.desc(), EmailTemplate.display_name
        )

        return query.offset(offset).limit(limit).all()

    async def get_default_template(self, category: str) -> Optional[EmailTemplate]:
        """
        Получение шаблона по умолчанию для категории

        Args:
            category: Категория

        Returns:
            EmailTemplate или None
        """
        return (
            self.db.query(EmailTemplate)
            .filter(
                and_(
                    EmailTemplate.category == category,
                    EmailTemplate.is_default == True,
                    EmailTemplate.is_active == True,
                )
            )
            .first()
        )

    async def duplicate_template(
        self, template_id: int, new_name: str, new_display_name: str, created_by: int
    ) -> EmailTemplate:
        """
        Дублирование шаблона

        Args:
            template_id: ID оригинального шаблона
            new_name: Новое имя
            new_display_name: Новое отображаемое имя
            created_by: ID пользователя

        Returns:
            EmailTemplate: Новый шаблон
        """
        try:
            original = await self.get_template_by_id(template_id)
            if not original:
                raise ValueError(f"Шаблон с ID {template_id} не найден")

            # Проверяем уникальность нового имени
            existing = (
                self.db.query(EmailTemplate)
                .filter(EmailTemplate.name == new_name)
                .first()
            )

            if existing:
                raise ValueError(f"Шаблон с именем '{new_name}' уже существует")

            # Создаем копию
            template_data = original.to_dict()
            template_data.update(
                {
                    "name": new_name,
                    "display_name": new_display_name,
                    "is_default": False,  # Копия не может быть default
                    "usage_count": 0,
                    "last_used_at": None,
                }
            )

            # Удаляем системные поля
            for field in ["id", "created_at", "updated_at", "created_by", "updated_by"]:
                template_data.pop(field, None)

            return await self.create_template(template_data, created_by)

        except Exception as e:
            logger.error(f"Ошибка дублирования шаблона: {e}")
            raise

    async def render_template(
        self, template_id: int, variables: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Рендеринг шаблона с переменными

        Args:
            template_id: ID шаблона
            variables: Переменные для подстановки

        Returns:
            Dict с rendered subject, html и text
        """
        try:
            template = await self.get_template_by_id(template_id)
            if not template:
                raise ValueError(f"Шаблон с ID {template_id} не найден")

            if template.is_active is False:
                raise ValueError(f"Шаблон '{template.name}' неактивен")

            # Валидируем переменные
            is_valid, missing = template.validate_variables(variables)
            if not is_valid:
                raise ValueError(
                    f"Отсутствуют обязательные переменные: {', '.join(missing)}"
                )

            # Рендерим
            subject = template.render_subject(variables)
            html_body = template.render_html(variables)
            text_body = template.render_text(variables)

            # Увеличиваем счетчик использования
            template.increment_usage()
            self.db.commit()

            return {"subject": subject, "html_body": html_body, "text_body": text_body}

        except Exception as e:
            logger.error(f"Ошибка рендеринга шаблона: {e}")
            raise

    async def render_template_by_name(
        self, template_name: str, variables: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Рендеринг шаблона по имени

        Args:
            template_name: Имя шаблона
            variables: Переменные для подстановки

        Returns:
            Dict с rendered subject, html и text
        """
        template = await self.get_template_by_name(template_name)
        if not template:
            raise ValueError(f"Шаблон '{template_name}' не найден")

        return await self.render_template(template.id, variables)

    async def get_template_stats(self) -> Dict[str, Any]:
        """
        Получение статистики по шаблонам

        Returns:
            Dict со статистикой
        """
        try:
            total = self.db.query(EmailTemplate).count()
            active = (
                self.db.query(EmailTemplate)
                .filter(EmailTemplate.is_active == True)
                .count()
            )
            by_category = {}

            # Статистика по категориям
            categories = self.db.query(EmailTemplate.category).distinct().all()
            for (category,) in categories:
                count = (
                    self.db.query(EmailTemplate)
                    .filter(EmailTemplate.category == category)
                    .count()
                )
                by_category[category] = count

            # Самые используемые
            top_used = (
                self.db.query(EmailTemplate)
                .filter(EmailTemplate.usage_count > 0)
                .order_by(EmailTemplate.usage_count.desc())
                .limit(5)
                .all()
            )

            top_templates = [
                {
                    "id": t.id,
                    "name": t.name,
                    "display_name": t.display_name,
                    "usage_count": t.usage_count,
                    "last_used_at": (
                        t.last_used_at.isoformat() if t.last_used_at else None
                    ),
                }
                for t in top_used
            ]

            return {
                "total_templates": total,
                "active_templates": active,
                "inactive_templates": total - active,
                "categories": by_category,
                "top_used_templates": top_templates,
            }

        except Exception as e:
            logger.error(f"Ошибка получения статистики шаблонов: {e}")
            return {}

    async def initialize_default_templates(
        self, created_by: int = 1
    ) -> List[EmailTemplate]:
        """
        Инициализация стандартных шаблонов

        Args:
            created_by: ID пользователя для создания

        Returns:
            List[EmailTemplate]: Созданные шаблоны
        """
        try:
            created_templates = []

            for template_data in EmailTemplate.get_default_templates():
                # Проверяем, существует ли уже
                existing = await self.get_template_by_name(template_data["name"])
                if existing:
                    continue

                # Создаем шаблон
                template = await self.create_template(template_data, created_by)
                created_templates.append(template)

            logger.info(
                f"Инициализировано {len(created_templates)} стандартных шаблонов"
            )
            return created_templates

        except Exception as e:
            logger.error(f"Ошибка инициализации стандартных шаблонов: {e}")
            raise

    async def export_templates(
        self, category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Экспорт шаблонов для резервного копирования

        Args:
            category: Опциональный фильтр по категории

        Returns:
            List[Dict]: Данные шаблонов
        """
        templates = await self.get_templates(category=category, limit=1000)
        return [template.to_dict() for template in templates]

    async def import_templates(
        self,
        templates_data: List[Dict[str, Any]],
        imported_by: int,
        overwrite_existing: bool = False,
    ) -> Dict[str, Any]:
        """
        Импорт шаблонов из резервной копии

        Args:
            templates_data: Данные шаблонов
            imported_by: ID пользователя
            overwrite_existing: Перезаписывать существующие

        Returns:
            Dict с результатами импорта
        """
        try:
            imported = 0
            skipped = 0
            errors = []

            for template_data in templates_data:
                try:
                    name = template_data.get("name")
                    if not name:
                        errors.append("Шаблон без имени пропущен")
                        continue

                    existing = await self.get_template_by_name(name)

                    if existing and not overwrite_existing:
                        skipped += 1
                        continue

                    # Подготавливаем данные для импорта
                    import_data = template_data.copy()

                    # Удаляем системные поля
                    for field in [
                        "id",
                        "created_at",
                        "updated_at",
                        "created_by",
                        "updated_by",
                    ]:
                        import_data.pop(field, None)

                    # Устанавливаем импортировавшего пользователя
                    import_data["updated_by"] = imported_by

                    if existing:
                        # Обновляем существующий
                        await self.update_template(
                            existing.id, import_data, imported_by
                        )
                    else:
                        # Создаем новый
                        import_data["created_by"] = imported_by
                        await self.create_template(import_data, imported_by)

                    imported += 1

                except Exception as e:
                    errors.append(f"Ошибка импорта шаблона '{name}': {str(e)}")

            return {
                "imported": imported,
                "skipped": skipped,
                "errors": errors,
                "total_processed": len(templates_data),
            }

        except Exception as e:
            logger.error(f"Ошибка импорта шаблонов: {e}")
            raise


# Функция для создания экземпляра сервиса
def get_email_template_service(db: Session) -> EmailTemplateService:
    """
    Получить экземпляр сервиса шаблонов

    Args:
        db: Сессия базы данных

    Returns:
        EmailTemplateService: Экземпляр сервиса
    """
    return EmailTemplateService(db)
