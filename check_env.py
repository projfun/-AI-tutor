#!/usr/bin/env python3
"""
Скрипт для проверки окружения AI-Tutor.
Использование: py -3.13 check_env.py
"""

import sys
import subprocess
from pathlib import Path

print("=" * 60)
print("🔍 AI-Tutor: Проверка окружения")
print("=" * 60)

checks = {
    "✅ OK": 0,
    "⚠️ WARNING": 0,
    "❌ ERROR": 0
}

def check(name, condition, error_msg=""):
    """Выполняет проверку и выводит результат."""
    if condition:
        print(f"✅ {name}")
        checks["✅ OK"] += 1
    else:
        print(f"❌ {name}")
        if error_msg:
            print(f"   └─ {error_msg}")
        checks["❌ ERROR"] += 1

def warn(name, msg=""):
    """Выводит предупреждение."""
    print(f"⚠️ {name}")
    if msg:
        print(f"   └─ {msg}")
    checks["⚠️ WARNING"] += 1

# 1. Python версия
print("\n📋 Python:")
py_version = sys.version_info
check("Python версия", py_version >= (3, 13), 
      f"требуется 3.13+, установлена {py_version.major}.{py_version.minor}")

# 2. Установленные модули
print("\n📦 Основные пакеты:")
required_modules = {
    "eel": "Веб-интерфейс",
    "requests": "HTTP запросы",
    "ollama": "API Ollama",
    "chromadb": "Векторная БД",
    "dotenv": "Переменные окружения",
    "duckduckgo_search": "Web Search",
}

for module, description in required_modules.items():
    try:
        __import__(module)
        check(f"{module} — {description}", True)
    except ImportError:
        check(f"{module} — {description}", False, "не установлен")

# 3. Структура папок
print("\n📁 Папки:")
root = Path(__file__).parent
check("web/ (интерфейс)", (root / "web").exists())
check("data/ (данные)", (root / "data").exists())
check("textbooks/ (учебники)", (root / "textbooks").exists())

# 4. Основные файлы
print("\n📄 Файлы:")
files = {
    "main.py": "Точка входа",
    "engine.py": "AI Engine",
    "portal.py": "API портала",
    "rag.py": "RAG система",
    "config.py": "Конфигурация",
    "web/index.html": "Веб-интерфейс",
}

for filename, description in files.items():
    filepath = root / filename
    check(f"{filename} — {description}", filepath.exists())

# 5. Ollama
print("\n🤖 Ollama:")
try:
    response = subprocess.run(
        ["py", "-3.13", "-c", 
         "import requests; requests.get('http://localhost:11434/api/tags', timeout=2)"],
        capture_output=True,
        timeout=5
    )
    if response.returncode == 0:
        check("Ollama доступна на localhost:11434", True)
    else:
        warn("Ollama не запущена", 
             "запустите её вручную или через run.bat")
except:
    warn("Ollama не запущена",
         "запустите её вручную или через run.bat")

# 6. .env файл
print("\n🔐 Авторизация:")
env_file = root / ".env"
if env_file.exists():
    with open(env_file, 'r') as f:
        content = f.read()
        if "SCHOOL_PORTAL_TOKEN" in content:
            check(".env с токеном портала", True)
        else:
            warn(".env существует но токена нет",
                 "добавьте SCHOOL_PORTAL_TOKEN=<ваш_токен>")
else:
    check(".env файл", False, 
          "создается автоматически при первой авторизации")

# Итоги
print("\n" + "=" * 60)
print("📊 РЕЗУЛЬТАТЫ:")
print("=" * 60)
for status, count in checks.items():
    if count > 0:
        print(f"{status}: {count}")

total_errors = checks["❌ ERROR"]
if total_errors == 0:
    print("\n✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
    print("\nТеперь вы можете запустить:")
    print("  py -3.13 main.py")
    print("  или")
    print("  run.bat (Windows)")
    sys.exit(0)
else:
    print(f"\n❌ НАЙДЕНО {total_errors} ОШИБОК")
    print("Пожалуйста, исправьте ошибки выше")
    sys.exit(1)
