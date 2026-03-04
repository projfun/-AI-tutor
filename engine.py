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

# Промпты для конкретных предметов
SUBJECT_PROMPTS = {
    "Физика": "Ты — эксперт по физике. Объясняй законы через явления природы и эксперименты. Используй формулы LaTeX.",
    "Математика": "Ты — математик-наставник. Разбивай доказательства на логические шаги. Показывай несколько способов решения (алгебраический, графический).",
    "Химия": "Ты — химик. Объясняй реакции через строение атомов и молекул. Пиши уравнения реакций четко.",
    "История": "Ты — историк. Рассказывай о событиях как о цепочке причин и следствий. Упоминай ключевые даты и личности.",
    "Биология": "Ты — биолог. Объясняй процессы в живой природе через эволюцию и взаимосвязи систем.",
    "Русский язык": "Ты — филолог. Объясняй правила правописания и пунктуации через логику языка и примеры.",
    "Английский язык": "You are a friendly English tutor. Explain grammar rules and vocabulary in a simple way, provide examples in both English and Russian.",
    "default": "Ты — универсальный ИИ-наставник. Помогай ученику разобраться в теме, задавай наводящие вопросы."
}

# Базовый системный промпт (теперь более гибкий)
SYSTEM_PROMPT_BASE = """Ты — опытный ИИ-репетитор (AI-Tutor). Твоя задача — помочь ученику понять суть, а не просто дать ответ.

🧠 ПРИНЦИПЫ:
1. Сначала теория и логика, потом решение.
2. Если есть несколько путей решения — покажи их.
3. Ответ выделяй в самом конце.
4. Задавай проверочный вопрос в конце.
"""

def get_system_prompt(subject: Optional[str] = None) -> str:
    """Формирует динамический системный промпт в зависимости от предмета."""
    subject_specialization = SUBJECT_PROMPTS.get(subject, SUBJECT_PROMPTS["default"])
    return f"{SYSTEM_PROMPT_BASE}\n\nТвоя специализация сейчас: {subject_specialization}"

class AITutorEngine:
    """Основной движок AI-тьютора."""
    
    def __init__(self, model: str = MODEL, ollama_api: str = OLLAMA_API):
        self.model = model
        self.ollama_api = ollama_api
        self.conversation_history: List[Dict[str, str]] = []
        self.search_enabled = True
        self.rag_enabled = False
    
    # ... (остальные методы)
    
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
        
        # Формируем динамический системный промпт
        system_prompt = get_system_prompt(subject)
        
        # Формируем сообщения для чата
        messages = [
            {"role": "system", "content": system_prompt},
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
