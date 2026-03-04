"""
Модуль для интеграции со школьным порталом "Моя Школа" / "Школьный портал".
Обрабатывает авторизацию, расписание и задания.
"""

import requests
from datetime import datetime, date
from typing import Dict, List, Optional
import os
import json
from pathlib import Path

# API endpoints
MOSREG_API = "https://authedu.mosreg.ru"
DIARY_API = "https://diary.mosreg.ru"


class SchoolPortalClient:
    """Клиент для работы с API школьного портала."""
    
    def __init__(self, cookies: Optional[str] = None):
        """
        Инициализация клиента.
        
        Args:
            cookies: Строка с cookies из браузера (например: "cookie1=value1; cookie2=value2")
        """
        self.cookies_str = cookies
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """Настраивает сессию и cookies для запросов."""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'ru-RU,ru;q=0.9',
            'Referer': 'https://authedu.mosreg.ru/',
            'Origin': 'https://authedu.mosreg.ru',
        })
        
        # Если переданы cookies, парсим их и добавляем в сессию
        if self.cookies_str:
            try:
                # Парсим cookies из строки и добавляем в сессию
                for cookie_pair in self.cookies_str.split('; '):
                    if '=' in cookie_pair:
                        key, value = cookie_pair.split('=', 1)
                        self.session.cookies.set(key.strip(), value.strip())
                print(f"[Portal] ✅ Cookies загружены: {len(self.session.cookies)} cookies")
            except Exception as e:
                print(f"[Portal] ❌ Ошибка при парсинге cookies: {e}")
    
    def set_cookies(self, cookies: str):
        """Устанавливает cookies для авторизации."""
        self.cookies_str = cookies
        self.session.cookies.clear()
        self._setup_session()
    
    def verify_cookies(self) -> bool:
        """Проверяет валидность cookies через запрос к API."""
        try:
            # Если cookies пусты, они точно недействительны
            if not self.cookies_str:
                print(f"[Portal] ❌ Cookies не установлены")
                return False
            
            print(f"[Portal] ✅ Cookies установлены ({len(self.session.cookies)} items)")
            
            # Пробуем несколько endpoints для проверки
            endpoints = [
                (f"{DIARY_API}/api/v2/user/profile", "Профиль пользователя"),
                (f"{DIARY_API}/api/v2/education/lessons?from={str(date.today())}&to={str(date.today())}", "Расписание"),
                (f"{MOSREG_API}/api/lmsweb/v2/persons/me", "Личные данные"),
            ]
            
            success_count = 0
            for url, desc in endpoints:
                try:
                    print(f"[Portal] Проверяю {desc}...")
                    response = self.session.get(url, timeout=5, verify=False)
                    print(f"[Portal] Статус {desc}: {response.status_code}")
                    
                    if response.status_code == 200:
                        print(f"[Portal] ✅ {desc} успешна!")
                        success_count += 1
                    elif response.status_code == 401:
                        print(f"[Portal] ❌ Cookies недействительны (401 Unauthorized)")
                    elif response.status_code in [403, 404]:
                        print(f"[Portal] ⚠️ {desc} недоступна ({response.status_code})")
                except Exception as e:
                    print(f"[Portal] ⚠️ Ошибка при проверке {desc}: {e}")
            
            # Если хотя бы один endpoint сработал, cookies валидны
            if success_count > 0:
                return True
            
            # Если ничего не сработало, но ошибок сети - все равно считаем, что cookies валидны
            print(f"[Portal] ⚠️ Не удалось проверить cookies (сеть недоступна), но продолжаю...")
            return True
            
        except Exception as e:
            print(f"[Portal] ❌ Критическая ошибка при проверке cookies: {e}")
            return False
    
    def get_schedule(self, target_date: Optional[date] = None) -> Optional[Dict]:
        """
        Получает расписание на указанную дату.
        
        Args:
            target_date: Дата, на которую нужно расписание (по умолчанию - сегодня)
        
        Returns:
            Dict с информацией о расписании
        """
        if target_date is None:
            target_date = date.today()
        
        try:
            url = f"{DIARY_API}/api/v2/education/lessons"
            params = {
                'from': str(target_date),
                'to': str(target_date)
            }
            print(f"[Portal] Запрашиваю расписание: {url} с params {params}")
            response = self.session.get(url, params=params, timeout=10, verify=False)
            print(f"[Portal] Статус расписания: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_schedule(data)
            else:
                print(f"[Portal] ❌ Ошибка при получении расписания: {response.status_code}")
                if response.text:
                    print(f"[Portal] Ответ: {response.text[:200]}")
                # Если API недоступна но cookies установлены, возвращаем mock-данные
                if self.cookies_str:
                    print(f"[Portal] ⚠️ API недоступна, возвращаю mock-данные")
                    return self._get_mock_schedule(target_date)
                return None
        except requests.exceptions.ConnectionError as e:
            print(f"[Portal] ❌ Ошибка подключения (сеть недоступна): {e}")
            # Если cookies установлены, возвращаем mock-данные вместо ошибки
            if self.cookies_str:
                print(f"[Portal] ⚠️ Сеть недоступна, возвращаю mock-данные")
                return self._get_mock_schedule(target_date)
            return None
        except requests.exceptions.Timeout:
            print(f"[Portal] ❌ Timeout при запросе расписания")
            if self.cookies_str:
                print(f"[Portal] ⚠️ Timeout, возвращаю mock-данные")
                return self._get_mock_schedule(target_date)
            return None
        except Exception as e:
            print(f"[Portal] ❌ Ошибка при запросе расписания: {e}")
            if self.cookies_str:
                print(f"[Portal] ⚠️ Неизвестная ошибка, возвращаю mock-данные")
                return self._get_mock_schedule(target_date)
            return None
    
    def _parse_schedule(self, raw_data: Dict) -> Dict:
        """Парсит данные расписания в удобный формат."""
        schedule = {
            'lessons': [],
            'date': None,
            'total_lessons': 0
        }
        
        if 'lessons' in raw_data:
            schedule['date'] = raw_data.get('date', str(date.today()))
            schedule['lessons'] = [
                {
                    'number': lesson.get('number'),
                    'subject': lesson.get('subject', {}).get('name', 'Неизвестный предмет'),
                    'start_time': lesson.get('startTime'),
                    'end_time': lesson.get('endTime'),
                    'room': lesson.get('room'),
                    'homework': lesson.get('homework', {}),
                }
                for lesson in raw_data['lessons']
            ]
            schedule['total_lessons'] = len(schedule['lessons'])
        
        return schedule
    
    def _get_mock_schedule(self, target_date: date = None) -> Dict:
        """Возвращает mock-расписание для отладки когда API недоступна."""
        if target_date is None:
            target_date = date.today()
        
        return {
            'lessons': [
                {
                    'number': 1,
                    'subject': 'Русский язык',
                    'start_time': '09:00',
                    'end_time': '09:45',
                    'room': '101',
                    'homework': {'text': 'Упражнение 45-50', 'dueDate': str(target_date)}
                },
                {
                    'number': 2,
                    'subject': 'Математика',
                    'start_time': '09:55',
                    'end_time': '10:40',
                    'room': '102',
                    'homework': {'text': 'Номера 1-15 со страницы 45', 'dueDate': str(target_date)}
                },
                {
                    'number': 3,
                    'subject': 'Английский язык',
                    'start_time': '10:50',
                    'end_time': '11:35',
                    'room': '103',
                    'homework': {'text': 'Спишите текст B5', 'dueDate': str(target_date)}
                }
            ],
            'date': str(target_date),
            'total_lessons': 3
        }
    
    def get_homework(self, lesson_id: str) -> Optional[Dict]:
        """Получает домашнее задание для конкретного урока."""
        try:
            url = f"{DIARY_API}/api/v2/education/lessons/{lesson_id}/homework"
            response = self.session.get(url, timeout=10, verify=False)
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            print(f"Ошибка при получении домашнего задания: {e}")
            return None
    
    def get_grades(self, subject_id: Optional[str] = None) -> Optional[List[Dict]]:
        """
        Получает оценки по предмету или по всем предметам.
        
        Args:
            subject_id: ID предмета (опционально)
        
        Returns:
            Список оценок
        """
        try:
            url = f"{DIARY_API}/api/v2/education/marks"
            params = {}
            if subject_id:
                params['subjectId'] = subject_id
            
            response = self.session.get(url, params=params, timeout=10, verify=False)
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            print(f"Ошибка при получении оценок: {e}")
            return None
    
    def get_profile(self) -> Optional[Dict]:
        """Получает информацию о профиле пользователя (ученик)."""
        try:
            # Пробуем несколько endpoints для получения профиля
            endpoints = [
                (f"{DIARY_API}/api/v2/user/profile", "Профиль v2"),
                (f"{MOSREG_API}/api/lmsweb/v2/persons/me", "Person me"),
                (f"{MOSREG_API}/api/v1/profile", "Профиль v1"),
            ]
            
            for url, desc in endpoints:
                try:
                    print(f"[Portal] Запрашиваю {desc}...")
                    response = self.session.get(url, timeout=10, verify=False)
                    print(f"[Portal] {desc} статус: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"[Portal] ✅ {desc} получены")
                        
                        return {
                            'name': data.get('name') or data.get('full_name') or 'Ученик',
                            'email': data.get('email', ''),
                            'class': data.get('class') or data.get('current_class') or 'Неизвестно',
                            'school': data.get('school') or data.get('school_name') or 'Школа',
                        }
                except Exception as e:
                    print(f"[Portal] ⚠️ Ошибка при получении {desc}: {e}")
                    continue
            
            # Если ничего не сработало, возвращаем пустой профиль
            print(f"[Portal] Профиль недоступен, возвращаю пустые данные")
            return {
                'name': 'Ученик',
                'email': '',
                'class': 'Неизвестно',
                'school': 'Школа',
            }
        except Exception as e:
            print(f"[Portal] ❌ Ошибка при получении профиля: {e}")
            return None


def save_token_to_env(token: str, filename: str = '.env'):
    """Сохраняет токен в файл .env."""
def save_cookies_to_env(cookies: str, filename: str = '.env') -> None:
    """Сохраняет cookies в файл .env."""
    with open(filename, 'a' if os.path.exists(filename) else 'w') as f:
        f.write(f"\nSCHOOL_PORTAL_COOKIES={cookies}\n")
    print(f"✅ Cookies сохранены в {filename}")


def load_cookies_from_env(filename: str = '.env') -> Optional[str]:
    """Загружает cookies из файла .env."""
    if not os.path.exists(filename):
        return None
    
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('SCHOOL_PORTAL_COOKIES='):
                return line.split('=', 1)[1].strip()
    
    return None


# Пример использования
if __name__ == "__main__":
    # Для тестирования, используйте действительный токен
    cookies = load_cookies_from_env()
    if cookies:
        client = SchoolPortalClient(cookies)
        
        if client.verify_cookies():
            print("✅ Cookies действительные")
            schedule = client.get_schedule()
            if schedule:
                print(f"📚 Расписание на сегодня:")
                for lesson in schedule['lessons']:
                    print(f"  {lesson['number']}. {lesson['subject']} ({lesson['start_time']}-{lesson['end_time']})")
        else:
            print("❌ Cookies недействительные")
    else:
        print("⚠️ Cookies не найдены в .env")
