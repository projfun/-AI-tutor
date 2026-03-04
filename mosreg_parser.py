import requests
import json
import re
import base64
import os
import subprocess
from typing import Dict, List, Optional
from datetime import date

class MosregParser:
    """
    Актуальный парсер для authedu.mosreg.ru.
    Адаптирован под структуру: data['children'][0]['first_name'], data['children'][0]['id'] и т.д.
    """
    
    def __init__(self, bearer_token: str):
        self.token = bearer_token.replace('Bearer ', '').strip()
        self.session = requests.Session()
        self._setup_session()
        
    def _setup_session(self):
        """Настройка сессии с максимально реалистичными заголовками Chrome 122."""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Authorization': f'Bearer {self.token}',
            'Referer': 'https://authedu.mosreg.ru/',
            'Origin': 'https://authedu.mosreg.ru',
            'X-Requested-With': 'XMLHttpRequest',
            'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Connection': 'keep-alive'
        })

    def _request_with_fallback(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        """Запрос с автоматическим переключением на curl при ошибках 403/SSL."""
        try:
            resp = self.session.request(method, url, timeout=20, verify=False, **kwargs)
            if resp.status_code == 200:
                return resp
            print(f"[Parser] ⚠️ API вернуло {resp.status_code}. Пробую через curl.exe...")
        except Exception as e:
            print(f"[Parser] ⚠️ Requests failed: {e}. Пробую через curl.exe...")
            
        try:
            curl_bin = 'curl.exe' if os.name == 'nt' else 'curl'
            cmd = [
                curl_bin, '-k', '-s', '-L', 
                '-X', method.upper(), 
                '--http2', 
                '--compressed',
                '--connect-timeout', '25',
                '--max-time', '45'
            ]
            
            for k, v in self.session.headers.items():
                cmd.extend(['-H', f'{k}: {v}'])
            
            full_url = url
            if 'params' in kwargs:
                import urllib.parse
                full_url = f"{url}?{urllib.parse.urlencode(kwargs['params'])}"
            
            cmd.append(full_url)
            result = subprocess.run(cmd, capture_output=True, timeout=50)
            
            if result.returncode == 0 and result.stdout:
                mock_resp = requests.Response()
                mock_resp.status_code = 200
                mock_resp._content = result.stdout
                return mock_resp
        except: pass
        return None

    def get_full_data(self) -> Dict:
        """Получает профиль и затем уроки по student_id."""
        print("[Parser] 🔍 Запуск комплексного сбора данных v1...")
        profile_data = self.get_profile_v1()
        
        if "error" in profile_data:
            return profile_data

        try:
            children = profile_data.get('children', [])
            if not children:
                return {"error": "Ученик не найден в блоке children", "code": 404}
            
            # Адаптация под вашу структуру: first_name, last_name, class_name
            student = children[0]
            student_id = student.get('id')
            
            print(f"[Parser] ✅ Ученик: {student.get('last_name')} {student.get('first_name')}, ID: {student_id}")
            
            # Получаем уроки через student_id
            lessons_data = self.parse_lessons(student_id, date.today())
            
            return {
                "success": True,
                "profile": {
                    "name": f"{student.get('first_name')} {student.get('last_name')}",
                    "class": student.get('class_name', '9-Б'),
                    "id": student_id,
                    "avatar": student.get('avatarUrl') or ""
                },
                "schedule": lessons_data
            }
        except Exception as e:
            return {"error": f"Ошибка обработки данных: {e}", "code": 500}

    def get_full_data(self) -> Dict:
        """Комплексный сбор данных: профиль + ID + уроки (v1 family)."""
        print("[Parser] 🔍 Запуск комплексного сбора данных v1...")
        profile_data = self.get_profile_v1()
        
        if "error" in profile_data:
            return profile_data

        try:
            # 1. Извлекаем данные профиля
            profile = profile_data.get('profile', {})
            children = profile_data.get('children', [])
            
            # Приоритет данным из children (там есть класс)
            student = children[0] if children else profile
            
            # Формируем ФИО (Кирилл Перекатнов)
            first_name = student.get('first_name') or profile.get('first_name', 'Ученик')
            last_name = student.get('last_name') or profile.get('last_name', '')
            full_name = f"{first_name} {last_name}".strip()
            
            student_id = student.get('id') or profile.get('id')
            class_name = student.get('class_name', '9-Б')
            
            print(f"[Parser] ✅ Ученик: {full_name}, ID: {student_id}, Класс: {class_name}")
            
            # 2. Получаем уроки
            lessons_data = self.parse_lessons(student_id, date.today())
            
            # 3. Если уроков нет в обычном списке, пробуем собрать из групп (groups/sections)
            if not lessons_data and children:
                print("[Parser] ⚠️ Список уроков пуст. Пробую собрать из учебных групп...")
                groups = children[0].get('groups', [])
                sections = children[0].get('sections', [])
                
                lessons_data = []
                # Объединяем основные предметы и доп. секции
                all_items = groups + sections
                for idx, item in enumerate(all_items):
                    name = item.get('name', 'Предмет')
                    # Очищаем название от лишней инфы (например, "9-Б 9 класс")
                    clean_name = name.split(' 9-')[0].split(',')[0].strip()
                    
                    lessons_data.append({
                        'number': idx + 1,
                        'subject': clean_name,
                        'startTime': '--:--',
                        'endTime': '--:--',
                        'homework': 'Задание в ЛК', # Заглушка, если нет API расписания
                        'id': item.get('id')
                    })

            return {
                "success": True,
                "profile": {
                    "name": full_name,
                    "class": class_name,
                    "id": student_id,
                    "avatar": student.get('avatar_url') or student.get('avatarUrl') or ""
                },
                "schedule": lessons_data
            }
        except Exception as e:
            print(f"[Parser] ❌ Ошибка обработки: {e}")
            return {"error": f"Ошибка обработки: {e}", "code": 500}

    def get_full_data_from_json(self, profile_data: Dict) -> Dict:
        """Обрабатывает уже полученный JSON (например, из перехвата Playwright)."""
        try:
            profile = profile_data.get('profile', {})
            children = profile_data.get('children', [])
            student = children[0] if children else profile
            
            first_name = student.get('first_name') or profile.get('first_name', 'Ученик')
            last_name = student.get('last_name') or profile.get('last_name', '')
            full_name = f"{first_name} {last_name}".strip()
            
            student_id = student.get('id') or profile.get('id')
            class_name = student.get('class_name', '9-Б')
            
            # Пытаемся получить уроки из JSON (если они там были вложены)
            # Или вызываем parse_lessons если есть student_id
            lessons_data = []
            if student_id and self.token != "dummy":
                lessons_data = self.parse_lessons(student_id, date.today())
            
            # Если уроков нет, собираем из групп
            if not lessons_data and children:
                groups = children[0].get('groups', [])
                sections = children[0].get('sections', [])
                all_items = groups + sections
                for idx, item in enumerate(all_items):
                    name = item.get('name', 'Предмет')
                    clean_name = name.split(' 9-')[0].split(',')[0].strip()
                    lessons_data.append({
                        'number': idx + 1,
                        'subject': clean_name,
                        'startTime': '--:--',
                        'endTime': '--:--',
                        'homework': 'Задание в ЛК',
                        'id': item.get('id')
                    })

            return {
                "success": True,
                "profile": {
                    "name": full_name,
                    "class": class_name,
                    "id": student_id,
                    "avatar": student.get('avatar_url') or student.get('avatarUrl') or ""
                },
                "schedule": lessons_data
            }
        except Exception as e:
            return {"error": str(e), "success": False}

    def get_profile_v1(self) -> Dict:
        """Запрос к актуальному эндпоинту профиля family v1."""
        url = "https://authedu.mosreg.ru/api/family/web/v1/profile"
        resp = self._request_with_fallback('GET', url)
        
        if not resp:
            return {"error": "Не удалось получить ответ от сервера (403/SSL/Timeout)", "code": 403}
        
        if resp.status_code == 401:
            return {"error": "Токен устарел (401 Unauthorized)", "code": 401}
        
        try:
            return resp.json()
        except:
            return {"error": "Ошибка парсинга JSON ответа", "code": 500}

    def parse_lessons(self, student_id: int, target_date: date) -> Optional[List]:
        """Запрос уроков через student_id на authedu.mosreg.ru."""
        date_str = target_date.strftime('%Y-%m-%d')
        url = f"https://authedu.mosreg.ru/api/family/web/v1/children/{student_id}/lessons"
        params = {'from': date_str, 'to': date_str}
        
        resp = self._request_with_fallback('GET', url, params=params)
        if resp and resp.status_code == 200:
            try:
                data = resp.json()
                # В v1 уроки могут быть в корне или в data['lessons']
                if isinstance(data, dict):
                    return data.get('lessons', []) or data.get('items', [])
                return data if isinstance(data, list) else []
            except: pass
        return []
