"""
Конфигурации моделей для совместимости с OpenRouter
"""

OPENROUTER_MODELS = {
    "deepseek-chat": {
        "id": "deepseek/deepseek-chat-v3.1",
        "name": "DeepSeek Chat V3.1",
        "context_length": 32768,
        "pricing": {"input": 0.00014, "output": 0.00028}
    },
    "kimi-k2": {
        "id": "moonshotai/kimi-k2",
        "name": "Kimi K2",
        "context_length": 32768,
        "pricing": {"input": 0.0002, "output": 0.0004}
    },
    "gpt-5-nano": {
        "id": "openai/gpt-5-nano",
        "name": "GPT-5 Nano",
        "context_length": 128000,
        "pricing": {"input": 0.00015, "output": 0.0006}
    }
}

# Выбор модели на основе типа задачи
MODEL_FOR_TASK = {
    "intent_analysis": "deepseek/deepseek-chat-v3.1",
    "response_generation": "deepseek/deepseek-chat-v3.1",
    "code_generation": "moonshotai/kimi-k2",
    "creative_writing": "openai/gpt-5-nano",
    "fallback": "openai/gpt-5-nano"
}
