"""
Роутер для управления кампаниями и их AI настройками
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...core.dependencies import get_current_user, get_db
from ...models.campaign import Campaign, CampaignAISettings
from ...models.user import User
from ...utils.logging import get_logger
from ..schemas.campaign import (
    CampaignAISettingsCreate,
    CampaignAISettingsResponse,
    CampaignAISettingsUpdate,
    CampaignCreate,
    CampaignListResponse,
    CampaignResponse,
    CampaignUpdate,
)

router = APIRouter(
    prefix="/campaigns",
    tags=["Campaigns"],
    responses={
        400: {"description": "Bad Request - Неверные параметры запроса"},
        401: {"description": "Unauthorized - Не авторизован"},
        403: {"description": "Forbidden - Доступ запрещен"},
        404: {"description": "Not Found - Кампания не найдена"},
        422: {"description": "Validation Error - Ошибка валидации данных"},
        500: {"description": "Internal Server Error - Внутренняя ошибка сервера"},
    },
)

logger = get_logger(__name__)


@router.post(
    "/",
    response_model=CampaignResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создание новой кампании",
    description="""
    Создает новую маркетинговую кампанию с базовыми настройками.

    **Особенности:**
    - Автоматически создается структура для AI настроек кампании
    - Кампания привязывается к организации пользователя
    - Статус по умолчанию: draft
    """,
    response_description="Созданная кампания",
)
async def create_campaign(
    campaign_data: CampaignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CampaignResponse:
    """
    Создание новой кампании.
    """
    try:
        # Создаем кампанию
        campaign = Campaign(
            name=campaign_data.name,
            description=campaign_data.description,
            organization_id=campaign_data.organization_id,
            status="draft",
            is_active=True,
        )

        db.add(campaign)
        db.commit()
        db.refresh(campaign)

        # Автоматически создаем базовые AI настройки для кампании
        ai_settings = CampaignAISettings(campaign_id=campaign.id)
        db.add(ai_settings)
        db.commit()

        logger.info(
            f"Campaign created: ID {campaign.id}, name '{campaign.name}' by user {current_user.id}"
        )

        return CampaignResponse(
            id=campaign.id,
            name=campaign.name,
            description=campaign.description,
            organization_id=campaign.organization_id,
            is_active=campaign.is_active,
            status=campaign.status,
            created_at=campaign.created_at,
            updated_at=campaign.updated_at,
            ai_settings={
                "default_model": ai_settings.default_model,
                "provider": ai_settings.provider,
                "temperature": ai_settings.temperature,
                "max_tokens": ai_settings.max_tokens,
            },
        )

    except Exception as e:
        logger.error(f"Failed to create campaign: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось создать кампанию: {str(e)}",
        )


@router.get(
    "/",
    response_model=CampaignListResponse,
    status_code=status.HTTP_200_OK,
    summary="Получение списка кампаний",
    description="""
    Возвращает список кампаний с поддержкой пагинации и фильтрации.

    **Параметры фильтрации:**
    - `organization_id`: ID организации
    - `status`: статус кампании (draft, active, paused, completed)
    - `is_active`: активна ли кампания
    - `page`: номер страницы (начиная с 1)
    - `per_page`: количество элементов на странице
    """,
    response_description="Список кампаний с метаданными",
)
async def get_campaigns(
    organization_id: Optional[int] = Query(None, description="ID организации"),
    status: Optional[str] = Query(None, description="Статус кампании"),
    is_active: Optional[bool] = Query(None, description="Активна ли кампания"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    per_page: int = Query(20, ge=1, le=100, description="Элементов на странице"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CampaignListResponse:
    """
    Получение списка кампаний с фильтрацией и пагинацией.
    """
    try:
        query = select(Campaign)

        # Применяем фильтры
        if organization_id:
            query = query.where(Campaign.organization_id == organization_id)
        if status:
            query = query.where(Campaign.status == status)
        if is_active is not None:
            query = query.where(Campaign.is_active == is_active)

        # Пагинация
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        result = db.execute(query)
        campaigns = result.scalars().all()

        # Получаем общее количество
        count_query = select(Campaign)
        if organization_id:
            count_query = count_query.where(Campaign.organization_id == organization_id)
        if status:
            count_query = count_query.where(Campaign.status == status)
        if is_active is not None:
            count_query = count_query.where(Campaign.is_active == is_active)

        total = db.execute(count_query).scalar() or 0

        # Формируем ответ
        campaign_responses = []
        for campaign in campaigns:
            ai_settings = None
            if campaign.ai_settings:
                ai_settings = {
                    "default_model": campaign.ai_settings.default_model,
                    "provider": campaign.ai_settings.provider,
                    "temperature": campaign.ai_settings.temperature,
                    "max_tokens": campaign.ai_settings.max_tokens,
                    "auto_reply_enabled": campaign.ai_settings.auto_reply_enabled,
                }

            campaign_responses.append(
                CampaignResponse(
                    id=campaign.id,
                    name=campaign.name,
                    description=campaign.description,
                    organization_id=campaign.organization_id,
                    is_active=campaign.is_active,
                    status=campaign.status,
                    created_at=campaign.created_at,
                    updated_at=campaign.updated_at,
                    ai_settings=ai_settings,
                )
            )

        return CampaignListResponse(
            campaigns=campaign_responses, total=total, page=page, per_page=per_page
        )

    except Exception as e:
        logger.error(f"Failed to get campaigns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось получить список кампаний: {str(e)}",
        )


@router.get(
    "/{campaign_id}",
    response_model=CampaignResponse,
    status_code=status.HTTP_200_OK,
    summary="Получение кампании по ID",
    description="""
    Возвращает детальную информацию о кампании по ее ID.

    **Включает:**
    - Основную информацию о кампании
    - AI настройки кампании
    - Метаданные (даты создания/обновления)
    """,
    response_description="Информация о кампании",
)
async def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CampaignResponse:
    """
    Получение кампании по ID.
    """
    try:
        campaign = db.get(Campaign, campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Кампания не найдена"
            )

        ai_settings = None
        if campaign.ai_settings:
            ai_settings = {
                "default_model": campaign.ai_settings.default_model,
                "provider": campaign.ai_settings.provider,
                "temperature": campaign.ai_settings.temperature,
                "max_tokens": campaign.ai_settings.max_tokens,
                "auto_reply_enabled": campaign.ai_settings.auto_reply_enabled,
                "custom_prompt": campaign.ai_settings.custom_prompt,
                "target_audience": campaign.ai_settings.target_audience,
                "brand_voice": campaign.ai_settings.brand_voice,
            }

        return CampaignResponse(
            id=campaign.id,
            name=campaign.name,
            description=campaign.description,
            organization_id=campaign.organization_id,
            is_active=campaign.is_active,
            status=campaign.status,
            created_at=campaign.created_at,
            updated_at=campaign.updated_at,
            ai_settings=ai_settings,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get campaign {campaign_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось получить кампанию: {str(e)}",
        )


@router.put(
    "/{campaign_id}",
    response_model=CampaignResponse,
    status_code=status.HTTP_200_OK,
    summary="Обновление кампании",
    description="""
    Обновляет информацию о кампании.

    **Можно обновить:**
    - Название и описание кампании
    - Статус кампании
    - Активность кампании
    """,
    response_description="Обновленная кампания",
)
async def update_campaign(
    campaign_id: int,
    campaign_data: CampaignUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CampaignResponse:
    """
    Обновление кампании.
    """
    try:
        campaign = db.get(Campaign, campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Кампания не найдена"
            )

        # Обновляем поля
        update_data = campaign_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(campaign, key, value)

        campaign.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(campaign)

        logger.info(f"Campaign updated: ID {campaign.id} by user {current_user.id}")

        ai_settings = None
        if campaign.ai_settings:
            ai_settings = {
                "default_model": campaign.ai_settings.default_model,
                "provider": campaign.ai_settings.provider,
                "temperature": campaign.ai_settings.temperature,
                "max_tokens": campaign.ai_settings.max_tokens,
            }

        return CampaignResponse(
            id=campaign.id,
            name=campaign.name,
            description=campaign.description,
            organization_id=campaign.organization_id,
            is_active=campaign.is_active,
            status=campaign.status,
            created_at=campaign.created_at,
            updated_at=campaign.updated_at,
            ai_settings=ai_settings,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update campaign {campaign_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось обновить кампанию: {str(e)}",
        )


@router.put(
    "/{campaign_id}/ai-settings",
    response_model=CampaignAISettingsResponse,
    status_code=status.HTTP_200_OK,
    summary="Обновление AI настроек кампании",
    description="""
    Обновляет AI настройки для конкретной кампании.

    **Можно обновить:**
    - Модель AI и параметры генерации
    - API ключи для разных провайдеров
    - Настройки автоответов
    - Специфические промпты и стиль общения
    - Лимиты использования токенов
    """,
    response_description="Обновленные AI настройки кампании",
)
async def update_campaign_ai_settings(
    campaign_id: int,
    ai_settings_data: CampaignAISettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CampaignAISettingsResponse:
    """
    Обновление AI настроек кампании.
    """
    try:
        # Проверяем, существует ли кампания
        campaign = db.get(Campaign, campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Кампания не найдена"
            )

        # Получаем или создаем AI настройки для кампании
        ai_settings = campaign.ai_settings
        if not ai_settings:
            ai_settings = CampaignAISettings(campaign_id=campaign_id)
            db.add(ai_settings)

        # Обновляем поля
        update_data = ai_settings_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(ai_settings, key, value)

        ai_settings.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(ai_settings)

        logger.info(
            f"Campaign AI settings updated: campaign_id {campaign_id} by user {current_user.id}"
        )

        return CampaignAISettingsResponse(
            id=ai_settings.id,
            campaign_id=ai_settings.campaign_id,
            default_model=ai_settings.default_model,
            temperature=ai_settings.temperature,
            max_tokens=ai_settings.max_tokens,
            provider=ai_settings.provider,
            auto_reply_enabled=ai_settings.auto_reply_enabled,
            auto_reply_temperature=ai_settings.auto_reply_temperature,
            auto_reply_max_tokens=ai_settings.auto_reply_max_tokens,
            custom_prompt=ai_settings.custom_prompt,
            target_audience=ai_settings.target_audience,
            brand_voice=ai_settings.brand_voice,
            daily_token_limit=ai_settings.daily_token_limit,
            monthly_token_limit=ai_settings.monthly_token_limit,
            created_at=ai_settings.created_at,
            updated_at=ai_settings.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update AI settings for campaign {campaign_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось обновить AI настройки кампании: {str(e)}",
        )


@router.get(
    "/{campaign_id}/ai-settings",
    response_model=CampaignAISettingsResponse,
    status_code=status.HTTP_200_OK,
    summary="Получение AI настроек кампании",
    description="""
    Возвращает AI настройки для конкретной кампании.

    **Включает:**
    - Параметры модели AI
    - Настройки автоответов
    - Специфические промпты кампании
    - Лимиты токенов

    **Примечание:** API ключи не возвращаются по соображениям безопасности
    """,
    response_description="AI настройки кампании",
)
async def get_campaign_ai_settings(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CampaignAISettingsResponse:
    """
    Получение AI настроек кампании.
    """
    try:
        campaign = db.get(Campaign, campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Кампания не найдена"
            )

        ai_settings = campaign.ai_settings
        if not ai_settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AI настройки для кампании не найдены",
            )

        return CampaignAISettingsResponse(
            id=ai_settings.id,
            campaign_id=ai_settings.campaign_id,
            default_model=ai_settings.default_model,
            temperature=ai_settings.temperature,
            max_tokens=ai_settings.max_tokens,
            provider=ai_settings.provider,
            auto_reply_enabled=ai_settings.auto_reply_enabled,
            auto_reply_temperature=ai_settings.auto_reply_temperature,
            auto_reply_max_tokens=ai_settings.auto_reply_max_tokens,
            custom_prompt=ai_settings.custom_prompt,
            target_audience=ai_settings.target_audience,
            brand_voice=ai_settings.brand_voice,
            daily_token_limit=ai_settings.daily_token_limit,
            monthly_token_limit=ai_settings.monthly_token_limit,
            created_at=ai_settings.created_at,
            updated_at=ai_settings.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get AI settings for campaign {campaign_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось получить AI настройки кампании: {str(e)}",
        )


@router.delete(
    "/{campaign_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление кампании",
    description="""
    Удаляет кампанию и все связанные с ней AI настройки.

    **Предупреждение:** Операция необратима!
    """,
    response_description="Кампания успешно удалена",
)
async def delete_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Удаление кампании.
    """
    try:
        campaign = db.get(Campaign, campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Кампания не найдена"
            )

        # Удаляем кампанию (AI настройки удалятся каскадно)
        db.delete(campaign)
        db.commit()

        logger.info(f"Campaign deleted: ID {campaign_id} by user {current_user.id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete campaign {campaign_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось удалить кампанию: {str(e)}",
        )
