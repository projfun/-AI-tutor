import asyncio
import os
import subprocess
import logging
import json
import socket
import sys
from pathlib import Path
from typing import Optional, Dict, List
from playwright.async_api import async_playwright, Browser, Page

logger = logging.getLogger("BrowserConnector")

class BrowserConnector:
    """
    Экспертный модуль 2026 года для управления реальным браузером через CDP.
    Автоматически находит Chrome, запускает его в режиме отладки и подключается для парсинга.
    """
    
    def __init__(self, port: int = 9222, user_data_dir: str = ".chrome-profile"):
        self.port = port
        self.user_data_dir = os.path.abspath(user_data_dir)
        self.playwright = None
        self.browser = None
        self.process = None

    def find_chrome_path(self) -> Optional[str]:
        """Автоматически находит путь к исполняемому файлу Chrome/Edge."""
        if sys.platform == "win32":
            paths = [
                os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
                os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
                os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
                os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
            ]
        elif sys.platform == "darwin":
            paths = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
        else:
            paths = ["/usr/bin/google-chrome", "/usr/bin/chromium"]

        for path in paths:
            if os.path.exists(path):
                return path
        return None

    def is_port_open(self, port: int) -> bool:
        """Проверяет, занят ли порт."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0

    async def launch_browser(self, target_url: str = "https://authedu.mosreg.ru/") -> bool:
        """Запускает реальный Chrome с флагом удаленной отладки и открывает сайт."""
        chrome_path = self.find_chrome_path()
        if not chrome_path:
            logger.error("❌ Chrome не найден в системе.")
            return False

        if self.is_port_open(self.port):
            logger.info(f"🔌 Порт {self.port} уже занят. Браузер запущен.")
            # Если порт открыт, попробуем просто переключиться на вкладку или открыть новую
            return True

        # Команда запуска с флагами 2026 года + URL сайта
        cmd = [
            chrome_path,
            f"--remote-debugging-port={self.port}",
            f"--user-data-dir={self.user_data_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--start-maximized",
            "--disable-infobars",
            target_url # Сразу открываем нужный сайт
        ]

        try:
            self.process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logger.info(f"🚀 Браузер запущен (CDP Port: {self.port})")
            # Даем время на инициализацию
            await asyncio.sleep(3)
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка при запуске браузера: {e}")
            return False

    async def connect_and_grab(self) -> Optional[Dict]:
        """Подключается к запущенному браузеру и собирает данные."""
        self.playwright = await async_playwright().start()
        try:
            # Подключаемся через CDP
            self.browser = await self.playwright.chromium.connect_over_cdp(f"http://localhost:{self.port}")
            context = self.browser.contexts[0]
            
            # Ищем вкладку МосРега или открываем новую
            page = None
            for p in context.pages:
                if "mosreg.ru" in p.url:
                    page = p
                    break
            
            if not page:
                page = await context.new_page()
                await page.goto("https://authedu.mosreg.ru/diary/schedules/day/", wait_until="networkidle")

            # Ждем подтверждения логина (проверяем наличие профиля)
            logger.info("⏳ Ожидание авторизации пользователя...")
            try:
                await page.wait_for_selector(".user-profile, .profile, .avatar, text='Выход'", timeout=5000)
            except:
                logger.warning("⚠️ Пользователь еще не вошел в систему.")
                return {"status": "need_login", "url": page.url}

            # Собираем данные
            data = await self.parse_myschool(page)
            return {"status": "success", "data": data}

        except Exception as e:
            logger.error(f"❌ Ошибка CDP подключения: {e}")
            return None

    async def parse_myschool(self, page: Page) -> Dict:
        """Парсинг данных из активной страницы."""
        # Собираем профиль
        profile = await page.evaluate("""async () => {
            try {
                const resp = await fetch('/api/family/web/v1/profile');
                return await resp.json();
            } catch (e) { return null; }
        }""")

        # Собираем расписание из DOM (максимально надежно)
        lessons = await page.evaluate("""() => {
            const results = [];
            const rows = document.querySelectorAll('.diary-day__lesson, .lesson-item, .ScheduleItem, tr[class*="lesson"]');
            rows.forEach((row, idx) => {
                results.push({
                    number: idx + 1,
                    subject: row.querySelector('.lesson__subject, .subject')?.innerText?.trim() || 'Предмет',
                    time: row.querySelector('.lesson__time, .time')?.innerText?.trim() || '--:--',
                    homework: row.querySelector('.lesson__homework, .homework')?.innerText?.trim() || '',
                    teacher: row.querySelector('.lesson__teacher, .teacher')?.innerText?.trim() || '',
                    room: row.querySelector('.lesson__room, .room')?.innerText?.trim() || ''
                });
            });
            return results;
        }""")

        return {
            "profile_raw": profile,
            "lessons": lessons
        }

    async def close(self):
        """Закрытие ресурсов."""
        if self.browser: await self.browser.close()
        if self.playwright: await self.playwright.stop()
        if self.process: self.process.terminate()
