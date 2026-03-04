"""
Главный модуль AI-Tutor.
Интегрирует Eel UI с бэкендом (Ollama, School Portal API, Web Search).
"""

import eel
import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime, date
import threading
from typing import Optional

# Импортируем наши модули
from env_setup import setup_environment, is_ollama_running, start_ollama
from portal import SchoolPortalClient, load_cookies_from_env, save_cookies_to_env
from engine import AITutorEngine
from browser_connector import BrowserConnector

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
def open_debug_browser():
    """Запускает браузер Chrome с флагами отладки."""
    connector = BrowserConnector()
    # Запускаем асинхронную функцию в новом потоке или через asyncio
    def run_launch():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(connector.launch_browser())
        
    threading.Thread(target=run_launch, daemon=True).start()
    return {"status": "launching"}

@eel.expose
def set_school_portal_auth(auth_data: dict) -> dict:
    """
    Устанавливает данные авторизации.
    """
    global portal_client
    try:
        portal_client = SchoolPortalClient(auth_data)
        save_auth_to_env(auth_data)
        app_config['token_verified'] = True
        
        # Возвращаем успех сразу, профиль подгрузится позже асинхронно
        # чтобы не вешать кнопку входа
        return {
            'success': True,
            'message': 'Данные приняты'
        }
    except Exception as e:
        return {'success': False, 'message': str(e)}

@eel.expose
def get_user_profile():
    """Асинхронно получает профиль."""
    if not portal_client:
        return None
    return portal_client.get_profile()

def save_auth_to_env(auth_data: dict):
    """Сохраняет данные авторизации в .env."""
    with open('.env', 'w', encoding='utf-8') as f:
        for k, v in auth_data.items():
            f.write(f"PORTAL_{k.upper()}={v}\n")

def load_auth_from_env() -> Optional[dict]:
    """Загружает данные авторизации из .env."""
    if not os.path.exists('.env'):
        return None
    
    auth_data = {}
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            if '=' in line:
                k, v = line.strip().split('=', 1)
                if k.startswith('PORTAL_'):
                    auth_data[k.replace('PORTAL_', '').lower()] = v
    return auth_data if auth_data else None


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
            'success': bool(schedule),
            'schedule': schedule.get('lessons', []) if schedule else [],
            'date': str(date.today()),
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Ошибка при загрузке расписания: {str(e)}',
            'schedule': []
        }


@eel.expose
def parse_manual_schedule(raw_data):
    """Парсит переданный вручную JSON расписания."""
    try:
        schedule = portal_client._parse_schedule(raw_data)
        if schedule and schedule.get('lessons'):
            return {"success": True, "schedule": schedule['lessons']}
        return {"success": False, "message": "В JSON не найдено уроков"}
    except Exception as e:
        return {"success": False, "message": str(e)}


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
    """
    Проверяет наличие сохраненных данных и возвращает их для заполнения полей формы.
    НЕ выполняет сетевых запросов.
    """
    auth_data = load_auth_from_env()
    if auth_data:
        return {
            'has_token': True,
            'auth_data': auth_data
        }
    return {'has_token': False}

@eel.expose
def logout():
    """Удаляет сохраненные данные и сбрасывает сессию."""
    if os.path.exists('.env'):
        os.remove('.env')
    global portal_client
    portal_client = SchoolPortalClient()
    return {'success': True}


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
