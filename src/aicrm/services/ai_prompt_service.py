"""
Сервис для управления AI промптами
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from ..models.ai_prompt import AIPrompt


class AIPromptService:
    """Сервис для работы с AI промптами"""

    def __init__(self, db: Session):
        self.db = db

    def get_all_prompts(self) -> List[AIPrompt]:
        """Получить все промпты"""
        return self.db.query(AIPrompt).order_by(AIPrompt.created_at.desc()).all()

    def get_active_prompts(self) -> List[AIPrompt]:
        """Получить активные промпты"""
        return (
            self.db.query(AIPrompt)
            .filter(AIPrompt.is_active)
            .order_by(AIPrompt.category, AIPrompt.name)
            .all()
        )

    def get_prompts_by_category(self, category: str) -> List[AIPrompt]:
        """Получить промпты по категории"""
        return (
            self.db.query(AIPrompt)
            .filter(AIPrompt.category == category, AIPrompt.is_active)
            .order_by(AIPrompt.name)
            .all()
        )

    def get_prompt_by_id(self, prompt_id: int) -> Optional[AIPrompt]:
        """Получить промпт по ID"""
        return self.db.query(AIPrompt).filter(AIPrompt.id == prompt_id).first()

    def create_prompt(
        self, name: str, content: str, category: str, **kwargs
    ) -> AIPrompt:
        """Создать новый промпт"""
        prompt = AIPrompt(name=name, content=content, category=category, **kwargs)
        self.db.add(prompt)
        self.db.commit()
        self.db.refresh(prompt)
        return prompt

    def update_prompt(self, prompt_id: int, **kwargs) -> Optional[AIPrompt]:
        """Обновить промпт"""
        prompt = self.get_prompt_by_id(prompt_id)
        if not prompt:
            return None

        for key, value in kwargs.items():
            if hasattr(prompt, key):
                setattr(prompt, key, value)

        self.db.commit()
        self.db.refresh(prompt)
        return prompt

    def delete_prompt(self, prompt_id: int) -> bool:
        """Удалить промпт"""
        prompt = self.get_prompt_by_id(prompt_id)
        if not prompt:
            return False

        self.db.delete(prompt)
        self.db.commit()
        return True

    def toggle_prompt_status(self, prompt_id: int) -> Optional[AIPrompt]:
        """Переключить статус промпта (активен/неактивен)"""
        prompt = self.get_prompt_by_id(prompt_id)
        if not prompt:
            return None

        prompt.is_active = not prompt.is_active
        self.db.commit()
        self.db.refresh(prompt)
        return prompt
