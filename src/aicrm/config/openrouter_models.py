"""
Конфигурации моделей для совместимости с OpenRouter
"""

OPENROUTER_MODELS = {
    "deepseek-coder": {
        "id": "deepseek/deepseek-coder:33b-instruct",
        "name": "DeepSeek Coder 33B",
        "context_length": 16384,
        "pricing": {"input": 0.00035, "output": 0.00035}
    },
    "llama-3-70b": {
        "id": "meta-llama/llama-3-70b-instruct",
        "name": "Llama 3 70B",
        "context_length": 8192,
        "pricing": {"input": 0.00059, "output": 0.00079}
    },
    "gemini-pro": {
        "id": "google/gemini-pro",
        "name": "Google Gemini Pro",
        "context_length": 32768,
        "pricing": {"input": 0.000125, "output": 0.000375}
    }
}

# Выбор модели на основе типа задачи
MODEL_FOR_TASK = {
    "intent_analysis": "deepseek/deepseek-coder:33b-instruct",
    "response_generation": "meta-llama/llama-3-70b-instruct",
    "code_generation": "deepseek/deepseek-coder:33b-instruct",
    "creative_writing": "google/gemini-pro"
}
