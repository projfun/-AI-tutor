"""
Конфигурация AI-Tutor.
Все настройки приложения в одном месте.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()

# ============= ОСНОВНЫЕ ПУТИ =============
PROJECT_ROOT = Path(__file__).parent
WEB_DIR = PROJECT_ROOT / "web"
DATA_DIR = PROJECT_ROOT / "data"
TEXTBOOKS_DIR = PROJECT_ROOT / "textbooks"

# Создаем папки если их нет
DATA_DIR.mkdir(exist_ok=True)
TEXTBOOKS_DIR.mkdir(exist_ok=True)


# ============= OLLAMA КОНФИГУРАЦИЯ =============
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "localhost")
OLLAMA_PORT = int(os.getenv("OLLAMA_PORT", 11434))
OLLAMA_API = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"

# Модели (в порядке предпочтения)
MODELS = {
    "primary": "llama3.1:8b-q4_K_M",      # Основная модель (быстрая)
    "quality": "llama3.1:8b-instruct",     # Для более качественных ответов (медленнее)
    "light": "qwen:4b",                    # Легкая модель (для слабых ПК)
}

DEFAULT_MODEL = MODELS["primary"]

# Параметры генерации
GENERATION_CONFIG = {
    "temperature": 0.7,      # Креативность (0-1)
    "top_p": 0.9,            # Nucleus sampling
    "top_k": 40,             # Top-K sampling
    "num_predict": 2048,     # Максимум токенов в ответе
}


# ============= ШКОЛЬНЫЙ ПОРТАЛ =============
SCHOOL_PORTAL = {
    "auth_api": "https://authedu.mosreg.ru",
    "diary_api": "https://diary.mosreg.ru",
    "token_env_var": "SCHOOL_PORTAL_TOKEN",
}


# ============= WEB ИНТЕРФЕЙС =============
WEB_CONFIG = {
    "host": "localhost",
    "port": 8000,
    "mode": "edge",  # Windows: 'edge' или 'chrome'
    "debug": False,
}


# ============= ПОИСК В ИНТЕРНЕТЕ =============
SEARCH_CONFIG = {
    "provider": "duckduckgo",  # duckduckgo (бесплатно) или google (требует API ключ)
    "max_results": 3,
    "timeout": 10,
}


# ============= СИСТЕМА PROMPT (Инструкции для ИИ) =============
SYSTEM_PROMPT = """Ты — ИИ-тьютор для ученика школы. Твоя цель — помочь ему разобраться в сложном материале через объяснение и направление.

ЗОЛОТЫЕ ПРАВИЛА (ОБЯЗАТЕЛЬНО СОБЛЮДАЙ):
1. ❌ НИКОГДА не решай задачи за ученика
2. ✅ ОБЪЯСНЯЙ алгоритм решения, не готовый ответ
3. 💡 Используй ПРИМЕРЫ и АНАЛОГИИ из реальной жизни
4. ❓ Спрашивай ВСТРЕЧНЫЕ ВОПРОСЫ, чтобы проверить понимание
5. 📚 Дай ССЫЛКИ на источники для углубленного изучения

СТРУКТУРА ОТВЕТА:
📝 Краткое объяснение темы (максимум 3 предложения)
🎯 Пошаговый алгоритм или логика решения
💡 Конкретный пример с цифрами
🔗 Ссылки на полезные видео/статьи
❓ Вопрос к ученику: "Ты вроде понял? Попробуй объяснить это своими словами"

СТИЛЬ ОБЩЕНИЯ:
- Дружелюбный и поддерживающий тон
- Используй эмодзи для структурирования текста
- Приветствуй ошибки как "учебные моменты"
- Будь кратким — максимум 2-3 абзаца на первый ответ
- Если ребенок демонстрирует попытку + логику — ПОХВАЛИ его!

ЗАПРЕЩЕНО:
❌ Давать готовые ответы на контрольные/тесты
❌ Помогать списывать домашку
❌ Выходить за рамки школьной программы без предупреждения
❌ Обсуждать политику, религию, личные данные

При множественных вопросах: Разбей на подзадачи и объясни каждую отдельно.
При вопросах вне твоей компетенции: Скажи честно "Это слишком сложно для школы" и переведи к другой теме.
"""


# ============= RAG (БАЗА ЗНАНИЙ).
RAG_CONFIG = {
    "enabled": True,
    "db_path": DATA_DIR / "chroma_db",
    "chunk_size": 500,
    "chunk_overlap": 100,
    "search_results": 3,
}


# ============= КЭШИРОВАНИЕ =============
CACHE_CONFIG = {
    "enabled": True,
    "directory": DATA_DIR / "cache",
    "max_size_mb": 100,  # Максимум размер кэша
    "ttl_hours": 24,     # Время жизни кэша
}

CACHE_CONFIG["directory"].mkdir(exist_ok=True)


# ============= ЛОГИРОВАНИЕ =============
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "[%(levelname)s] %(message)s",
    "file": DATA_DIR / "ai_tutor.log",
}


# ============= ВАЛИДАЦИЯ =============
def validate_config():
    """Проверяет валидность конфигурации."""
    warnings = []
    
    if not WEB_DIR.exists():
        warnings.append(f"⚠️ Web директория не найдена: {WEB_DIR}")
    
    if not (WEB_DIR / "index.html").exists():
        warnings.append(f"⚠️ index.html не найден в {WEB_DIR}")
    
    # Проверяем поддерживаемые провайдеры поиска
    valid_providers = ["duckduckgo", "google"]
    if SEARCH_CONFIG["provider"] not in valid_providers:
        warnings.append(f"⚠️ Неизвестный провайдер поиска: {SEARCH_CONFIG['provider']}")
    
    if warnings:
        print("\n⚠️ Предупреждения конфигурации:")
        for warning in warnings:
            print(f"  {warning}")
    
    return len(warnings) == 0


# ============= ВЫВОД КОНФИГУРАЦИИ =============
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("AI-TUTOR: КОНФИГУРАЦИЯ")
    print("=" * 60)
    
    print(f"\n📁 Пути:")
    print(f"  Проект: {PROJECT_ROOT}")
    print(f"  Web: {WEB_DIR}")
    print(f"  Данные: {DATA_DIR}")
    print(f"  Учебники: {TEXTBOOKS_DIR}")
    
    print(f"\n🤖 Ollama:")
    print(f"  API: {OLLAMA_API}")
    print(f"  Основная модель: {DEFAULT_MODEL}")
    
    print(f"\n🔍 Поиск:")
    print(f"  Провайдер: {SEARCH_CONFIG['provider']}")
    print(f"  Макс результатов: {SEARCH_CONFIG['max_results']}")
    
    print(f"\n💾 RAG:")
    print(f"  Включен: {RAG_CONFIG['enabled']}")
    print(f"  БД: {RAG_CONFIG['db_path']}")
    
    print(f"\n🌐 Веб:")
    print(f"  Адрес: http://{WEB_CONFIG['host']}:{WEB_CONFIG['port']}")
    
    print("\n" + "=" * 60)
    
    valid = validate_config()
    if valid:
        print("✅ Конфигурация валидна\n")
    else:
        print("⚠️ Проверьте предупреждения выше!\n")
