"""
AI Engine для AI-Tutor.
Управляет интеграцией с Ollama и реализует логику наставника.
"""

import requests
from typing import Generator, Optional, Dict, List
import json
from duckduckgo_search import DDGS

# Конфигурация
OLLAMA_API = "http://localhost:11434"
MODEL = "llama3.1:8b"
REQUEST_TIMEOUT = 60  # 60 секунд (было 300)

# Системный промпт - улучшенная инструкция для ИИ
SYSTEM_PROMPT = """Ты — опытный и терпеливый ИИ-репетитор (AI-Tutor). Твоя задача — помочь ученику понять предмет, а не просто дать списать.

🧠 **ТВОИ ПРИНЦИПЫ:**
1. **КОНТЕКСТ ВАЖЕН:** Всегда учитывай предмет, по которому задан вопрос. Если предмет не указан явно, постарайся определить его по контексту вопроса.
2. **НЕ ДАВАЙ ГОТОВЫЙ ОТВЕТ СРАЗУ:** Твоя цель — научить. Сначала объясни тему, покажи путь к решению.
3. **МНОГОВАРИАНТНОСТЬ:** Если задачу можно решить несколькими способами, покажи их (например, аналитически и графически).
4. **ПОШАГОВОСТЬ:** Разбивай сложные объяснения на шаги.
5. **ПРОВЕРКА:** В конце объяснения задай проверочный вопрос, чтобы убедиться, что ученик понял.

📝 **СТРУКТУРА ТВОЕГО ОТВЕТА:**

**Шаг 1: Анализ задачи**
- Определи предмет и тему.
- Кратко переформулируй задачу, чтобы подтвердить понимание.

**Шаг 2: Теория и Подход**
- Объясни формулы или правила, которые здесь применяются.
- Предложи методы решения (Метод 1, Метод 2...).

**Шаг 3: Решение (Скрытое)**
- *Здесь ты пошагово решаешь задачу, объясняя каждый шаг.*
- *Не пиши просто "Ответ: 5". Пиши "Складываем 2 и 3, получаем 5".*

**Шаг 4: Итоговый ответ**
- Выдели его явно (например, **Ответ: ...**), но только ПОСЛЕ объяснения.
- Если ученик просит только ответ, мягко напомни, что важно понять суть, но дай ответ.

🎨 **СТИЛЬ ОБЩЕНИЯ:**
- Используй дружелюбный тон.
- Используй форматирование (жирный шрифт, списки) для читаемости.
- Используй эмодзи умеренно (📚, 💡, ✍️).
"""


class AITutorEngine:
    """Основной движок AI-тьютора."""
    
    def __init__(self, model: str = MODEL, ollama_api: str = OLLAMA_API):
        self.model = model
        self.ollama_api = ollama_api
        self.conversation_history: List[Dict[str, str]] = []
        self.search_enabled = True
        self.rag_enabled = False  # будет включен позже, когда добавим ChromaDB
    
    def is_available(self) -> bool:
        """Проверяет, доступна ли Ollama и модель."""
        try:
            url = f"{self.ollama_api}/api/tags"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = [m['name'] for m in data.get('models', [])]
                print(f"[Engine] Модели в Ollama: {models}")
                print(f"[Engine] Ищу модель: {self.model}")
                found = any(self.model in m for m in models)
                if found:
                    print(f"[Engine] Модель найдена")
                else:
                    print(f"[Engine] Модель не найдена")
                return found
            else:
                print(f"[Engine] Ollama не ответила (статус {response.status_code})")
                return False
        except Exception as e:
            print(f"[Engine] Ошибка при проверке Ollama: {e}")
            return False
    
    def search_web(self, query: str, max_results: int = 3) -> List[Dict[str, str]]:
        """
        Ищет информацию в интернете через DuckDuckGo.
        """
        try:
            if not self.search_enabled:
                return []
            
            print(f"[Engine] Поиск в интернете: {query}")
            results = []
            
            with DDGS() as ddgs:
                search_results = ddgs.text(query, max_results=max_results)
                for result in search_results:
                    results.append({
                        'title': result.get('title', ''),
                        'url': result.get('href', ''),
                        'description': result.get('body', '')
                    })
            
            return results
        except Exception as e:
            print(f"Ошибка при поиске в интернете: {e}")
            return []
    
    def _format_search_context(self, search_results: List[Dict[str, str]]) -> str:
        """Форматирует результаты поиска в контекст для модели."""
        if not search_results:
            return ""
        
        context = "\n Информация из интернета:\n"
        for i, result in enumerate(search_results, 1):
            context += f"\n{i}. {result['title']}\n"
            context += f"   Ссылка: {result['url']}\n"
            context += f"   Описание: {result['description'][:200]}...\n"
        
        return context
    
    def ask(
        self,
        question: str,
        subject: Optional[str] = None,
        use_search: bool = True,
        stream: bool = True
    ) -> Generator[str, None, None]:
        """
        Задает вопрос тьютору с поддержкой поиска.
        """
        # Добавляем контекст предмета в вопрос
        full_question = question
        if subject:
            full_question = f"[Предмет: {subject}]\n{question}"
        
        # Ищем информацию в интернете, если нужно
        search_context = ""
        if use_search:
            search_results = self.search_web(question, max_results=3)
            search_context = self._format_search_context(search_results)
        
        # Формируем полный промпт
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]
        
        # Добавляем историю разговора
        messages.extend(self.conversation_history)
        
        # Добавляем контекст поиска и вопрос
        user_message = f"{full_question}"
        if search_context:
            user_message = f"{search_context}\n\nВопрос ученика: {full_question}"
        
        messages.append({"role": "user", "content": user_message})
        
        # Запрашиваем ответ от Ollama
        try:
            url = f"{self.ollama_api}/api/chat"
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": stream,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                }
            }
            
            print(f"[Engine] Отправляю запрос к {self.model} на {url}")
            
            if stream:
                # Streaming режим
                response = requests.post(
                    url,
                    json=payload,
                    stream=True,
                    timeout=REQUEST_TIMEOUT
                )
                
                if response.status_code != 200:
                    yield f"Ollama вернула ошибку {response.status_code}"
                    return
                
                full_response = ""
                for line in response.iter_lines(decode_unicode=True):
                    if line:
                        try:
                            chunk = json.loads(line)
                            if 'message' in chunk and 'content' in chunk['message']:
                                content = chunk['message']['content']
                                full_response += content
                                yield content
                            if chunk.get('done'):
                                self.conversation_history.append({"role": "user", "content": user_message})
                                self.conversation_history.append({"role": "assistant", "content": full_response})
                        except Exception as e:
                            print(f"[Engine] Ошибка при парсинге чанка: {e}")
            else:
                response = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
                if response.status_code == 200:
                    data = response.json()
                    content = data['message']['content']
                    self.conversation_history.append({"role": "user", "content": user_message})
                    self.conversation_history.append({"role": "assistant", "content": content})
                    yield content
                else:
                    yield f"Ошибка: {response.status_code}"
        except Exception as e:
            print(f"[Engine] Ошибка в ask: {e}")
            yield f"Ошибка подключения к Ollama: {str(e)}"

    def get_history(self) -> List[Dict[str, str]]:
        return self.conversation_history

    def clear_history(self):
        self.conversation_history = []
