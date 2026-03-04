"""
Модуль для автоматической проверки и установки Ollama.
Запускается при первом старте приложения.
"""

import os
import subprocess
import sys
import requests
import zipfile
import shutil
from pathlib import Path

OLLAMA_PORT = 11434
OLLAMA_DIR = Path.home() / "AppData" / "Local" / "Programs" / "Ollama"
OLLAMA_EXE = OLLAMA_DIR / "ollama.exe"
MODEL_NAME = "llama3.1:8b-q4_K_M"  # Квантованная версия для производительности


def is_ollama_installed():
    """Проверяет, установлена ли Ollama."""
    return OLLAMA_EXE.exists()


def is_ollama_running():
    """Проверяет, запущена ли Ollama на localhost:11434."""
    try:
        response = requests.get(f"http://localhost:{OLLAMA_PORT}/api/tags", timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def download_ollama():
    """Скачивает Ollama installer с официального сайта."""
    print("📥 Скачивание Ollama...")
    url = "https://ollama.ai/download/OllamaSetup.exe"
    installer_path = Path.home() / "Downloads" / "OllamaSetup.exe"
    
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(installer_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        percent = (downloaded / total_size) * 100
                        print(f"  Прогресс: {percent:.1f}%", end='\r')
        
        print(f"\n✅ Ollama скачана: {installer_path}")
        return installer_path
    except Exception as e:
        print(f"❌ Ошибка при скачивании Ollama: {e}")
        return None


def install_ollama(installer_path):
    """Запускает установщик Ollama."""
    print("⚙️ Запуск установки Ollama...")
    try:
        subprocess.run([str(installer_path)], check=True)
        print("✅ Ollama установлена!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при установке Ollama: {e}")
        return False


def pull_model():
    """Скачивает необходимую модель в Ollama."""
    print(f"🤖 Скачивание модели {MODEL_NAME}...")
    print("   (Это может занять несколько минут...)")
    
    try:
        # Используем API Ollama для скачивания модели
        url = f"http://localhost:{OLLAMA_PORT}/api/pull"
        data = {"name": MODEL_NAME}
        
        response = requests.post(url, json=data, timeout=300, stream=True)
        
        for line in response.iter_lines():
            if line:
                print(f"  {line.decode('utf-8')}")
        
        if response.status_code == 200:
            print(f"✅ Модель {MODEL_NAME} успешно загружена!")
            return True
        else:
            print(f"❌ Ошибка при скачивании модели: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def start_ollama():
    """Запускает Ollama в фоне."""
    print("🚀 Запуск Ollama...")
    try:
        if sys.platform == "win32":
            # Windows: запускаем в фоне
            subprocess.Popen(
                [str(OLLAMA_EXE), "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            subprocess.Popen([str(OLLAMA_EXE), "serve"])
        
        # Ждем, пока Ollama запустится
        import time
        for i in range(30):
            if is_ollama_running():
                print("✅ Ollama запущена!")
                return True
            print(f"  Ожидание запуска... ({i+1}/30)")
            time.sleep(1)
        
        return False
    except Exception as e:
        print(f"❌ Ошибка при запуске Ollama: {e}")
        return False


def setup_environment():
    """Главная функция для настройки окружения."""
    print("=" * 60)
    print("🔧 AI-Tutor: Инициализация окружения")
    print("=" * 60)
    
    # Шаг 1: Проверяем наличие Ollama
    if is_ollama_installed():
        print("✅ Ollama уже установлена")
    else:
        print("❌ Ollama не найдена")
        installer = download_ollama()
        if installer:
            if install_ollama(installer):
                # Удаляем установщик
                os.remove(installer)
            else:
                print("⚠️ Установку нужно провести вручную:")
                print(f"  Скачайте с https://ollama.ai")
                return False
    
    # Шаг 2: Проверяем, запущена ли Ollama
    if is_ollama_running():
        print("✅ Ollama уже запущена")
    else:
        print("❌ Ollama не запущена")
        if not start_ollama():
            print("⚠️ Не удалось запустить Ollama автоматически")
            print("  Пожалуйста, запустите Ollama вручную")
            return False
    
    # Шаг 3: Проверяем наличие модели
    try:
        url = f"http://localhost:{OLLAMA_PORT}/api/tags"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = [m['name'] for m in data.get('models', [])]
            
            if any(MODEL_NAME in m for m in models):
                print(f"✅ Модель {MODEL_NAME} уже загружена")
            else:
                print(f"❌ Модель {MODEL_NAME} не найдена")
                if not pull_model():
                    return False
    except Exception as e:
        print(f"⚠️ Не удалось проверить модели: {e}")
    
    print("=" * 60)
    print("✅ Окружение готово! Можно запускать приложение.")
    print("=" * 60)
    return True


if __name__ == "__main__":
    setup_environment()
