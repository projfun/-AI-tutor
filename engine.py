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

# Системный промпт - жесткая инструкция для ИИ
SYSTEM_PROMPT = """Ты — ИИ-тьютор для ученика. Твоя цель — помочь ему разобраться в школьном материале через объяснение и направление, а НЕ решение задачи.

ВАЖНЫЕ ПРАВИЛА:
1. **Никогда не решай задачи за ученика** — вместо этого объясни алгоритм и логику решения
2. **Объясняй через вопросы** — спрашивай, что ученик уже понял
3. **Используй доступный язык** — избегай сложных терминов без объяснения
4. **Приводи примеры** — используй аналогии и конкретные примеры из жизни
5. **Направляй к источникам** — если нужны подробности, дай ссылки на источники
6. **Проверяй понимание** — в конце спроси, понял ли ученик

СТРУКТУРА ОТВЕТА:
- Краткое объяснение теории (2-3 предложения)
- Пошаговый алгоритм/логика решения
- Пример или аналогия
- Ссылки на полезные ресурсы
- Вопрос к ученику для проверки понимания

СТИЛЬ:
- Дружелюбный и поддерживающий тон
- Используй эмодзи для структурирования (🎯 📚 ✅ 💡)
- Будь кратким — максимум 2-3 абзаца на первый ответ
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
                    print(f"[Engine] ✅ Модель найдена!")
                else:
                    print(f"[Engine] ❌ Модель не найдена")
                return found
            else:
                print(f"[Engine] ❌ Ollama не ответила (статус {response.status_code})")
                return False
        except Exception as e:
            print(f"[Engine] ❌ Ошибка при проверке Ollama: {e}")
            return False
    
    def search_web(self, query: str, max_results: int = 3) -> List[Dict[str, str]]:
        """
        Ищет информацию в интернете через DuckDuckGo.
        
        Args:
            query: Search query
            max_results: Максимум результатов
        
        Returns:
            Список результатов с заголовками и описаниями
        """
        try:
            if not self.search_enabled:
                return []
            
            print(f"🔍 Поиск: {query}")
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
        
        Args:
            question: Вопрос ученика
            subject: Школьный предмет (опционально)
            use_search: Использовать ли интернет поиск
            stream: Использовать ли streaming для ответа
        
        Yields:
            Части ответа (если stream=True)
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
            
            print(f"[Engine] 🤖 Отправляю запрос к {self.model} на {url}")
            
            if stream:
                # Streaming режим
                response = requests.post(
                    url,
                    json=payload,
                    stream=True,
                    timeout=REQUEST_TIMEOUT
                )
                print(f"[Engine] Статус: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"[Engine] ❌ Ошибка от Ollama: {response.status_code}")
                    yield f"❌ Ollama вернула ошибку {response.status_code}"
                    return
                
                full_response = ""
                line_count = 0
                try:
                    for line in response.iter_lines(decode_unicode=True):
                        if line:
                            line_count += 1
                            print(f"[Engine] Получена строка {line_count}")
                            try:
                                data = json.loads(line)
                                chunk = data.get('message', {}).get('content', '')
                                if chunk:
                                    full_response += chunk
                                    yield chunk
                                    print(f"[Engine] Выслан чанк: {len(chunk)} символов")
                            except json.JSONDecodeError as je:
                                print(f"[Engine] ⚠️ Ошибка парсинга JSON: {je}")
                                print(f"[Engine] Строка была: {line[:100]}")
                                continue
                except requests.exceptions.ChunkedEncodingError as ce:
                    print(f"[Engine] ⚠️ Ошибка при чтении потока: {ce}")
                    if full_response:
                        print(f"[Engine] Отправлен частичный ответ ({len(full_response)} символов)")
                    else:
                        yield f"❌ Ошибка при получении ответа: {str(ce)}"
                    return
                except requests.exceptions.Timeout:
                    print(f"[Engine] ⏱️ Timeout при чтении потока (после {line_count} строк)")
                    if full_response:
                        print(f"[Engine] Отправлен частичный ответ ({len(full_response)} символов)")
                    else:
                        yield "⏱️ Модель не ответила вовремя"
                    return
                
                # Добавляем в историю
                self.conversation_history.append(
                    {"role": "user", "content": full_question}
                )
                self.conversation_history.append(
                    {"role": "assistant", "content": full_response}
                )
            else:
                # Обычный режим
                response = requests.post(
                    url,
                    json=payload,
                    timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
                data = response.json()
                answer = data.get('message', {}).get('content', '')
                
                # Добавляем в историю
                self.conversation_history.append(
                    {"role": "user", "content": full_question}
                )
                self.conversation_history.append(
                    {"role": "assistant", "content": answer}
                )
                
                return answer
        
        except requests.exceptions.Timeout:
            print(f"[Engine] ⏱️ Превышено время ожидания")
            yield "⏱️ Ошибка: Превышено время ожидания. Пожалуйста, повторите попытку."
        except requests.exceptions.RequestException as e:
            print(f"[Engine] ❌ Ошибка сети: {str(e)}")
            yield f"❌ Ошибка при запросе к ИИ: {str(e)}"
        except json.JSONDecodeError as e:
            print(f"[Engine] ❌ Ошибка парсинга JSON: {str(e)}")
            yield f"❌ Ошибка при обработке ответа: {str(e)}"
        except Exception as e:
            print(f"[Engine] ❌ Неизвестная ошибка: {str(e)}")
            yield f"❌ Неизвестная ошибка: {str(e)}"
    
    def clear_history(self):
        """Очищает историю разговора."""
        self.conversation_history = []
    
    def get_history(self) -> List[Dict[str, str]]:
        """Возвращает историю разговора."""
        return self.conversation_history
    
    async def process_rag_query(self, query: str, documents: List[str]) -> str:
        """
        Обрабатывает запрос с использованием RAG (Retrieval-Augmented Generation).
        Будет реализовано позже с ChromaDB.
        
        Args:
            query: Запрос пользователя
            documents: Список релевантных документов
        
        Returns:
            Ответ с учетом документов
        """
        if not documents or not self.rag_enabled:
            return ""
        
        context = "\n Информация из базы знаний (учебники):\n"
        for i, doc in enumerate(documents[:3], 1):  # Максимум 3 документа
            context += f"\n{i}. {doc[:200]}...\n"
        
        # Обработаем КАК обычный запрос, но с добавленным контекстом
        # В будущем это будет асинхронный вызов
        return context


# Пример использования
if __name__ == "__main__":
    engine = AITutorEngine()
    
    # Проверяем доступность
    if engine.is_available():
        print("✅ Ollama и модель доступны")
        
        # Пример вопроса
        question = "Объясни, почему в цепи из резисторов напряжение делится?"
        print(f"\n📚 Вопрос: {question}\n")
        print("🤖 Ответ:")
        
        for chunk in engine.ask(question, subject="Физика"):
            print(chunk, end="", flush=True)
        print("\n")
    else:
        print("❌ Ollama или модель не доступны")