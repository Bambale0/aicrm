"""
Схемы для AI Manager API
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class AIPromptBase(BaseModel):
    """Базовая схема AI промпта"""
    name: str = Field(..., max_length=255, description="Название промпта")
    content: str = Field(..., description="Содержимое промпта")
    category: str = Field(..., max_length=100, description="Категория промпта")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Температура генерации")
    max_tokens: int = Field(1000, gt=0, description="Максимальное количество токенов")
    model: str = Field("deepseek/deepseek-chat-v3.1", description="Модель AI")


class AIPromptCreate(AIPromptBase):
    """Схема для создания AI промпта"""
    is_active: bool = Field(True, description="Активен ли промпт")


class AIPromptUpdate(BaseModel):
    """Схема для обновления AI промпта"""
    name: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, gt=0)
    model: Optional[str] = None
    is_active: Optional[bool] = None


class AIPromptResponse(AIPromptBase):
    """Схема ответа AI промпта"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ServiceBase(BaseModel):
    """Базовая схема услуги"""
    name: str = Field(..., max_length=255, description="Название услуги")
    description: str = Field(..., description="Описание услуги")
    price: float = Field(..., gt=0, description="Цена услуги")
    category: str = Field(..., max_length=100, description="Категория услуги")
    duration_hours: Optional[float] = Field(None, gt=0, description="Продолжительность в часах")
    unit: str = Field("шт", max_length=50, description="Единица измерения")


class ServiceCreate(ServiceBase):
    """Схема для создания услуги"""
    is_active: bool = Field(True, description="Активна ли услуга")


class ServiceUpdate(BaseModel):
    """Схема для обновления услуги"""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    category: Optional[str] = Field(None, max_length=100)
    duration_hours: Optional[float] = Field(None, gt=0)
    unit: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class ServiceResponse(ServiceBase):
    """Схема ответа услуги"""
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    """Базовая схема товара"""
    name: str = Field(..., max_length=255, description="Название товара")
    description: str = Field(..., description="Описание товара")
    price: float = Field(..., gt=0, description="Цена товара")
    category: str = Field(..., max_length=100, description="Категория товара")
    stock_quantity: int = Field(0, ge=0, description="Количество на складе")
    sku: Optional[str] = Field(None, max_length=100, description="Артикул товара")
    unit: str = Field("шт", max_length=50, description="Единица измерения")
    weight_kg: Optional[float] = Field(None, gt=0, description="Вес в килограммах")
    dimensions: Optional[str] = Field(None, max_length=100, description="Габариты")


class ProductCreate(ProductBase):
    """Схема для создания товара"""
    is_active: bool = Field(True, description="Активен ли товар")


class ProductUpdate(BaseModel):
    """Схема для обновления товара"""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    category: Optional[str] = Field(None, max_length=100)
    stock_quantity: Optional[int] = Field(None, ge=0)
    sku: Optional[str] = Field(None, max_length=100)
    unit: Optional[str] = Field(None, max_length=50)
    weight_kg: Optional[float] = Field(None, gt=0)
    dimensions: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    """Схема ответа товара"""
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CategoryResponse(BaseModel):
    """Схема ответа для списка категорий"""
    categories: List[str]
