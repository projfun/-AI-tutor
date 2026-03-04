"""
Главный модуль AI-Tutor.
Интегрирует Eel UI с бэкендом (Ollama, School Portal API, Web Search).
"""

import eel
import os
import sys
import json
from pathlib import Path
from datetime import datetime, date
import threading

# Импортируем наши модули
from env_setup import setup_environment, is_ollama_running, start_ollama
from portal import SchoolPortalClient, load_cookies_from_env, save_cookies_to_env
from engine import AITutorEngine

# Инициализируем Eel
eel.init('web')

# Глобальные переменные
ai_engine: AITutorEngine = AITutorEngine()
portal_client: SchoolPortalClient = SchoolPortalClient()
app_config = {
    'token_verified': False,
    'user_profile': None,
    'schedule': {},
}


@eel.expose
def check_environment():
    """JavaScript может вызвать эту функцию для проверки окружения."""
    return {
        'ollama_running': is_ollama_running(),
        'ai_engine_available': ai_engine.is_available(),
        'token_verified': app_config['token_verified'],
    }


@eel.expose
def setup_and_start():
    """Запускает инициализацию окружения."""
    print("[Backend] 🔧 Начинаем инициализацию...")
    
    # Проверяем и запускаем Ollama в отдельном потоке
    def init_thread():
        setup_environment()
        if not is_ollama_running():
            print("[Backend] ⚠️ Ollama не запущена, пытаемся запустить...")
            start_ollama()
    
    init_task = threading.Thread(target=init_thread, daemon=True)
    init_task.start()
    
    return {"status": "initialization_started"}


@eel.expose
def set_school_portal_cookies(cookies: str) -> dict:
    """
    Устанавливает cookies для авторизации в школьном портале.
    JavaScript передает cookies, которые пользователь скопировал из браузера.
    """
    try:
        print(f"[Backend] Проверяем cookies...")
        portal_client.set_cookies(cookies)
        if portal_client.verify_cookies():
            # Сохраняем cookies
            save_cookies_to_env(cookies)
            
            # Получаем профиль пользователя
            profile = portal_client.get_profile()
            app_config['token_verified'] = True
            app_config['user_profile'] = profile
            
            print(f"[Backend] Cookies успешно проверены")
            return {
                'success': True,
                'message': 'Авторизация успешна',
                'profile': profile
            }
        else:
            return {
                'success': False,
                'message': 'Cookies недействительные. Пожалуйста, проверьте их.',
            }
    except Exception as e:
        return {
            'success': False,
            'message': f'Ошибка: {str(e)}',
        }


@eel.expose
def get_today_schedule() -> dict:
    """Получает расписание на сегодня."""
    try:
        if not app_config['token_verified']:
            return {
                'success': False,
                'message': 'Требуется авторизация',
                'schedule': []
            }
        
        schedule = portal_client.get_schedule(date.today())
        
        return {
            'success': True,
            'schedule': schedule['lessons'] if schedule else [],
            'date': str(date.today()),
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Ошибка при загрузке расписания: {str(e)}',
            'schedule': []
        }


@eel.expose
def ask_tutor(question: str, subject: str = None) -> dict:
    """
    Основной метод для взаимодействия с ИИ-тьютором.
    Возвращает ответ потоком.
    """
    try:
        if not ai_engine.is_available():
            return {
                'success': False,
                'message': 'ИИ-движок недоступен. Пожалуйста, проверьте Ollama.',
            }
        
        print(f"[Backend] Вопрос: {question}")
        print(f"[Backend] Предмет: {subject if subject else 'Не указан'}")
        
        # Получаем ответ потоком
        response_text = ""
        for chunk in ai_engine.ask(question, subject=subject, use_search=True):
            response_text += chunk
            print(f"[Backend] Получен чанк: {len(chunk)} символов")
        
        print(f"[Backend] Ответ готов: {len(response_text)} символов")
        
        return {
            'success': True,
            'response': response_text,
        }
    except Exception as e:
        print(f"[Backend] Ошибка в ask_tutor: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'message': f'Ошибка: {str(e)}',
        }


@eel.expose
def get_conversation_history() -> list:
    """Возвращает историю разговора."""
    return ai_engine.get_history()


@eel.expose
def clear_conversation():
    """Очищает историю разговора."""
    ai_engine.clear_history()
    return {'status': 'cleared'}


@eel.expose
def load_token_if_exists() -> dict:
    """Проверяет, есть ли сохраненные cookies в .env."""
    cookies = load_cookies_from_env()
    if cookies:
        # Пытаемся проверить сохраненные cookies
        portal_client.set_cookies(cookies)
        if portal_client.verify_cookies():
            app_config['token_verified'] = True
            profile = portal_client.get_profile()
            app_config['user_profile'] = profile
            return {
                'has_token': True,
                'profile': profile,
            }
    
    return {'has_token': False}


@eel.expose
def get_app_config() -> dict:
    """Возвращает конфигурацию приложения."""
    return {
        'token_verified': app_config['token_verified'],
        'user_profile': app_config['user_profile'],
    }


def main():
    """Главная функция приложения."""
    print("=" * 60)
    print("AI-Tutor: Персональный школьный навигатор")
    print("=" * 60)
    
    # ПРИМЕЧАНИЕ: Мы убрали блокирующий вызов load_token_if_exists() отсюда.
    # Теперь проверка токена происходит асинхронно через JavaScript (window.onload)
    # Это значительно ускоряет запуск приложения.
    
    # Проверяем окружение в отдельном потоке (чтобы UI не зависал)
    def check_env_thread():
        if not is_ollama_running():
            print("\nOllama не найдена. Попытка автоматической установки...")
            setup_environment()
    
    env_thread = threading.Thread(target=check_env_thread, daemon=True)
    env_thread.start()
    
    # Запускаем Eel приложение
    print("\nЗапуск десктопного интерфейса...")
    
    try:
        # Пытаемся запустить в режиме Chrome (как приложение)
        # Если Chrome не установлен, Eel автоматически попробует Edge или системный браузер
        eel.start(
            'index.html',
            mode='chrome', # По умолчанию пытаемся запустить как Chrome App
            host='localhost',
            port=8000,
            size=(1200, 800), # Размер окна
            position=(100, 100),
            block=True
        )
    except Exception as e:
        print(f"[Fatal] Ошибка при запуске интерфейса: {e}")
        # Запасной вариант - запуск в системном браузере
        eel.start('index.html', mode='default')


if __name__ == '__main__':
    main()
