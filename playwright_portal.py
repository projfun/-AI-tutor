"""
Expert Scraper 2026: Моя Школа (Московская область)
Requirements:
pip install playwright playwright-stealth
playwright install chromium
"""

import asyncio
import json
import random
import os
import logging
import time
from datetime import date, datetime
from typing import Dict, List, Optional
from playwright.async_api import async_playwright, BrowserContext, Page, expect
from playwright_stealth import stealth_async

# === CONFIGURATION & LOGGING ===
LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("MosregExpert")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
]

VIEWPORTS = [
    {'width': 1920, 'height': 1080},
    {'width': 1366, 'height': 768},
    {'width': 1440, 'height': 900}
]

class MosregExpertClient:
    def __init__(self, user_data_dir: str = "expert_context"):
        self.user_data_dir = user_data_dir
        self.playwright = None
        self.context = None
        self.proxy = None # Placeholder: {"server": "http://user:pass@host:port"}

    async def _apply_manual_stealth(self, page: Page):
        """Ручные патчи для обхода детекции 2026 года."""
        await page.add_init_script("""
            // Удаление следов автоматизации
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = { runtime: {} };
            
            // Рандомизация аппаратных характеристик
            Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
            Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
            
            // Подмена WebGL (защита от отпечатков видеокарты)
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) return 'Intel Inc.';
                if (parameter === 37446) return 'Intel(R) Iris(R) Xe Graphics';
                return getParameter.apply(this, arguments);
            };
        """)

    async def launch_stealth_browser(self, headless: bool = False):
        """Запуск браузера с максимальной маскировкой."""
        self.playwright = await async_playwright().start()
        
        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-infobars",
            "--ignore-certificate-errors",
            "--disable-dev-shm-usage"
        ]

        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            headless=headless,
            args=launch_args,
            user_agent=random.choice(USER_AGENTS),
            viewport=random.choice(VIEWPORTS),
            proxy=self.proxy,
            ignore_https_errors=True
        )

        # Применяем стелс на все будущие страницы
        await self.context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        logger.info("🚀 Stealth browser context initialized.")

    async def human_delay(self, min_ms=400, max_ms=1500):
        """Имитация человеческой паузы."""
        await asyncio.sleep(random.uniform(min_ms, max_ms) / 1000)

    async def human_move_and_click(self, page: Page, selector: str):
        """Движение мыши и клик как у человека."""
        element = await page.wait_for_selector(selector)
        box = await element.bounding_box()
        if box:
            # Движение по кривой (эмуляция)
            target_x = box['x'] + box['width'] / 2 + random.randint(-5, 5)
            target_y = box['y'] + box['height'] / 2 + random.randint(-5, 5)
            await page.mouse.move(target_x, target_y, steps=random.randint(10, 20))
            await self.human_delay(200, 500)
            await page.click(selector)

    async def human_type(self, page: Page, selector: str, text: str):
        """Печать текста с переменной скоростью."""
        await page.wait_for_selector(selector)
        await page.focus(selector)
        for char in text:
            await page.type(selector, char, delay=random.randint(60, 250))
            if random.random() < 0.05: # Шанс опечатки/заминки
                await asyncio.sleep(random.uniform(0.2, 0.5))

    async def login(self, username, password, retries=3):
        """Процесс входа с обработкой Cloudflare и ошибок."""
        page = self.context.pages[0] if self.context.pages else await self.context.new_page()
        await stealth_async(page)
        await self._apply_manual_stealth(page)

        for attempt in range(retries):
            try:
                logger.info(f"🔗 Attempt {attempt+1}: Navigating to authedu.mosreg.ru...")
                await page.goto("https://authedu.mosreg.ru/", wait_until="networkidle", timeout=60000)
                
                # Проверка Cloudflare
                if await page.query_selector("text='Verify you are human'") or await page.query_selector("#challenge-running"):
                    logger.warning("🛡️ Cloudflare detected! Waiting for challenge...")
                    await asyncio.sleep(15)

                # Ввод данных
                await self.human_type(page, "input[name='login'], input[placeholder*='Логин']", username)
                await self.human_delay()
                await self.human_type(page, "input[name='password'], input[type='password']", password)
                await self.human_delay(800, 2000)
                
                await self.human_move_and_click(page, "button[type='submit'], .login-button")
                
                # Ждем перехода
                await page.wait_for_url("**/diary/**", timeout=45000)
                logger.info("✅ Login successful!")
                return True

            except Exception as e:
                logger.error(f"❌ Login failed (attempt {attempt+1}): {e}")
                await page.screenshot(path=f"fail_login_{attempt}.png")
                if attempt < retries - 1:
                    await asyncio.sleep(5 * (attempt + 1)) # Backoff
        return False

    async def get_schedule(self) -> List[Dict]:
        """Парсинг расширенных данных расписания."""
        page = self.context.pages[0]
        if "/diary/schedules/day" not in page.url:
            await page.goto("https://authedu.mosreg.ru/diary/schedules/day/", wait_until="domcontentloaded")
        
        await self.human_delay(2000, 4000)
        
        try:
            # Экспертный парсинг через JS execution
            lessons = await page.evaluate("""() => {
                const results = [];
                const rows = document.querySelectorAll('.diary-day__lesson, .lesson-item, .ScheduleItem');
                
                rows.forEach((row, idx) => {
                    const subject = row.querySelector('.lesson__subject, .subject')?.innerText?.trim();
                    if (!subject) return;

                    results.push({
                        number: idx + 1,
                        subject: subject,
                        time: row.querySelector('.lesson__time, .time')?.innerText?.trim() || '--:--',
                        room: row.querySelector('.lesson__room, .room')?.innerText?.trim() || '---',
                        teacher: row.querySelector('.lesson__teacher, .teacher')?.innerText?.trim() || 'Не указан',
                        homework: row.querySelector('.lesson__homework, .homework')?.innerText?.trim() || 'Нет задания',
                        materials: Array.from(row.querySelectorAll('a[href*="file"], a[href*="material"]')).map(a => ({
                            title: a.innerText.trim(),
                            url: a.href
                        }))
                    });
                });
                return results;
            }""")
            return lessons
        except Exception as e:
            logger.error(f"❌ Schedule parsing error: {e}")
            return []

    async def connect_to_running_browser(self, port: int = 9222) -> bool:
        """Подключается к уже открытому браузеру Chrome/Edge."""
        self.playwright = await async_playwright().start()
        try:
            # Подключаемся по протоколу CDP
            self.browser = await self.playwright.chromium.connect_over_cdp(f"http://localhost:{port}")
            # Берем первый контекст (обычно он один в запущенном браузере)
            self.context = self.browser.contexts[0]
            logger.info(f"🔌 Успешно подключено к запущенному браузеру на порту {port}")
            return True
        except Exception as e:
            logger.error(f"❌ Не удалось подключиться к браузеру: {e}")
            return False

    async def grab_data_from_open_tab(self) -> Optional[Dict]:
        """Ищет вкладку 'Моя школа' и забирает данные прямо из неё."""
        if not self.context:
            return None
            
        target_page = None
        for page in self.context.pages:
            url = page.url
            if "mosreg.ru" in url:
                target_page = page
                logger.info(f"🎯 Найдена открытая вкладка: {url}")
                break
        
        if not target_page:
            logger.warning("🔍 Вкладка 'Моя школа' не найдена в открытом браузере.")
            return None

        try:
            # 1. Пробуем вытащить профиль через выполнение JS на странице
            profile_raw = await target_page.evaluate("""async () => {
                // Пытаемся найти данные в глобальных переменных страницы
                const state = window.__INITIAL_STATE__ || window.__DATA__;
                if (state) return state;
                
                // Если нет переменных, пробуем сделать запрос от лица страницы
                try {
                    const resp = await fetch('/api/family/web/v1/profile');
                    return await resp.json();
                } catch (e) { return null; }
            }""")
            
            # 2. Собираем уроки прямо из DOM
            lessons = await self.get_schedule_from_page(target_page)
            
            return {
                "profile_raw": profile_raw,
                "lessons": lessons
            }
        except Exception as e:
            logger.error(f"❌ Ошибка при сборе данных из вкладки: {e}")
            return None

    async def get_schedule_from_page(self, page: Page) -> List[Dict]:
        """Парсинг уроков с конкретной страницы."""
        return await page.evaluate("""() => {
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

    async def close(self):
        if self.context: await self.context.close()
        if self.playwright: await self.playwright.stop()

async def main():
    client = MosregExpertClient()
    try:
        # 1. Запуск
        await client.launch_stealth_browser(headless=False)
        
        # 2. Логин (раскомментируйте и введите данные для первого запуска)
        # await client.login("your_login", "your_password")
        # await client.save_session()
        
        # 3. Парсинг
        schedule = await client.get_schedule()
        
        # 4. Красивый вывод
        print("\n" + "🚀" + "—"*15 + " [ MOSREG EXPERT REPORT ] " + "—"*15 + "🚀")
        for l in schedule:
            print(f"【{l['number']}】 📚 {l['subject']} ({l['time']})")
            print(f"   👤 Учитель: {l['teacher']} | 🏫 Каб: {l['room']}")
            print(f"   📝 ДЗ: {l['homework']}")
            if l['materials']:
                print(f"   📎 Материалы: {', '.join([m['title'] for m in l['materials']])}")
            print("—"*60)
            
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
