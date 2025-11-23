"""
Сервис управления организациями для мультитенантной архитектуры
"""
import uuid
import secrets
import string
from typing import Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from datetime import datetime

from ..models.organization import Organization
from ..core.database import get_master_db
from ..core.config import settings
from ..utils.logging import get_logger
from ..utils.crypto import encrypt_data, decrypt_data

logger = get_logger(__name__)


class OrganizationService:
    """
    Сервис для управления организациями в мультитенантной системе.
    Отвечает за создание, управление и подключение к базам данных организаций.
    """
    
    def __init__(self):
        self.master_engine = None
        self._tenant_engines = {}  # Кэш движков для организаций
    
    def _get_master_engine(self):
        """Получить движок для мастер-базы"""
        if not self.master_engine:
            self.master_engine = create_engine(
                f"postgresql://{settings.db_user}:{settings.db_password}@"
                f"{settings.db_host}:{settings.db_port}/aicrm_master",
                pool_size=5,
                max_overflow=10
            )
        return self.master_engine
    
    def create_organization(
        self,
        db: Session,
        name: str,
        email: str,
        phone: Optional[str] = None,
        website: Optional[str] = None,
        plan: str = "free"
    ) -> Organization:
        """
        Создать новую организацию с отдельной базой данных.
        
        Args:
            db: Сессия мастер-базы
            name: Название организации
            email: Email организации
            phone: Телефон организации
            website: Веб-сайт организации
            plan: План подписки (free, basic, premium, enterprise)
            
        Returns:
            Organization: Созданная организация
            
        Raises:
            ValueError: Если организация с таким email уже существует
        """
        try:
            # Проверка существования организации
            existing_org = db.query(Organization).filter(
                (Organization.email == email) | (Organization.slug == self._generate_slug(name))
            ).first()
            
            if existing_org:
                raise ValueError("Organization with this email or name already exists")
            
            # Генерация уникальных данных
            org_slug = self._generate_slug(name)
            db_name = f"aicrm_org_{uuid.uuid4().hex[:8]}"
            db_username = f"org_{uuid.uuid4().hex[:8]}"
            db_password = self._generate_secure_password()
            
            # Создание организации в мастер-базе
            organization = Organization(
                name=name,
                slug=org_slug,
                email=email,
                phone=phone,
                website=website,
                db_name=db_name,
                db_host=settings.db_host or "localhost",
                db_port=settings.db_port or 5432,
                db_username=db_username,
                db_password_encrypted=encrypt_data(db_password),
                plan=plan,
                is_active=True,
                is_verified=False,
                created_at=datetime.utcnow()
            )
            
            db.add(organization)
            db.commit()
            db.refresh(organization)
            
            # Создание базы данных для организации
            self._create_organization_database(organization, db_password)
            
            logger.info(f"Organization created: {organization.name} (ID: {organization.id})")
            return organization
            
        except Exception as e:
            logger.error(f"Failed to create organization: {e}")
            db.rollback()
            raise
    
    def _create_organization_database(self, org: Organization, db_password: str):
        """
        Создать отдельную базу данных для организации.
        
        Args:
            org: Объект организации
            db_password: Пароль для базы данных
        """
        try:
            # Подключение к PostgreSQL для создания базы и пользователя
            admin_engine = create_engine(
                f"postgresql://{settings.db_user}:{settings.db_password}@"
                f"{org.db_host}:{org.db_port}/postgres"
            )
            
            with admin_engine.connect() as conn:
                # Создание пользователя для базы данных
                conn.execute(f"CREATE USER {org.db_username} WITH PASSWORD '{db_password}'")
                logger.info(f"Created database user: {org.db_username}")
                
                # Создание базы данных
                conn.execute(f"CREATE DATABASE {org.db_name} OWNER {org.db_username}")
                logger.info(f"Created database: {org.db_name}")
                
                # Назначение привилегий
                conn.execute(f"GRANT ALL PRIVILEGES ON DATABASE {org.db_name} TO {org.db_username}")
                conn.commit()
            
            # Инициализация структуры базы данных
            self._initialize_organization_database(org)
            
        except Exception as e:
            logger.error(f"Failed to create database for organization {org.name}: {e}")
            # Попытка очистить в случае ошибки
            try:
                self._cleanup_organization_database(org)
            except Exception as cleanup_error:
                logger.error(f"Cleanup failed: {cleanup_error}")
            raise RuntimeError(f"Database creation failed: {e}")
    
    def _initialize_organization_database(self, org: Organization):
        """
        Инициализировать структуру базы данных для организации.
        Создает все нужные таблицы и начальные данные.
        
        Args:
            org: Объект организации
        """
        try:
            # Создание движка для базы организации
            org_engine = create_engine(
                f"postgresql://{org.db_username}:{decrypt_data(org.db_password_encrypted)}@"
                f"{org.db_host}:{org.db_port}/{org.db_name}"
            )
            
            # Импорт всех моделей
            from ..models.base import Base
            from ..models import user
            
            # Создание всех таблиц
            Base.metadata.create_all(org_engine)
            logger.info(f"Database structure created for organization: {org.name}")
            
            # Создание администратора организации
            from ..services.auth import auth_service
            from ..api.schemas.auth import UserCreate
            
            # Создание сессии для организационной базы
            from sqlalchemy.orm import sessionmaker
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=org_engine)
            
            with SessionLocal() as org_db:
                admin_user = UserCreate(
                    email=org.email,
                    username=org.slug,
                    full_name=org.name,
                    password=decrypt_data(org.db_password_encrypted)[:12],  # Пароль организации
                    is_active=True,
                    is_superuser=True,
                    role="admin"
                )
                
                user = auth_service.create_user(org_db, admin_user.dict())
                logger.info(f"Admin user created for organization: {org.name}")
                
        except Exception as e:
            logger.error(f"Failed to initialize database for organization {org.name}: {e}")
            raise RuntimeError(f"Database initialization failed: {e}")
    
    def _cleanup_organization_database(self, org: Organization):
        """
        Очистить ресурсы базы данных при ошибке создания.
        
        Args:
            org: Объект организации
        """
        try:
            admin_engine = create_engine(
                f"postgresql://{settings.db_user}:{settings.db_password}@"
                f"{org.db_host}:{org.db_port}/postgres"
            )
            
            with admin_engine.connect() as conn:
                # Удаление базы данных
                conn.execute(f"DROP DATABASE IF EXISTS {org.db_name}")
                logger.warning(f"Dropped database: {org.db_name}")
                
                # Удаление пользователя
                conn.execute(f"DROP USER IF EXISTS {org.db_username}")
                logger.warning(f"Dropped user: {org.db_username}")
                
        except Exception as e:
            logger.error(f"Cleanup failed for organization {org.name}: {e}")
    
    def _generate_slug(self, name: str) -> str:
        """
        Сгенерировать уникальный slug из названия организации.
        
        Args:
            name: Название организации
            
        Returns:
            str: Уникальный slug
        """
        import re
        
        # Транслитерация и очистка
        slug = re.sub(r'[^a-zA-Z0-9\s]', '', name.lower())
        slug = re.sub(r'\s+', '-', slug.strip())
        
        # Добавление суффикса, если slug уже существует
        db = next(get_master_db())
        original_slug = slug
        counter = 1
        
        while db.query(Organization).filter(Organization.slug == slug).first():
            slug = f"{original_slug}-{counter}"
            counter += 1
            
        return slug
    
    def _generate_secure_password(self, length: int = 16) -> str:
        """
        Сгенерировать безопасный пароль.
        
        Args:
            length: Длина пароля
            
        Returns:
            str: Сгенерированный пароль
        """
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password
    
    def get_organization_by_slug(self, slug: str, db: Session) -> Optional[Organization]:
        """
        Получить организацию по slug.
        
        Args:
            slug: Уникальный идентификатор организации
            db: Сессия базы данных
            
        Returns:
            Organization или None
        """
        return db.query(Organization).filter(
            Organization.slug == slug,
            Organization.is_active == True
        ).first()
    
    def get_organization_engine(self, organization_id: int) -> Any:
        """
        Получить движок базы данных для организации.
        Использует кэширование для производительности.
        
        Args:
            organization_id: ID организации
            
        Returns:
            SQLAlchemy Engine для базы организации
            
        Raises:
            ValueError: Если организация не найдена или неактивна
        """
        if organization_id in self._tenant_engines:
            return self._tenant_engines[organization_id]
        
        # Получение информации об организации из мастер-базы
        master_db = next(get_master_db())
        org = master_db.query(Organization).filter(
            Organization.id == organization_id,
            Organization.is_active == True
        ).first()
        
        if not org:
            raise ValueError(f"Organization {organization_id} not found or inactive")
        
        # Создание движка для базы организации
        engine = create_engine(
            f"postgresql://{org.db_username}:{decrypt_data(org.db_password_encrypted)}@"
            f"{org.db_host}:{org.db_port}/{org.db_name}",
            pool_size=5,
            max_overflow=10
        )
        
        self._tenant_engines[organization_id] = engine
        return engine
    
    def invalidate_organization_cache(self, organization_id: int):
        """
        Инвалидировать кэш движка для организации.
        
        Args:
            organization_id: ID организации
        """
        if organization_id in self._tenant_engines:
            # Закрытие соединения
            engine = self._tenant_engines.pop(organization_id)
            engine.dispose()
            logger.info(f"Invalidated cache for organization {organization_id}")


# Глобальный экземпляр сервиса
organization_service = OrganizationService()
