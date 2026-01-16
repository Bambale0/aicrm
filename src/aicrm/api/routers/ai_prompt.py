"""
Маршруты для управления AI промптами
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...core.database import get_master_db
from ...models.ai_prompt import AIPrompt
from ...utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/ai-prompts", tags=["AI Prompts"])


class AIPromptCreate(BaseModel):
    """Схема создания AI промпта"""

    name: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1, max_length=100)
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(1000, gt=0)
    model: Optional[str] = Field("deepseek/deepseek-chat-v3.1")


class AIPromptUpdate(BaseModel):
    """Схема обновления AI промпта"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, gt=0)
    model: Optional[str] = None
    is_active: Optional[bool] = None


class AIPromptResponse(BaseModel):
    """Схема ответа с AI промптом"""

    id: int
    name: str
    content: str
    category: str
    is_active: bool
    temperature: float
    max_tokens: int
    model: str
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True


@router.post("/", response_model=AIPromptResponse, status_code=status.HTTP_201_CREATED)
async def create_ai_prompt(
    prompt_data: AIPromptCreate, db: Session = Depends(get_master_db)
):
    """
    Создать новый AI промпт

    Args:
        prompt_data: Данные для создания промпта

    Returns:
        AIPromptResponse: Созданный промпт
    """
    # Проверяем уникальность имени
    existing = db.query(AIPrompt).filter(AIPrompt.name == prompt_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt with this name already exists",
        )

    prompt = AIPrompt(**prompt_data.dict())
    db.add(prompt)
    db.commit()
    db.refresh(prompt)

    logger.info(f"AI prompt created: {prompt.name} (ID: {prompt.id})")

    return AIPromptResponse.from_orm(prompt)


@router.get("/", response_model=List[AIPromptResponse])
async def list_ai_prompts(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    active_only: bool = False,
    db: Session = Depends(get_master_db),
):
    """
    Получить список AI промптов

    Args:
        skip: Количество пропускаемых записей
        limit: Максимальное количество возвращаемых записей
        category: Фильтр по категории
        active_only: Показывать только активные промпты

    Returns:
        List[AIPromptResponse]: Список промптов
    """
    query = db.query(AIPrompt)

    if category:
        query = query.filter(AIPrompt.category == category)

    if active_only:
        query = query.filter(AIPrompt.is_active == True)

    prompts = query.offset(skip).limit(limit).all()

    return [AIPromptResponse.from_orm(prompt) for prompt in prompts]


@router.get("/{prompt_id}", response_model=AIPromptResponse)
async def get_ai_prompt(prompt_id: int, db: Session = Depends(get_master_db)):
    """
    Получить AI промпт по ID

    Args:
        prompt_id: ID промпта

    Returns:
        AIPromptResponse: Информация о промпте

    Raises:
        HTTPException: Если промпт не найден
    """
    prompt = db.query(AIPrompt).filter(AIPrompt.id == prompt_id).first()

    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="AI prompt not found"
        )

    return AIPromptResponse.from_orm(prompt)


@router.put("/{prompt_id}", response_model=AIPromptResponse)
async def update_ai_prompt(
    prompt_id: int, update_data: AIPromptUpdate, db: Session = Depends(get_master_db)
):
    """
    Обновить AI промпт

    Args:
        prompt_id: ID промпта
        update_data: Данные для обновления

    Returns:
        AIPromptResponse: Обновленный промпт

    Raises:
        HTTPException: Если промпт не найден
    """
    prompt = db.query(AIPrompt).filter(AIPrompt.id == prompt_id).first()

    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="AI prompt not found"
        )

    # Проверяем уникальность имени при изменении
    if update_data.name and update_data.name != prompt.name:
        existing = db.query(AIPrompt).filter(AIPrompt.name == update_data.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prompt with this name already exists",
            )

    # Обновляем поля
    update_dict = update_data.dict(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(prompt, field, value)

    db.commit()
    db.refresh(prompt)

    logger.info(f"AI prompt updated: {prompt.name} (ID: {prompt.id})")

    return AIPromptResponse.from_orm(prompt)


@router.delete("/{prompt_id}")
async def delete_ai_prompt(prompt_id: int, db: Session = Depends(get_master_db)):
    """
    Удалить AI промпт

    Args:
        prompt_id: ID промпта

    Returns:
        dict: Результат операции

    Raises:
        HTTPException: Если промпт не найден
    """
    prompt = db.query(AIPrompt).filter(AIPrompt.id == prompt_id).first()

    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="AI prompt not found"
        )

    db.delete(prompt)
    db.commit()

    logger.info(f"AI prompt deleted: {prompt.name} (ID: {prompt.id})")

    return {"message": "AI prompt deleted successfully", "id": prompt_id}


@router.get("/categories/list")
async def get_prompt_categories(db: Session = Depends(get_master_db)):
    """
    Получить список всех категорий промптов

    Returns:
        dict: Список категорий с количеством промптов
    """
    from sqlalchemy import func

    categories = (
        db.query(AIPrompt.category, func.count(AIPrompt.id))
        .group_by(AIPrompt.category)
        .all()
    )

    return {
        "categories": [
            {"name": category, "count": count} for category, count in categories
        ]
    }
