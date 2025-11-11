"""
Унифицированный AI клиент
"""
import httpx
import logging
from openai import OpenAI, AsyncOpenAI
from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

from ...core.ai_config import AIProvider, ai_config

logger = logging.getLogger(__name__)


class UnifiedAIClient:
    """
    Унифицированный AI клиент, работающий с несколькими провайдерами через OpenAI-совместимый интерфейс
    """

    def __init__(self):
        self.provider = ai_config.AI_PROVIDER
        self.client = self._initialize_client()
        self.async_client = self._initialize_async_client()

    def _initialize_client(self) -> OpenAI:
        """Инициализация синхронного OpenAI клиента для выбранного провайдера"""
        config = self._get_provider_config()
        return OpenAI(
            api_key=config["api_key"],
            base_url=config["base_url"],
            timeout=httpx.Timeout(30.0)
        )

    def _initialize_async_client(self) -> AsyncOpenAI:
        """Инициализация асинхронного OpenAI клиента"""
        config = self._get_provider_config()
        return AsyncOpenAI(
            api_key=config["api_key"],
            base_url=config["base_url"],
            timeout=httpx.Timeout(30.0)
        )

    def _get_provider_config(self) -> Dict[str, str]:
        """Получение конфигурации для текущего провайдера"""
        if self.provider == AIProvider.OPENROUTER:
            return {
                "api_key": ai_config.OPENROUTER_API_KEY,
                "base_url": ai_config.OPENROUTER_BASE_URL
            }
        elif self.provider == AIProvider.OPENAI:
            return {
                "api_key": ai_config.OPENAI_API_KEY,
                "base_url": ai_config.OPENAI_BASE_URL or "https://api.openai.com/v1"
            }
        elif self.provider == AIProvider.HUGGINGFACE:
            # Hugging Face использует другой API, обработаем отдельно
            return {
                "api_key": ai_config.HUGGINGFACE_API_KEY,
                "base_url": "https://api-inference.huggingface.co"
            }
        else:
            raise ValueError(f"Неподдерживаемый AI провайдер: {self.provider}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Унифицированный метод завершения чата, работающий со всеми провайдерами
        """
        try:
            if self.provider == AIProvider.HUGGINGFACE:
                return await self._huggingface_completion(messages, model, temperature)
            else:
                return await self._openai_completion(messages, model, temperature, max_tokens)

        except Exception as e:
            logger.error(f"Ошибка AI API: {e}")
            raise

    async def _openai_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str],
        temperature: float,
        max_tokens: Optional[int]
    ) -> str:
        """Завершение через OpenAI-совместимый API (работает с OpenRouter)"""
        model = model or ai_config.DEFAULT_MODEL

        response = await self.async_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens or ai_config.MAX_TOKENS,
            stream=False
        )

        return response.choices[0].message.content

    async def _huggingface_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str],
        temperature: float
    ) -> str:
        """Завершение через Hugging Face Inference API"""
        # Конвертация сообщений в формат промпта
        prompt = self._format_messages_for_hf(messages)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ai_config.HUGGINGFACE_BASE_URL}/models/{model or ai_config.DEFAULT_MODEL}",
                headers={"Authorization": f"Bearer {ai_config.HUGGINGFACE_API_KEY}"},
                json={
                    "inputs": prompt,
                    "parameters": {
                        "temperature": temperature,
                        "max_new_tokens": ai_config.MAX_TOKENS,
                        "return_full_text": False
                    }
                },
                timeout=30.0
            )

            if response.status_code == 200:
                result = response.json()
                return result[0]['generated_text']
            else:
                raise Exception(f"Ошибка Hugging Face API: {response.text}")

    def _format_messages_for_hf(self, messages: List[Dict[str, str]]) -> str:
        """Конвертация сообщений чата в формат промпта для Hugging Face"""
        formatted = []
        for msg in messages:
            if msg['role'] == 'system':
                formatted.append(f"System: {msg['content']}")
            elif msg['role'] == 'user':
                formatted.append(f"Human: {msg['content']}")
            elif msg['role'] == 'assistant':
                formatted.append(f"Assistant: {msg['content']}")

        return "\n".join(formatted) + "\nAssistant:"
