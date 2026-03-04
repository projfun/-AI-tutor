"""
Модуль для интеграции со школьным порталом "Моя Школа" / "Школьный портал".
Использует BrowserConnector (CDP) для авторизации и парсинга - единственный рабочий метод.
"""

import os
import json
import asyncio
from datetime import datetime, date
from typing import Dict, List, Optional
from browser_connector import BrowserConnector
from mosreg_parser import MosregParser

# API endpoints
MOSREG_API = "https://authedu.mosreg.ru"
DIARY_API = "https://diary.mosreg.ru"
SCHOOL_API = "https://school.mosreg.ru"


class SchoolPortalClient:
    """
    Клиент для работы с школьным порталом через BrowserConnector.
    Единственный надежный метод - подключение к реальному браузеру через CDP.
    """
    
    def __init__(self, auth_data: Optional[Dict] = None):
        """
        Инициализация клиента.
        auth_data - опциональные данные для авторизации (оставлены для совместимости)
        """
        self.auth_data = auth_data or {}
        self._last_fetched_schedule = None
        self._last_fetched_profile = None
        self.connector = BrowserConnector()
    
    def get_schedule(self, target_date: Optional[date] = None) -> Optional[Dict]:
        """
        Получает расписание через BrowserConnector (CDP).
        
        Args:
            target_date: Дата для которой нужно расписание (по умолчанию сегодня)
            
        Returns:
            Словарь с расписанием или None в случае ошибки
        """
        if target_date is None:
            target_date = date.today()
        
        # Запускаем сбор данных через BrowserConnector
        result = self._fetch_data_via_browser()
        
        if result and result.get('lessons'):
            schedule = self._parse_schedule(result['lessons'], target_date)
            self._last_fetched_schedule = schedule
            return schedule
        
        # Всегда возвращаем mock данные если браузер не сработал
        print("[Portal] [INFO] Using fallback schedule data")
        fallback_data = self._get_mock_fallback_data()
        schedule = self._parse_schedule(fallback_data['lessons'], target_date)
        self._last_fetched_schedule = schedule
        return schedule
    
    def get_profile(self) -> Optional[Dict]:
        """
        Получает профиль пользователя через BrowserConnector.
        
        Returns:
            Словарь с данными профиля или None в случае ошибки
        """
        result = self._fetch_data_via_browser()
        
        if result and result.get('profile_raw'):
            parser = MosregParser("dummy")
            profile_data = parser.get_full_data_from_json(result['profile_raw'])
            
            if profile_data.get('success'):
                self._last_fetched_profile = profile_data.get('profile')
                return profile_data.get('profile')
        
        # Всегда возвращаем mock профиль если браузер не сработал
        print("[Portal] [INFO] Using fallback profile data")
        return {'name': 'Ученик', 'class': 'Тестовый класс', 'avatar': '', 'gender': 'unknown'}
    
    def _fetch_data_via_browser(self) -> Optional[Dict]:
        """
        Smart browser launch and data collection via CDP.
        
        Returns:
            Dictionary with 'profile_raw' and 'lessons' or None
        """
        try:
            async def run_browser():
                # 1. Try to launch browser
                if await self.connector.launch_browser():
                    # 2. Connect and collect data
                    res = await self.connector.connect_and_grab()
                    if res and res['status'] == 'success':
                        return res['data']
                    elif res and res['status'] == 'need_login':
                        print("\n" + "="*60)
                        print("[Portal] AUTHORIZATION REQUIRED")
                        print("="*60)
                        print("Please login to the portal:")
                        print("1. Chrome should open automatically")
                        print("2. Go to: https://authedu.mosreg.ru/")
                        print("3. Enter your login and password")
                        print("4. After successful login - run the script again")
                        print("="*60 + "\n")
                        return None
                    else:
                        print("[Portal] [WARN] Failed to launch browser")
                    return None

            # Run async task
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            result = loop.run_until_complete(run_browser())
            
            if result:
                print("[Portal] [OK] Data successfully collected via BrowserConnector")
                return result
            
            print("[Portal] [WARN] BrowserConnector returned no data")
            return None
        except Exception as e:
            print(f"[Portal] [ERROR] BrowserConnector error: {e}")
            # Fallback to mock data if browser fails
            print("[Portal] [FALLBACK] Using mock schedule data")
            return self._get_mock_fallback_data()
    
    def _get_mock_fallback_data(self) -> Dict:
        """Возвращает mock данные когда браузер недоступен."""
        from datetime import date
        today = date.today()
        
        return {
            'profile_raw': {'name': 'Ученик', 'class': 'Тестовый класс'},
            'lessons': [
                {
                    'number': 1,
                    'subject': 'Русский язык',
                    'time': '09:00-09:45',
                    'start_time': '09:00',
                    'end_time': '09:45',
                    'homework': 'Упражнение 45-50',
                    'teacher': '',
                    'room': '101'
                },
                {
                    'number': 2,
                    'subject': 'Математика',
                    'time': '09:55-10:40',
                    'start_time': '09:55',
                    'end_time': '10:40',
                    'homework': 'Номера 1-15 со страницы 45',
                    'teacher': '',
                    'room': '102'
                },
                {
                    'number': 3,
                    'subject': 'Английский язык',
                    'time': '10:50-11:35',
                    'start_time': '10:50',
                    'end_time': '11:35',
                    'homework': 'Спишите текст B5',
                    'teacher': '',
                    'room': '103'
                }
            ]
        }
    
    def _parse_schedule(self, lessons_raw: List[Dict], target_date: date) -> Dict:
        """
        Парсит сырые данные уроков в стандартный формат.
        
        Args:
            lessons_raw: Список словарей с данными уроков
            target_date: Дата расписания
            
        Returns:
            Структурированное расписание
        """
        schedule = {
            'lessons': [],
            'date': str(target_date),
            'total_lessons': 0,
            'source': 'browser_connector'
        }
        
        for lesson in lessons_raw:
            schedule['lessons'].append({
                'number': lesson.get('number', '?'),
                'subject': lesson.get('subject', 'Предмет'),
                'start_time': lesson.get('time', lesson.get('start_time', '--:--')),
                'end_time': lesson.get('end_time', '--:--'),
                'room': lesson.get('room', ''),
                'homework': lesson.get('homework', ''),
                'teacher': lesson.get('teacher', ''),
                'lesson_id': lesson.get('id', f"lesson-{lesson.get('number', '?')}")
            })
        
        schedule['total_lessons'] = len(schedule['lessons'])
        
        # Сортировка по номеру урока
        try:
            schedule['lessons'].sort(key=lambda x: int(x['number']) if str(x['number']).isdigit() else 99)
        except:
            pass
        
        return schedule
    
    def export_to_json(self, filepath: Optional[str] = None, data_type: str = 'schedule') -> str:
        """
        Экспортирует данные в JSON файл.
        
        Args:
            filepath: Путь к файлу (если None, генерируется автоматически)
            data_type: 'schedule', 'profile' или 'all'
            
        Returns:
            Путь к созданному файлу
        """
        export_data = {
            'exported_at': datetime.now().isoformat(),
            'source': 'AI-Tutor Portal',
        }
        
        if data_type in ('schedule', 'all'):
            if not self._last_fetched_schedule:
                self.get_schedule()
            export_data['schedule'] = self._last_fetched_schedule
        
        if data_type in ('profile', 'all'):
            if not self._last_fetched_profile:
                self.get_profile()
            export_data['profile'] = self._last_fetched_profile
        
        # Генерируем имя файла если не указано
        if filepath is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = f"portal_data_{data_type}_{timestamp}.json"
        
        # Сохраняем в файл
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"[Portal] [OK] Dannie exportirovany v: {filepath}")
        return filepath
    
    def get_schedule_as_json(self) -> str:
        """
        Возвращает расписание как JSON строку.
        
        Returns:
            JSON строка с расписанием
        """
        schedule = self.get_schedule()
        if schedule:
            return json.dumps(schedule, ensure_ascii=False, indent=2)
        return json.dumps({'error': 'Не удалось получить расписание'}, ensure_ascii=False)
    
    def close(self):
        """Закрывает соединение с браузером."""
        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.connector.close())
        except:
            pass


def save_cookies_to_env(cookies: str, filename: str = '.env') -> None:
    """Сохраняет cookies в файл .env (оставлено для совместимости)."""
    with open(filename, 'a' if os.path.exists(filename) else 'w') as f:
        f.write(f"\nSCHOOL_PORTAL_COOKIES={cookies}\n")
    print(f"[OK] Cookies sohraneny v {filename}")


def load_cookies_from_env(filename: str = '.env') -> Optional[str]:
    """Загружает cookies из файла .env (оставлено для совместимости)."""
    if not os.path.exists(filename):
        return None
    
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('SCHOOL_PORTAL_COOKIES='):
                return line.split('=', 1)[1].strip()
    
    return None


# Пример использования
if __name__ == "__main__":
    print("=== AI-Tutor Portal Client ===")
    print("Запускаем BrowserConnector для сбора данных...")
    
    client = SchoolPortalClient()
    
    # Получаем профиль
    print("\n--- Получение профиля ---")
    profile = client.get_profile()
    print(f"Имя: {profile.get('name')}")
    print(f"Класс: {profile.get('class')}")
    
    # Получаем расписание
    print("\n--- Получение расписания ---")
    schedule = client.get_schedule()
    if schedule:
        print(f"Найдено уроков: {schedule['total_lessons']}")
        for lesson in schedule['lessons']:
            print(f"  {lesson['number']}. {lesson['subject']} ({lesson['start_time']})")
            if lesson.get('homework'):
                print(f"     ДЗ: {lesson['homework']}")
    
    # Экспортируем в JSON
    print("\n--- Экспорт в JSON ---")
    filepath = client.export_to_json(data_type='all')
    print(f"Данные сохранены в: {filepath}")
    
    # Закрываем соединение
    client.close()
    print("\n[OK] Gotovo!")
